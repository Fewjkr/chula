import pandas as pd
import streamlit as st

# ===============================
# CONFIG
# ===============================
APP_TITLE = "Specified Allowable Concentration Search System for Cosmetic Preservatives and Ingredients"
SEARCH_COMMON = "Name of Common Ingredients Glossary"
SEARCH_CAS = "CAS Number"

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    page_icon="🧴"
)

# ===============================
# STYLE (ธีม + layout)
# ===============================
st.markdown(
    """
    <style>
        html, body, [class*="css"]  {
            font-family: "Segoe UI", "Noto Sans Thai", sans-serif;
        }

        /* พื้นหลังหลัก */
        .stApp {
            background: linear-gradient(180deg, #0b1220 0%, #0e1628 100%);
        }

        /* กล่อง card */
        div[data-testid="stContainer"] {
            background-color: #0f1a30;
            border-radius: 14px;
            padding: 18px;
            border: 1px solid #1f2a44;
        }

        /* หัวข้อใหญ่ */
        .app-title {
            font-size: 40px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 6px;
        }

        .app-subtitle {
            font-size: 16px;
            color: #cbd5e1;
        }

        /* label */
        label {
            font-weight: 600 !important;
            color: #e5e7eb !important;
        }

        /* เส้นคั่น */
        hr {
            border-color: #1f2a44;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ===============================
# HEADER (โลโก้ + ชื่อ)
# ===============================
h1, h2 = st.columns([0.12, 0.88], vertical_alignment="center")
with h1:
    st.image("logo.png", width=72)
with h2:
    st.markdown(f'<div class="app-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">'
        'ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสียและวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง'
        '</div>',
        unsafe_allow_html=True
    )

st.divider()

# ===============================
# UTILS
# ===============================
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

# ===============================
# LOAD DATA
# ===============================
df_pres = load_csv("preservatives.csv")
df_allow = load_csv("allowed.csv")

df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

# ===============================
# CONTROLS
# ===============================
c1, c2 = st.columns([1.2, 2.8])
with c1:
    dataset = st.selectbox(
        "ชุดข้อมูล",
        ["ทั้งหมด (2 ไฟล์)", "วัตถุกันเสีย", "วัตถุอาจใช้เป็นส่วนผสม"]
    )
with c2:
    q = st.text_input(
        "ค้นหา (Common หรือ CAS)",
        placeholder="เช่น Benzoic acid หรือ 65-85-0"
    )

if dataset == "วัตถุกันเสีย":
    df = df_pres.copy()
elif dataset == "วัตถุอาจใช้เป็นส่วนผสม":
    df = df_allow.copy()
else:
    df = pd.concat([df_pres, df_allow], ignore_index=True)

# ===============================
# FILTER
# ===============================
df_f = df.copy()
if q.strip():
    ql = q.lower()
    mask = False
    if SEARCH_COMMON in df_f.columns:
        mask = mask | norm_series(df_f[SEARCH_COMMON]).str.contains(ql, na=False)
    if SEARCH_CAS in df_f.columns:
        mask = mask | norm_series(df_f[SEARCH_CAS]).str.contains(ql, na=False)
    df_f = df_f[mask].copy()

df_f = df_f.reset_index(drop=True)
st.write(f"พบ {len(df_f):,} รายการ")

# ===============================
# PAGINATION
# ===============================
p1, p2 = st.columns([1.2, 2.8])
with p1:
    show_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 30, 50], index=1)
with p2:
    st.caption("แสดงข้อมูลทั้งหมดในแต่ละรายการ (ไม่ต้องกดดูรายละเอียด)")

total = len(df_f)
if total == 0:
    st.info("ไม่พบข้อมูล")
    st.stop()

pages = (total - 1) // show_per_page + 1
page = st.number_input("หน้า", min_value=1, max_value=pages, value=1, step=1)

start = (page - 1) * show_per_page
end = min(start + show_per_page, total)

st.divider()

# ===============================
# RENDER CARDS
# ===============================
for i in range(start, end):
    row = df_f.iloc[i]

    common = clean_val(row.get(SEARCH_COMMON))
    cas = clean_val(row.get(SEARCH_CAS))
    src = clean_val(row.get("แหล่งข้อมูล"))
    order = clean_val(row.get("ลำดับ"))

    maxc = clean_val(row.get("ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)"))
    usecase = clean_val(row.get("กรณีที่ใช้"))
    chem = clean_val(row.get("Chemical Name/ Other Name"))
    cond = clean_val(row.get("เงื่อนไข"))

    with st.container():
        st.markdown(f"### {common} • {cas}")
        st.caption(f"แหล่งข้อมูล: {src} | ลำดับ: {order}")

        a, b, c = st.columns([1.2, 1.2, 2.2])
        with a:
            st.caption("ความเข้มข้นสูงสุด")
            st.write(maxc)
        with b:
            st.caption("กรณีที่ใช้")
            st.write(usecase)
        with c:
            st.caption("Chemical Name / Other Name")
            st.write(chem)

        st.markdown("**เงื่อนไขการใช้งาน**")
        st.write(cond)
