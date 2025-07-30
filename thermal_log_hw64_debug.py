
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO, StringIO

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

st.set_page_config(page_title="Thermal Log Debug Tool", layout="wide")
st.title("🛠️ Thermal Log Debug 工具（HW64資料讀取測試）")

uploaded_file = st.file_uploader("請上傳一個 HW64 thermal log CSV 檔", type="csv")

if uploaded_file:
    filename = uploaded_file.name
    file_type = classify_file(filename)

    st.write(f"📄 檔案名稱：{filename}")
    st.write(f"🔍 判定檔案類型：{file_type}")

    try:
        df = pd.read_csv(uploaded_file, encoding='cp950', engine='python', on_bad_lines='skip', quoting=3)
        st.success("✅ 成功讀取檔案")
        st.write(f"📏 原始資料筆數：{len(df)}")
        st.write(f"📐 欄位數：{len(df.columns)}")

        st.subheader("📋 欄位名稱")
        st.write(df.columns.tolist())

        st.subheader("🔎 前 20 筆資料")
        st.dataframe(df.head(20))

        st.subheader("🔎 後 20 筆資料")
        st.dataframe(df.tail(20))

    except Exception as e:
        st.error(f"❌ 讀取檔案失敗：{e}")
else:
    st.info("請上傳一份 HW64 檔案以進行分析。")
