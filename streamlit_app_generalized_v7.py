import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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

st.set_page_config(page_title="Thermal Log 分析工具 v6", layout="wide")
st.title("Thermal Log 分析工具（格式修正 v6）")

uploaded_files = st.file_uploader("請上傳 thermal log 的 CSV 檔（可多選）", type="csv", accept_multiple_files=True)

all_dataframes = {}
file_column_selection = {}
file_range_selection = {}
valid_dataframes = []
common_params = [
    'Total System Power [W]', 'CPU Package Power [W]', ' 1:TGP (W)', 'Charge Rate [W]',
    'IA Cores Power [W]', 'GT Cores Power [W]', ' 1:NVVDD Power (W)', ' 1:FBVDD Power (W)',
    'CPU Package [蚓]', ' 1:Temperature GPU (C)', ' 1:Temperature Memory (C)',
    'SEN1-temp(Degree C)', 'SEN2-temp(Degree C)', 'SEN3-temp(Degree C)', 'SEN4-temp(Degree C)',
    'SEN5-temp(Degree C)', 'SEN6-temp(Degree C)', 'SEN7-temp(Degree C)', 'SEN8-temp(Degree C)', 'SEN9-temp(Degree C)'
]

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
                df = pd.read_csv(uploaded_file, encoding='cp950', engine='python', skipfooter=2, on_bad_lines='skip')
                df = df.iloc[5:].reset_index(drop=True)
            else:
                df = pd.read_csv(uploaded_file, encoding='cp950', engine='python', on_bad_lines='skip')
                df = df.reset_index(drop=True)

            df.columns = df.columns.str.strip()
            all_dataframes[shortname] = df
            valid_dataframes.append((shortname, df))

            st.markdown(f"---\n### 📁 檔案：{shortname}")

            selected_cols = st.multiselect(f"選擇要分析的欄位（{shortname}）", df.columns.tolist(), key='col_' + shortname)
            file_column_selection[shortname] = selected_cols

            total_rows = len(df)
            start_index = st.number_input(f"從第 N 筆開始（{shortname}）", min_value=0, max_value=total_rows - 1, value=0, key='start_' + shortname)
            end_index = st.number_input(f"到第 M 筆結束（{shortname}）", min_value=start_index + 1, max_value=total_rows, value=total_rows, key='end_' + shortname)
            file_range_selection[shortname] = (start_index, end_index)

            if selected_cols:
                df_subset = df.iloc[start_index:end_index]
                st.write("📊 統計資訊：")
                for col in selected_cols:
                    series = pd.to_numeric(df_subset[col], errors='coerce').dropna()
                    st.write(f"🔹 **{col}**")
                    st.write(f"- 最大值：{series.max():.2f}")
                    st.write(f"- 最小值：{series.min():.2f}")
                    st.write(f"- 平均值：{series.mean():.2f}")

        except Exception as e:
            st.error(f"❌ 檔案 {filename} 發生錯誤：{e}")

    st.markdown("---")
    st.subheader("📌 常用參數彙總（唯一值，不顯示檔名）")

    unique_param_results = []
    added_keys = set()

    for shortname, df in valid_dataframes:
        df_tail = df.tail(600)
        for col in common_params:
            key = normalize(col)
            if key in added_keys:
                continue
            match = [c for c in df_tail.columns if normalize(c) == key]
            if match:
                values = pd.to_numeric(df_tail[match[0]], errors='coerce').dropna()
                value = f"{values.mean():.2f}" if not values.empty else "-"
                unique_param_results.append((col, value))
                added_keys.add(key)

    summary_df = pd.DataFrame(unique_param_results, columns=["參數名稱", "數值"])
    desired_order = [
        'Total System Power [W]', 'CPU Package Power [W]', ' 1:TGP (W)', 'Charge Rate [W]',
        'IA Cores Power [W]', 'GT Cores Power [W]', ' 1:NVVDD Power (W)', ' 1:FBVDD Power (W)',
        'CPU Package [蚓]', ' 1:Temperature GPU (C)', ' 1:Temperature Memory (C)',
        'SEN1-temp(Degree C)', 'SEN2-temp(Degree C)', 'SEN3-temp(Degree C)', 'SEN4-temp(Degree C)',
        'SEN5-temp(Degree C)', 'SEN6-temp(Degree C)', 'SEN7-temp(Degree C)', 'SEN8-temp(Degree C)', 'SEN9-temp(Degree C)'
    ]
    summary_df = summary_df.set_index("參數名稱").reindex(desired_order).reset_index()
    st.dataframe(summary_df)

    export_raw_dataframes = []
    for shortname, df in all_dataframes.items():
        selected_cols = file_column_selection.get(shortname, [])
        start_index, end_index = file_range_selection.get(shortname, (0, len(df)))
        if selected_cols:
            df_subset = df.iloc[start_index:end_index][selected_cols].copy()
            export_raw_dataframes.append(df_subset.reset_index(drop=True))

    if export_raw_dataframes:
        merged_export = pd.concat(export_raw_dataframes, axis=1)
        buffer = BytesIO()
        merged_export.to_csv(buffer, index=False, encoding='utf-8-sig')
        buffer.seek(0)
        st.download_button("⬇️ 匯出所選 raw data 為 CSV", buffer, file_name="selected_raw_data.csv", mime="text/csv")

    chart_title = st.text_input("🖋️ 圖表標題", value="跨檔案多欄位比較圖")
    st.subheader("📈 同圖比較曲線圖")
    fig, ax = plt.subplots(figsize=(12, 5), dpi=200)

    for shortname, df in all_dataframes.items():
        selected_cols = file_column_selection.get(shortname, [])
        start_index, end_index = file_range_selection.get(shortname, (0, len(df)))
        df_subset = df.iloc[start_index:end_index]
        for col in selected_cols:
            if col in df_subset.columns:
                series = pd.to_numeric(df_subset[col], errors='coerce').dropna()
                ax.plot(series.reset_index(drop=True), label=f"{shortname} - {col}")

    ax.set_title(chart_title)
    ax.set_xlabel("Index")
    ax.set_ylabel("Value")
    ax.grid(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, frameon=False)
    st.pyplot(fig)

    labels = []
    for shortname, df in all_dataframes.items():
        selected_cols = file_column_selection.get(shortname, [])
        for col in selected_cols:
            if col in df.columns:
                labels.append(f"{shortname} - {col}")
    if labels:
        st.markdown("**📋 曲線項目說明：**")
        st.markdown("<br>".join(labels), unsafe_allow_html=True)
else:
    st.info("請上傳至少一個檔案以開始。")
