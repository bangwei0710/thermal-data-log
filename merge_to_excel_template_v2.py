
import streamlit as st
import pandas as pd
from io import BytesIO

# 嘗試使用 xlsxwriter，若缺少套件則提示
try:
    import xlsxwriter
except ImportError:
    st.error("⚠️ 請先安裝 xlsxwriter 套件：請執行 `pip install xlsxwriter`")
    st.stop()

st.set_page_config(page_title="Thermal Log 整合工具", layout="wide")
st.title("📊 Thermal Log 多檔案整合 → 指定 Excel 格式")

st.markdown("請上傳多份資料檔案（CSV 或 Excel），系統將根據檔名自動分類為：`HW64`、`PTAT`、`GPUmon`，並輸出為對應格式的 Excel 檔案。")

uploaded_files = st.file_uploader("📂 上傳多個資料檔", type=["csv", "xls", "xlsx"], accept_multiple_files=True)

sheet_data = {"HW64": [], "PTAT": [], "GPUmon": []}

def normalize_columns(df):
    df.columns = df.columns.str.strip()
    return df

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
    for f in uploaded_files:
        file_type = classify_file(f.name)
        if not file_type:
            st.warning(f"⚠️ 檔案 `{f.name}` 無法識別類型，已略過")
            continue

        try:
            if f.name.endswith(".csv"):
                df = pd.read_csv(f, encoding="cp950", engine="python", on_bad_lines="skip")
            else:
                df = pd.read_excel(f)
            df = normalize_columns(df)
            if file_type == "GPUmon":
                df = df.iloc[35:].reset_index(drop=True)
            sheet_data[file_type].append(df)
            st.success(f"✅ 已成功載入 `{f.name}` → 分類為 {file_type}")
        except Exception as e:
            st.error(f"❌ 載入錯誤：{f.name} → {e}")

    # 整合並匯出 Excel
    if any(sheet_data.values()):
        st.markdown("---")
        st.subheader("📤 匯出格式化 Excel")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, dfs in sheet_data.items():
                if dfs:
                    merged = pd.concat(dfs, ignore_index=True)
                    merged.to_excel(writer, sheet_name=sheet, index=False)
        output.seek(0)

        st.download_button(
            label="⬇️ 下載整合後 Excel",
            data=output,
            file_name="merged_log_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
