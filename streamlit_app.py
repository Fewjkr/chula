import pandas as pd
import streamlit as st
from pathlib import Path

APP_TITLE = "Specified Allowable Concentration Search System for Cosmetic Preservatives and Ingredients"
SEARCH_COMMON = "Name of Common Ingredients Glossary"
SEARCH_CAS = "CAS Number"

# -------------------------
# Helpers
# -------------------------
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
    # รองรับ encoding ทั่วไปที่เจอบ่อยกับไฟล์ไทย
    for enc in ["utf-8-sig", "utf-8", "cp874"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path)

def esc_html(s: str) -> str:
    # ป้องกันข้อความมี < > & แล้วทำให้ HTML เพี้ยน
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🧴")

# -------------------------
# Light theme + readable components
# -------------------------
st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Noto Sans Thai", sans-serif;
            color: #0f172a !important;
        }
        .stApp { background-color: #f8fafc; }

        /* header */
        .app-title {
            font-size: 34px;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.15;
            margin-bottom: 4px;
        }
        .app-subtitle {
            font-size: 15px;
            color: #334155;
        }

        /* inputs */
        input, textarea {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-radius: 10px !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-radius: 10px !important;
        }

        /* cards (containers) */
        div[data-testid="stContainer"] {
            background: #ffffff;
            border: 1px solid #bfdbfe;
            border-left: 6px solid #2563eb;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.07);
        }

        /* card title (แก้ปัญหายาวแล้วหล่นบรรทัด) */
        .card-title {
            font-size: 24px;
            font-weight: 800;
            margin: 0 0 4px 0;
            white-space: nowrap;        /* ไม่ขึ้นบรรทัดใหม่ */
            overflow: hidden;           /* ซ่อนส่วนที่เกิน */
            text-overflow: ellipsis;    /* ... */
        }
        .card-subtitle {
            font-size: 13px;
            color: #475569;
            margin: 0 0 10px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* captions */
        .stCaption { color: #475569 !important; }
        label { font-weight: 600 !important; color: #0f172a !important; }
        hr { border-color: #e2e8f0; }

        /* tighten default spacing a bit */
        .block-container { padding-top: 1.1rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# Header (logo + title)
# -------------------------
logo_path = Path("logo.png")
h1, h2 = st.columns([0.08, 0.92], vertical_alignment="center")
with h1:
    if logo_path.exists():
        st.image(str(logo_path), width=115)
with h2:
    st.markdown(f'<div class="app-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">'
        'ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสียและวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง'
        "</div>",
        unsafe_allow_html=True
    )

st.divider()

# -------------------------
# Load data
# -------------------------
df_pres = load_csv("preservatives.csv")
df_allow = load_csv("allowed.csv")
df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

# -------------------------
# Controls
# -------------------------
c1, c2 = st.columns([1.1, 2.9])
with c1:
    dataset = st.selectbox("ชุดข้อมูล", ["ข้อมูลทั้งหมด", "วัตถุกันเสีย", "วัตถุอาจใช้เป็นส่วนผสม"])
with c2:
    q = st.text_input("ค้นหา (Common หรือ CAS)", placeholder="เช่น Benzoic acid หรือ 65-85-0")

if dataset == "วัตถุกันเสีย":
    df = df_pres.copy()
elif dataset == "วัตถุอาจใช้เป็นส่วนผสม":
    df = df_allow.copy()
else:
    df = pd.concat([df_pres, df_allow], ignore_index=True)

# -------------------------
# Filter (realtime)
# -------------------------
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

# -------------------------
# Options
# -------------------------
o1, o2 = st.columns([1.2, 3.8])
with o1:
    show_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 30, 50], index=1)
with o2:
    st.caption("รายการจะแสดงรายละเอียดทั้งหมดโดยไม่ต้องกดดู")

# -------------------------
# Pagination
# -------------------------
total = len(df_f)
if total == 0:
    st.info("ไม่พบข้อมูล")
    st.stop()

pages = (total - 1) // show_per_page + 1
page = st.number_input("หน้า", min_value=1, max_value=pages, value=1, step=1)
start = (page - 1) * show_per_page
end = min(start + show_per_page, total)

st.divider()

# -------------------------
# Render cards (no expander)
# -------------------------
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

    # ✅ แก้หัวข้อยาว: เอา src ไปเป็น subtitle และตัดหัวข้อด้วย ellipsis
    main_title = f"{common} • {cas}"
    sub_title = src

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="card-title" title="{esc_html(main_title)}">{esc_html(main_title)}</div>
            <div class="card-subtitle" title="{esc_html(sub_title)}">{esc_html(sub_title)}</div>
            """,
            unsafe_allow_html=True
        )

        # แถวบน: สรุป
        a, b, c = st.columns([1.3, 1.6, 2.4])
        with a:
            st.caption("ความเข้มข้นสูงสุด")
            st.write(maxc)
        with b:
            st.caption("ข้อมูลการใช้งาน")
            st.write(f"กรณีที่ใช้: {usecase}")
        with c:
            st.caption("Chemical Name / Other Name")
            st.write(chem)

        st.markdown("---")

        # แถวล่าง: รายละเอียด
        d1, d2 = st.columns([1.3, 2.7])
        with d1:
            st.caption("ข้อมูลหลัก")
            st.write(f"**ลำดับ:** {order}")
            st.write(f"**Common:** {common}")
            st.write(f"**CAS:** {cas}")
        with d2:
            st.caption("เงื่อนไขการใช้งาน")
            st.write(cond)
