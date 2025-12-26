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

TRUNC_LIMIT = {
    "Chemical Name/ Other Name": 60,
    "Name of Common Ingredients Glossary": 46,
    "กรณีที่ใช้": 42,
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)": 60,
    "เงื่อนไข": 90,
}

def trunc(s, n):
    s = "" if s is None else str(s)
    s = " ".join(s.split())
    if n and len(s) > n:
        return s[: max(0, n - 1)] + "…"
    return s

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

def norm_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().str.strip()

st.set_page_config(page_title=APP_TITLE, layout="wide")

# --- Header ---
st.title(APP_TITLE)
st.caption("ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสีย และวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง")

# --- Load data ---
df_pres = load_csv("preservatives.csv")
df_allow = load_csv("allowed.csv")
df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

# --- Controls ---
c1, c2 = st.columns([1.2, 2.8])
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

cols = safe_cols(df, DISPLAY_COLUMNS)
show_cols = ["แหล่งข้อมูล"] + cols

# --- Filter ---
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
st.write(f"พบ {len(df_f):,} แถว")

left, right = st.columns([3.4, 1.6])

with left:
    st.subheader("ผลการค้นหา")

    if len(df_f) == 0:
        st.info("ไม่พบข้อมูล")
        st.stop()

    df_view = df_f[show_cols].copy()
    for col, lim in TRUNC_LIMIT.items():
        if col in df_view.columns:
            df_view[col] = df_view[col].apply(lambda x: trunc(x, lim))

    st.dataframe(df_view, use_container_width=True, height=680)

with right:
    st.subheader("รายละเอียด")

    # สร้าง label ให้เลือก (พิมพ์ค้นหาใน dropdown ได้)
    def make_label(r):
        common = str(r.get(SEARCH_COMMON, "")).strip()
        cas = str(r.get(SEARCH_CAS, "")).strip()
        src = str(r.get("แหล่งข้อมูล", "")).strip()
        parts = []
        if common:
            parts.append(common)
        if cas and cas != "nan":
            parts.append(f"({cas})")
        if src:
            parts.append(f"- {src}")
        return " ".join(parts) if parts else f"Row {r.name}"

    labels = df_f.apply(make_label, axis=1).tolist()

    if "selected_label" not in st.session_state:
        st.session_state.selected_label = labels[0]

    selected = st.selectbox(
        "เลือกรายการ (พิมพ์เพื่อค้นหาได้)",
        options=labels,
        index=labels.index(st.session_state.selected_label) if st.session_state.selected_label in labels else 0,
    )
    st.session_state.selected_label = selected
    idx = labels.index(selected)
    row = df_f.iloc[idx]

    # แสดงแบบอ่านง่ายเป็น section
    st.markdown("### ข้อมูลหลัก")
    st.write(f"**แหล่งข้อมูล:** {row.get('แหล่งข้อมูล','-')}")
    st.write(f"**ลำดับ:** {row.get('ลำดับ','-')}")
    st.write(f"**Common:** {row.get(SEARCH_COMMON,'-')}")
    st.write(f"**CAS:** {row.get(SEARCH_CAS,'-')}")
    st.write(f"**กรณีที่ใช้:** {row.get('กรณีที่ใช้','-')}")

    st.markdown("---")
    st.markdown("### รายละเอียดสาร")
    st.write(f"**Chemical Name/Other Name:** {row.get('Chemical Name/ Other Name','-')}")
    st.write(f"**ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w):** {row.get('ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)','-')}")

    st.markdown("---")
    st.markdown("### เงื่อนไข")
    cond = row.get("เงื่อนไข", "-")
    cond = "-" if (pd.isna(cond) or str(cond).strip() == "") else str(cond)
    st.text_area("", value=cond, height=280)
