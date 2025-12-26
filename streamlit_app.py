import pandas as pd
import streamlit as st

APP_TITLE = "Specified Allowable Concentration Search System"

DISPLAY_COLUMNS = [
    "ลำดับ",
    "Chemical Name/ Other Name",
    "Name of Common Ingredients Glossary",
    "CAS Number",
    "กรณีที่ใช้",
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)",
    "เงื่อนไข",
]

SEARCH_COMMON = "Name of Common Ingredients Glossary"
SEARCH_CAS = "CAS Number"

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "cp874"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path)

def safe_cols(df: pd.DataFrame, cols):
    return [c for c in cols if c in df.columns]

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.caption("ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสีย และวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง")

df_pres = load_csv("preservatives.csv")
df_allow = load_csv("allowed.csv")
df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

dataset = st.selectbox("ชุดข้อมูล", ["ทั้งหมด (2 ไฟล์)", "วัตถุกันเสีย", "วัตถุอาจใช้เป็นส่วนผสม"])

if dataset == "วัตถุกันเสีย":
    df = df_pres.copy()
elif dataset == "วัตถุอาจใช้เป็นส่วนผสม":
    df = df_allow.copy()
else:
    df = pd.concat([df_pres, df_allow], ignore_index=True)

cols = safe_cols(df, DISPLAY_COLUMNS)
show_cols = ["แหล่งข้อมูล"] + cols if "แหล่งข้อมูล" in df.columns else cols

q = st.text_input("ค้นหา (Common หรือ CAS)", placeholder="เช่น Piroctone olamine หรือ 101-20-2")

if q.strip():
    ql = q.strip().lower()
    mask = False
    if SEARCH_COMMON in df.columns:
        mask = mask | df[SEARCH_COMMON].astype(str).str.lower().str.contains(ql, na=False)
    if SEARCH_CAS in df.columns:
        mask = mask | df[SEARCH_CAS].astype(str).str.lower().str.contains(ql, na=False)
    df_f = df[mask].copy()
else:
    df_f = df.copy()

st.write(f"พบ {len(df_f):,} แถว")

left, right = st.columns([3.4, 1.2])

with left:
    st.subheader("ผลการค้นหา")
    df_view = df_f[show_cols].reset_index(drop=True)

    # เลือกแถวด้วย radio (ง่ายกว่า index)
    if len(df_view) == 0:
        st.dataframe(df_view, use_container_width=True, height=620)
        st.stop()

    st.dataframe(df_view, use_container_width=True, height=620)

with right:
    st.subheader("รายละเอียด")

    idx = st.number_input(
        "Row index (ดูจากแถวในตารางฝั่งซ้าย)",
        min_value=0,
        max_value=max(len(df_view) - 1, 0),
        value=0,
        step=1,
    )

    row = df_view.iloc[int(idx)]

    def show_field(label, key):
        if key in row.index:
            val = row[key]
            if pd.isna(val) or str(val).strip() == "":
                val = "-"
            st.markdown(f"**{label}**  \n{val}")

    show_field("แหล่งข้อมูล", "แหล่งข้อมูล")
    show_field("ลำดับ", "ลำดับ")
    show_field("Common", SEARCH_COMMON)
    show_field("CAS", SEARCH_CAS)
    show_field("กรณีที่ใช้", "กรณีที่ใช้")
    show_field("Chemical", "Chemical Name/ Other Name")
    show_field("ความเข้มข้นสูงสุด", "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)")

    st.markdown("**เงื่อนไข**")
    cond = row["เงื่อนไข"] if "เงื่อนไข" in row.index else "-"
    if pd.isna(cond) or str(cond).strip() == "":
        cond = "-"
    st.text_area("", value=str(cond), height=240)
