import pandas as pd
import streamlit as st

APP_TITLE = "Specified Allowable Concentration Search System for Cosmetic Preservatives and Ingredients"
SEARCH_COMMON = "Name of Common Ingredients Glossary"
SEARCH_CAS = "CAS Number"

def clean_val(v):
    if v is None:
        return "-"
    if isinstance(v, float) and pd.isna(v):
        return "-"
    s = str(v).strip()
    return "-" if s == "" or s.lower() == "nan" else s

def norm_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().str.strip()

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    for enc in ["utf-8-sig", "utf-8", "cp874"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path)

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.caption("ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสียและวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง")

# ---- load ----
df_pres = load_csv("preservatives.csv")
df_allow = load_csv("allowed.csv")
df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

# ---- controls ----
c1, c2 = st.columns([1.1, 2.9])
with c1:
    dataset = st.selectbox("ชุดข้อมูล", ["ทั้งหมด (2 ไฟล์)", "วัตถุกันเสีย", "วัตถุอาจใช้เป็นส่วนผสม"])
with c2:
    q = st.text_input("ค้นหา (Common หรือ CAS)", placeholder="เช่น Piroctone olamine หรือ 101-20-2")

if dataset == "วัตถุกันเสีย":
    df = df_pres.copy()
elif dataset == "วัตถุอาจใช้เป็นส่วนผสม":
    df = df_allow.copy()
else:
    df = pd.concat([df_pres, df_allow], ignore_index=True)

# ---- filter ----
df_f = df.copy()
qq = (q or "").strip()
if qq:
    ql = qq.lower()
    mask = False
    if SEARCH_COMMON in df_f.columns:
        mask = mask | norm_series(df_f[SEARCH_COMMON]).str.contains(ql, na=False)
    if SEARCH_CAS in df_f.columns:
        mask = mask | norm_series(df_f[SEARCH_CAS]).str.contains(ql, na=False)
    df_f = df_f[mask].copy()

df_f = df_f.reset_index(drop=True)
st.write(f"พบ {len(df_f):,} รายการ")

# ---- options ----
o1, o2 = st.columns([1.2, 3.8])
with o1:
    show_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 30, 50], index=1)
with o2:
    st.caption("รายการจะแสดงรายละเอียดทั้งหมดโดยไม่ต้องกดดู")

# ---- pagination ----
total = len(df_f)
if total == 0:
    st.info("ไม่พบข้อมูล")
    st.stop()

pages = (total - 1) // show_per_page + 1
page = st.number_input("หน้า", min_value=1, max_value=pages, value=1, step=1)
start = (page - 1) * show_per_page
end = min(start + show_per_page, total)

st.divider()

# ---- render cards (no expander) ----
for i in range(start, end):
    row = df_f.iloc[i]

    src = clean_val(row.get("แหล่งข้อมูล", "-"))
    common = clean_val(row.get(SEARCH_COMMON, "-"))
    cas = clean_val(row.get(SEARCH_CAS, "-"))
    maxc = clean_val(row.get("ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)", "-"))
    usecase = clean_val(row.get("กรณีที่ใช้", "-"))
    chem = clean_val(row.get("Chemical Name/ Other Name", "-"))
    order = clean_val(row.get("ลำดับ", "-"))
    cond = clean_val(row.get("เงื่อนไข", "-"))

    title = f"{common} • {cas} • {src}"

    with st.container(border=True):
        st.markdown(f"### {title}")

        # แถวบน: สรุป
        a, b, c = st.columns([1.2, 1.2, 2.2])
        with a:
            st.caption("ความเข้มข้นสูงสุด")
            st.write(maxc)
        with b:
            st.caption("กรณีที่ใช้")
            st.write(usecase)
        with c:
            st.caption("Chemical Name/Other Name")
            st.write(chem)

        st.markdown("---")

        # แถวล่าง: รายละเอียดทั้งหมด (อ่านง่าย)
        d1, d2 = st.columns([1.2, 2.8])
        with d1:
            st.caption("ข้อมูลหลัก")
            st.write(f"**แหล่งข้อมูล:** {src}")
            st.write(f"**ลำดับ:** {order}")
            st.write(f"**Common:** {common}")
            st.write(f"**CAS:** {cas}")
        with d2:
            st.caption("เงื่อนไขการใช้งาน")
            st.write(cond)
