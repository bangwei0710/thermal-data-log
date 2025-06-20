
import streamlit as st
import pandas as pd
from io import BytesIO

try:
    import xlsxwriter
except ImportError:
    st.error("請先安裝 xlsxwriter 套件：pip install xlsxwriter")
    st.stop()

st.set_page_config(page_title="Thermal Log 整合工具 v3", layout="wide")
st.title("📊 Thermal Log 多檔整合 ➜ 多 Sheet + 統整頁（平均）")

uploaded_files = st.file_uploader("📂 上傳多個 CSV 或 Excel 檔案", type=["csv", "xls", "xlsx"], accept_multiple_files=True)

start_row = st.number_input("📍 輸入統計起始列", min_value=0, value=0)
end_row = st.number_input("📍 輸入統計結束列（不含）", min_value=1, value=1000)

sheet_data = {"HW64": [], "PTAT": [], "GPUmon": []}
summary_data = []

# 圖中指定欄位順序（固定）
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
    merged_all = []  # 合併所有資料統整用

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

    # 匯出 Excel（含統整頁）
    if any(sheet_data.values()):
        st.markdown("---")
        st.subheader("📤 匯出整合 Excel（含統整頁）")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            # 每類別寫入一張 sheet
            for sheet, dfs in sheet_data.items():
                if dfs:
                    merged = pd.concat(dfs, ignore_index=True)
                    merged.to_excel(writer, sheet_name=sheet, index=False)

            # 統整頁面（Summary）
            st.markdown("📑 產生統整頁：Summary")
            if merged_all:
                total_df = pd.concat(merged_all, ignore_index=True)
                stat_df = total_df.iloc[start_row:end_row]
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
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

        output.seek(0)
        st.download_button(
            label="⬇️ 下載整合 Excel 檔（含 Summary）",
            data=output,
            file_name="merged_log_data_with_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
