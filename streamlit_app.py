import pandas as pd
import streamlit as st

APP_TITLE = "Specified Allowable Concentration Search System"

# คอลัมน์ที่แสดงในตาราง (ลำดับอยู่หน้าสุด)
TABLE_COLUMNS_ORDER = [
    "ลำดับ",
    "แหล่งข้อมูล",
    "Name of Common Ingredients Glossary",
    "CAS Number",
    "Chemical Name/ Other Name",
    "กรณีที่ใช้",
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)",
    "เงื่อนไข",  # ✅ เพิ่มกลับเข้าตาราง
]

# คอลัมน์ในรายละเอียด (แสดงเต็ม อ่านง่าย)
DETAIL_FIELDS = [
    ("แหล่งข้อมูล", "แหล่งข้อมูล"),
    ("ลำดับ", "ลำดับ"),
    ("Common", "Name of Common Ingredients Glossary"),
    ("CAS", "CAS Number"),
    ("กรณีที่ใช้", "กรณีที่ใช้"),
    ("Chemical Name/Other Name", "Chemical Name/ Other Name"),
    ("ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)", "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)"),
]

SEARCH_COMMON = "Name of Common Ingredients Glossary"
SEARCH_CAS = "CAS Number"

# ตัดคำให้พอดีช่อง (เฉพาะในตาราง)
TRUNC_LIMIT = {
    "Chemical Name/ Other Name": 55,
    "Name of Common Ingredients Glossary": 42,
    "กรณีที่ใช้": 40,
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)": 50,
    "เงื่อนไข": 80,  # ✅ ตัดคำเงื่อนไขในตาราง
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

def norm_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().str.strip()

def safe_cols(df: pd.DataFrame, cols):
    return [c for c in cols if c in df.columns]

def clean_val(v):
    if v is None:
        return "-"
    if isinstance(v, float) and pd.isna(v):
        return "-"
    s = str(v).strip()
    return "-" if s == "" or s.lower() == "nan" else s

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.caption("ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสีย และวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง")

# ----- Load -----
df_pres = load_csv("preservatives.csv")
df_allow = load_csv("allowed.csv")
df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

# ----- Controls -----
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

# ----- Filter -----
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

left, right = st.columns([3.6, 1.4])

with left:
    st.subheader("ผลการค้นหา")

    if len(df_f) == 0:
        st.info("ไม่พบข้อมูล")
        st.stop()

    # จัดคอลัมน์ตามลำดับที่ต้องการ
    table_cols = safe_cols(df_f, TABLE_COLUMNS_ORDER)
    df_table = df_f[table_cols].copy()

    # truncate ให้ดูง่ายในตาราง
    for col, lim in TRUNC_LIMIT.items():
        if col in df_table.columns:
            df_table[col] = df_table[col].apply(lambda x: trunc(clean_val(x), lim))

    # ตารางแบบอ่านอย่างเดียว
    st.data_editor(
        df_table,
        use_container_width=True,
        height=700,
        hide_index=True,
        disabled=list(df_table.columns),
        column_config={
            "ลำดับ": st.column_config.TextColumn(width="small"),
            "แหล่งข้อมูล": st.column_config.TextColumn(width="small"),
            "CAS Number": st.column_config.TextColumn(width="small"),
        },
    )

with right:
    st.subheader("รายละเอียด")

    if len(df_f) == 0:
        st.stop()

    # เลือกแถวด้วย dropdown (พิมพ์ค้นหาได้)
    def make_label(r):
        common = clean_val(r.get(SEARCH_COMMON, ""))
        cas = clean_val(r.get(SEARCH_CAS, ""))
        src = clean_val(r.get("แหล่งข้อมูล", ""))
        parts = []
        if common != "-":
            parts.append(common)
        if cas != "-":
            parts.append(f"({cas})")
        if src != "-":
            parts.append(f"- {src}")
        return " ".join(parts) if parts else f"Row {r.name}"

    labels = df_f.apply(make_label, axis=1).tolist()

    if "selected_label" not in st.session_state or st.session_state.selected_label not in labels:
        st.session_state.selected_label = labels[0]

    selected = st.selectbox(
        "เลือกรายการ (พิมพ์เพื่อค้นหาได้)",
        options=labels,
        index=labels.index(st.session_state.selected_label),
    )
    st.session_state.selected_label = selected
    idx = labels.index(selected)
    row = df_f.iloc[idx]

    st.markdown("### ข้อมูลหลัก")
    for label, key in DETAIL_FIELDS:
        st.markdown(f"**{label}**")
        st.write(clean_val(row.get(key, "-")))

    st.markdown("---")
    st.markdown("### เงื่อนไขการใช้งาน")
    cond = clean_val(row.get("เงื่อนไข", "-"))
    st.text_area("", value=cond, height=280)
