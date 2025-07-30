
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO, StringIO

def normalize(col):
    if not isinstance(col, str):
        return ""
    return col.strip().lower().replace(" ", "").replace(":", "").replace("（", "(").replace("）", ")")

def classify_file(filename):
    lower = filename.lower()
    if "gpu" in lower:
        return "GPUmon"
    elif "ptat" in lower:
        return "PTAT"
    elif "hw" in lower:
        return "HW64"
    else:
        return "Other"

column_alias_map = {
    'Total System Power [W]': ['Total System Power [W]', 'System Power(W)'],
    'CPU Package Power [W]': ['CPU Package Power [W]', 'CPU Package [W]'],
    ' 1:TGP (W)': ['1:TGP (W)', 'TGP(W)', 'GPU TGP(W)'],
    'Charge Rate [W]': ['Charge Rate [W]', 'Charger In(W)'],
    'IA Cores Power [W]': ['IA Cores Power [W]'],
    'GT Cores Power [W]': ['GT Cores Power [W]'],
    ' 1:NVVDD Power (W)': ['1:NVVDD Power (W)'],
    ' 1:FBVDD Power (W)': ['1:FBVDD Power (W)'],
    'CPU Package [蚓]': ['CPU Package [蚓]', 'CPU Temperature(°C)', 'CPU Package(C)'],
    ' 1:Temperature GPU (C)': ['1:Temperature GPU (C)', 'GPU Temperature(°C)', '1:GPU Temperature (C)'],
    ' 1:Temperature Memory (C)': ['1:Temperature Memory (C)', 'Memory Temperature(°C)', '1:Memory Temperature (C)'],
    'SEN1-temp(Degree C)': ['SEN1-temp(Degree C)', 'Temp0 [°C]'],
    'SEN2-temp(Degree C)': ['SEN2-temp(Degree C)', 'Temp1 [°C]'],
    'SEN3-temp(Degree C)': ['SEN3-temp(Degree C)', 'Temp2 [°C]'],
    'SEN4-temp(Degree C)': ['SEN4-temp(Degree C)', 'Temp3 [°C]'],
    'SEN5-temp(Degree C)': ['SEN5-temp(Degree C)', 'Temp4 [°C]'],
    'SEN6-temp(Degree C)': ['SEN6-temp(Degree C)', 'Temp5 [°C]'],
    'SEN7-temp(Degree C)': ['SEN7-temp(Degree C)', 'Temp6 [°C]'],
    'SEN8-temp(Degree C)': ['SEN8-temp(Degree C)', 'Temp7 [°C]'],
    'SEN9-temp(Degree C)': ['SEN9-temp(Degree C)', 'Temp8 [°C]'],
}

st.set_page_config(page_title="Thermal Log 分析工具 v6.4", layout="wide")
st.title("Thermal Log 分析工具（v6.4 - 常用欄位別名比對修正）")

uploaded_files = st.file_uploader("請上傳 thermal log 的 CSV 檔（可多選）", type="csv", accept_multiple_files=True)

all_dataframes = {}
file_column_selection = {}
file_range_selection = {}
valid_dataframes = []

if uploaded_files:
    st.info("📌 每個檔案可選擇多個欄位與資料範圍，圖表支援高解析度（DPI 200）")

    for uploaded_file in uploaded_files:
        try:
            filename = uploaded_file.name
            shortname = filename.split('/')[-1]
            file_type = classify_file(filename)

            if file_type == "GPUmon":
                all_lines = uploaded_file.getvalue().decode('cp950').splitlines()
                df = pd.read_csv(StringIO("\n".join(all_lines[35:])), encoding='cp950', engine='python')
            elif file_type == "PTAT":
                df = pd.read_csv(uploaded_file, encoding='cp950', engine='python', on_bad_lines='skip')
                df = df.iloc[5:].reset_index(drop=True)
            elif file_type == "HW64":
                df = pd.read_csv(uploaded_file, encoding='cp950', engine='python', on_bad_lines='skip', quoting=3)
                df = df.reset_index(drop=True)
                if not pd.to_numeric(df.iloc[-1].dropna(), errors='coerce').notna().all():
                    df = df.iloc[:-1]
                df.columns = df.columns.str.strip()
            else:
                df = pd.read_csv(uploaded_file, encoding='cp950', engine='python', on_bad_lines='skip')
                df = df.reset_index(drop=True)
                df.columns = df.columns.str.strip()

            all_dataframes[shortname] = df
            valid_dataframes.append((shortname, df))

        except Exception as e:
            st.error(f"❌ 檔案 {filename} 發生錯誤：{e}")

    st.markdown("---")
    st.subheader("📌 常用參數彙總（支援別名自動對應）")

    unique_param_results = []
    added_keys = set()

    for shortname, df in valid_dataframes:
        df_tail = df.tail(600)
        for standard_name, alias_list in column_alias_map.items():
            norm_key = normalize(standard_name)
            if norm_key in added_keys:
                continue
            match = [c for c in df_tail.columns if normalize(c) in [normalize(a) for a in alias_list]]
            if match:
                values = pd.to_numeric(df_tail[match[0]], errors='coerce').dropna()
                value = f"{values.mean():.2f}" if not values.empty else "-"
                unique_param_results.append((standard_name, value))
                added_keys.add(norm_key)

    summary_df = pd.DataFrame(unique_param_results, columns=["參數名稱", "數值"])
    summary_df = summary_df.set_index("參數名稱").reindex(column_alias_map.keys()).reset_index()
    st.dataframe(summary_df)
