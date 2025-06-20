
import streamlit as st
import pandas as pd
from io import BytesIO

try:
    import xlsxwriter
except ImportError:
    st.error("請先安裝 xlsxwriter 套件：pip install xlsxwriter")
    st.stop()

st.set_page_config(page_title="Thermal Log 整合工具 v10", layout="wide")
st.title("📊 Thermal Log 統整工具 v10（欄位比對修復＋可視化）")

uploaded_files = st.file_uploader("📂 上傳多個 CSV 或 Excel 檔案", type=["csv", "xls", "xlsx"], accept_multiple_files=True)

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
    if not isinstance(col, str):
        return ""
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
    total_max_rows = 0

    for f in uploaded_files:
        file_type = classify_file(f.name)
        if not file_type:
            st.warning(f"⚠️ 檔案 `{f.name}` 無法分類，已略過")
            continue
        try:
            if f.name.endswith(".csv"):
                if file_type == "GPUmon":
                    df_raw = pd.read_csv(f, encoding="cp950", engine="python", on_bad_lines="skip", skiprows=35)
                    df_raw.columns = df_raw.iloc[0]
                    df = df_raw.iloc[1:].reset_index(drop=True)
                else:
                    df = pd.read_csv(f, encoding="cp950", engine="python", on_bad_lines="skip")
            else:
                df = pd.read_excel(f)

            df.columns = df.columns.str.strip()
            df = df.loc[:, ~df.columns.duplicated()]  # 🔧 移除重複欄位

            if file_type == "HW64":
                df = df.iloc[5:-2].reset_index(drop=True)
            elif file_type == "PTAT":
                df = df.iloc[5:].reset_index(drop=True)

            sheet_data[file_type].append(df)
            merged_all.append(df)
            total_max_rows = max(total_max_rows, len(df))
            st.success(f"✅ 已處理 `{f.name}`（{file_type}，共 {len(df)} 筆）")
        except Exception as e:
            st.error(f"❌ 錯誤：{f.name} → {e}")

    st.markdown("### 📊 設定 Summary 統計範圍")
    start_row = st.number_input("📍 起始列 (從 0 開始)", min_value=0, value=0)
    end_row = st.number_input("📍 結束列（不含）", min_value=start_row + 1, value=total_max_rows)

    st.markdown("### 📋 Summary 統計（平均值）")
    if merged_all:
        stat_df = pd.concat(merged_all, ignore_index=True).iloc[start_row:end_row]
        stat_df.columns = stat_df.columns.str.strip()
        norm_stat_cols = [normalize(c) for c in stat_df.columns]

        results = []
        missing_columns = []

        for col in summary_columns:
            target_key = normalize(col)
            match = [c for c in stat_df.columns if normalize(c) == target_key]
            if match:
                series = pd.to_numeric(stat_df[match[0]], errors='coerce').dropna()
                value = f"{series.mean():.2f}" if not series.empty else "-"
            else:
                value = "-"
                missing_columns.append(col)
            results.append({"參數名稱": col, "平均值": value})

        summary_df = pd.DataFrame(results)
        st.dataframe(summary_df, use_container_width=True)

        if missing_columns:
            with st.expander("⚠️ 無法對應的欄位（檢查是否有誤或不存在）"):
                st.write(missing_columns)

        with st.expander("📋 所有目前欄位名稱（正規化後）"):
            st.write(norm_stat_cols)

else:
    st.info("請上傳至少一個檔案以開始。")
