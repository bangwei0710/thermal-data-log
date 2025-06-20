
import streamlit as st
import pandas as pd
from io import BytesIO

try:
    import xlsxwriter
except ImportError:
    st.error("請先安裝 xlsxwriter 套件：pip install xlsxwriter")
    st.stop()

st.set_page_config(page_title="Thermal Log 整合工具 v5", layout="wide")
st.title("📊 Thermal Log ➜ 先下載 A Excel，再即時顯示 Summary")

uploaded_files = st.file_uploader("📂 上傳多個 CSV 或 Excel 檔案", type=["csv", "xls", "xlsx"], accept_multiple_files=True)

start_row = st.number_input("📍 輸入統計起始列", min_value=0, value=0)
end_row = st.number_input("📍 輸入統計結束列（不含）", min_value=1, value=1000)

sheet_data = {"HW64": [], "PTAT": [], "GPUmon": []}
summary_columns = [
    'Total System Power [W]', 'CPU Package Power [W]', ' 1:TGP (W)', 'Charge Rate [W]',
    'IA Cores Power [W]', 'GT Cores Power [W]', ' 1:NVVDD Power (W)', ' 1:FBVDD Power (W)',
    'CPU Package [蚓]', ' 1:Temperature GPU (C)', ' 1:Temperature Memory (C)', 'Temp0 [蚓]',
    'SEN1-temp(Degree C)', 'SEN2-temp(Degree C)', 'SEN3-temp(Degree C)', 'SEN4-temp(Degree C)',
    'SEN5-temp(Degree C)', 'SEN6-temp(Degree C)', 'SEN7-temp(Degree C)', 'SEN8-temp(Degree C)',
    'SEN9-temp(Degree C)', 'J', 'C', 'D',
    'HP1-1', 'HP1-2', 'HP1-3', 'HP1-4', 'HP2-1', 'HP2-2', 'HP2-3', 'HP2-4',
    'CPUfin', 'GPUfin'
]

def normalize(col):
    return col.strip().lower().replace(" ", "").replace(":", "").replace("（", "(").replace("）", ")")

def classify_file(name):
    lower = name.lower()
    if "gpu" in lower:
        return "GPUmon"
    elif "ptat" in lower:
        return "PTAT"
    elif "hw" in lower:
        return "HW64"
    else:
        return None

if uploaded_files:
    merged_all = []
    for f in uploaded_files:
        file_type = classify_file(f.name)
        if not file_type:
            st.warning(f"⚠️ 檔案 `{f.name}` 無法分類，已略過")
            continue
        try:
            if f.name.endswith(".csv"):
                df = pd.read_csv(f, encoding="cp950", engine="python", on_bad_lines="skip")
            else:
                df = pd.read_excel(f)
            df.columns = df.columns.str.strip()
            if file_type == "GPUmon":
                df = df.iloc[35:].reset_index(drop=True)
            else:
                df = df.reset_index(drop=True).iloc[5:]
            sheet_data[file_type].append(df)
            merged_all.append(df)
            st.success(f"✅ 已載入 `{f.name}` → 分類為 {file_type}")
        except Exception as e:
            st.error(f"❌ 錯誤：{f.name} → {e}")

    # 匯出 A Excel（分類原始 sheet）
    st.markdown("### 📥 1️⃣ 下載 A Excel（整合多個分類 sheet）")
    a_excel = BytesIO()
    with pd.ExcelWriter(a_excel, engine="xlsxwriter") as writer:
        for sheet, dfs in sheet_data.items():
            if dfs:
                merged = pd.concat(dfs, ignore_index=True)
                merged.to_excel(writer, sheet_name=sheet, index=False)
    a_excel.seek(0)
    st.download_button(
        label="⬇️ 下載 A Excel：多 sheet 原始資料",
        data=a_excel,
        file_name="A_merged_raw_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 直接在網頁即時顯示 Summary 統計表
    st.markdown("### 📊 2️⃣ 即時 Summary 統計（指定範圍）")
    if merged_all:
        stat_df = pd.concat(merged_all, ignore_index=True).iloc[start_row:end_row]
        stat_df.columns = stat_df.columns.str.strip()

        results = []
        for col in summary_columns:
            match = [c for c in stat_df.columns if normalize(c) == normalize(col)]
            if match:
                series = pd.to_numeric(stat_df[match[0]], errors='coerce').dropna()
                value = f"{series.mean():.2f}" if not series.empty else "-"
            else:
                value = "-"
            results.append({"參數名稱": col, "平均值": value})
        summary_df = pd.DataFrame(results)
        st.dataframe(summary_df, use_container_width=True)

else:
    st.info("請上傳至少一個檔案以開始。")
