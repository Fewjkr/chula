import pandas as pd
import streamlit as st
from pathlib import Path

APP_TITLE = "Specified Allowable Concentration Search System for Cosmetic Preservatives and Ingredients"

# ---- Column names (หลัก ๆ) ----
COL_COMMON = "Name of Common Ingredients Glossary"
COL_CAS = "CAS Number"
COL_CHEM = "Chemical Name/ Other Name"
COL_MAXC = "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)"
COL_USECASE = "กรณีที่ใช้"
COL_COND = "เงื่อนไข"
COL_ORDER = "ลำดับ"

# ---- allowed.csv อาจมีคอลัมน์เพิ่ม ----
AREA_COL_CANDIDATES = [
    "บริเวณที่ใช้",
    "บริเวณ",
    "บริเวณที่ใช้ และ/หรือ การนำไปใช้",
    "Area of use",
    "Area of Use",
    "Use area",
    "Use Area",
    "บริเวณ/ส่วนของร่างกายที่ใช้",
]

# -------------------- Helpers --------------------
def clean_val(v):
    if v is None:
        return "-"
    try:
        if isinstance(v, float) and pd.isna(v):
            return "-"
    except Exception:
        pass
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return "-"
    return s

def norm_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().str.strip()

def pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    last_err = None
    for enc in ["utf-8-sig", "utf-8", "cp874", "tis-620"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_err = e
    try:
        return pd.read_csv(path)
    except Exception:
        raise last_err

def find_logo_path() -> str | None:
    candidates = [
        "logo.png", "logo.jpg", "logo.jpeg", "logo.webp",
        "logo.PNG", "logo.JPG", "logo.JPEG", "logo.WEBP",
    ]
    for name in candidates:
        p = Path(name)
        if p.exists() and p.is_file():
            return str(p)
    return None

def build_title(common: str, cas: str) -> str:
    # หัวการ์ด: เน้น Common ก่อน (ไม่เอา CAS ไปไว้บนหัว)
    if common != "-" and common.strip():
        return common
    if cas != "-" and cas.strip():
        return cas
    return "-"

# -------------------- Page config --------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")

# -------------------- CSS (Light + modern cards) --------------------
st.markdown(
    """
<style>
/* ===== Page ===== */
.stApp { background: #f6f8fc !important; }
html, body, [class*="css"] {
  font-family: "Segoe UI", "Noto Sans Thai", "Noto Sans", sans-serif !important;
}
.block-container { padding-top: 1.75rem !important; padding-bottom: 2.5rem !important; }
@media (min-width: 1200px){
  .block-container { max-width: 1280px; }
}

/* Force readable text on light bg */
.stApp, .stApp * { color: #0f172a !important; }
.stCaption, .stCaption * { color: #475569 !important; opacity: 1 !important; }
h1, h2, h3, h4, h5, h6 { color: #0f172a !important; }

/* Divider */
hr { border-color: #e2e8f0 !important; }

/* ===== Inputs ===== */
input, textarea {
  background: #ffffff !important;
  color: #0f172a !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 14px !important;
  box-shadow: none !important;
}
input:focus, textarea:focus {
  border: 2px solid #2563eb !important;
  outline: none !important;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12) !important;
}

/* Selectbox */
div[data-baseweb="select"] > div{
  background: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 14px !important;
  box-shadow: none !important;
}
div[data-baseweb="select"] > div:focus-within{
  border: 2px solid #2563eb !important;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12) !important;
}
div[data-baseweb="select"] span{ color: #0f172a !important; }
label { font-weight: 800 !important; }

/* ===== Number input +/- buttons ===== */
div[data-testid="stNumberInput"]{
  align-items: center !important;
}
div[data-testid="stNumberInput"] input{
  border-radius: 14px !important;
}
div[data-testid="stNumberInput"] button {
  background: #2563eb !important;
  border: 1px solid #1d4ed8 !important;
  color: #ffffff !important;
  border-radius: 12px !important;
  width: 44px !important;
  height: 40px !important;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.16) !important;
}
div[data-testid="stNumberInput"] button:hover { filter: brightness(0.96) !important; }
div[data-testid="stNumberInput"] button svg { fill: #ffffff !important; }

/* ===== Cards ===== */
div[data-testid="stContainer"]{
  background: #ffffff !important;
  border: 1px solid #c7ddff !important;
  border-left: 10px solid #2563eb !important;
  border-radius: 18px !important;
  padding: 18px 18px 16px 18px !important;
  margin-bottom: 16px !important;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06) !important;
}

/* Card title/subtitle with ellipsis */
.card-title{
  font-size: 26px !important;
  font-weight: 900 !important;
  line-height: 1.2 !important;
  margin: 0 0 6px 0 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.card-subtitle{
  font-size: 13px !important;
  color: #475569 !important;
  margin: 0 0 10px 0 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Pills */
.pill{
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8 !important;
  margin-right: 8px;
  margin-bottom: 6px;
}

/* Section titles */
.section-title{
  font-size: 14px;
  font-weight: 900;
  margin: 12px 0 6px 0;
  color: #0f172a !important;
}

/* Columns spacing */
[data-testid="column"] { padding-right: 10px; padding-left: 10px; }

/* Header layout */
.header-wrap{
  margin-top: 12px; /* ลงมานิดหน่อยด้านบน */
  margin-bottom: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------- Header (Logo + Title) --------------------
logo_path = find_logo_path()

st.markdown('<div class="header-wrap">', unsafe_allow_html=True)
h1, h2 = st.columns([0.18, 0.82], vertical_alignment="center")

with h1:
    if logo_path:
        # ทำให้ใหญ่ขึ้นให้สมส่วน
        st.image(logo_path, width=180)

with h2:
    st.markdown(f"## {APP_TITLE}")
    st.caption("ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสีย และวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง")

st.markdown("</div>", unsafe_allow_html=True)
st.divider()

# -------------------- Load data --------------------
df_pres = None
df_allow = None

try:
    df_pres = load_csv("preservatives.csv")
except Exception:
    pass

try:
    df_allow = load_csv("allowed.csv")
except Exception:
    pass

if df_pres is None and df_allow is None:
    st.error("ไม่พบไฟล์ preservatives.csv และ allowed.csv ในโฟลเดอร์เดียวกับไฟล์ streamlit_app.py")
    st.stop()

if df_pres is not None:
    df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
if df_allow is not None:
    df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

# -------------------- Controls --------------------
left, right = st.columns([1.35, 3.0])
with left:
    options = []
    if df_pres is not None and df_allow is not None:
        options = ["ข้อมูลทั้งหมด", "วัตถุกันเสีย", "วัตถุอาจใช้เป็นส่วนผสม"]
    elif df_pres is not None:
        options = ["วัตถุกันเสีย"]
    else:
        options = ["วัตถุอาจใช้เป็นส่วนผสม"]
    dataset = st.selectbox("ชุดข้อมูล", options)

with right:
    q = st.text_input("ค้นหา (Common หรือ CAS)", placeholder="เช่น Benzoic acid หรือ 65-85-0")

# dataset selection
if dataset == "วัตถุกันเสีย":
    df = df_pres.copy()
elif dataset == "วัตถุอาจใช้เป็นส่วนผสม":
    df = df_allow.copy()
else:
    df = pd.concat([df_pres, df_allow], ignore_index=True)

# -------------------- Filter realtime (Common + CAS เท่านั้น) --------------------
df_f = df.copy()
qq = (q or "").strip()
if qq:
    ql = qq.lower()
    mask = False
    if COL_COMMON in df_f.columns:
        mask = mask | norm_series(df_f[COL_COMMON]).str.contains(ql, na=False)
    if COL_CAS in df_f.columns:
        mask = mask | norm_series(df_f[COL_CAS]).str.contains(ql, na=False)
    df_f = df_f[mask].copy()

df_f = df_f.reset_index(drop=True)
st.write(f"พบ **{len(df_f):,}** รายการ")

# -------------------- Pagination --------------------
c1, c2, c3 = st.columns([1.0, 1.4, 2.6])
with c1:
    show_per_page = st.selectbox("แสดงต่อหน้า", [10, 20, 30, 50], index=1)
with c2:
    total = len(df_f)
    pages = (total - 1) // show_per_page + 1 if total else 1
    page = st.number_input("หน้า", min_value=1, max_value=pages, value=1, step=1)
with c3:
    st.caption("แสดงแบบ Block ครบทุกข้อมูล (ไม่ต้องกดดูรายละเอียด)")

if len(df_f) == 0:
    st.info("ไม่พบข้อมูล")
    st.stop()

start = (page - 1) * show_per_page
end = min(start + show_per_page, len(df_f))

st.divider()

# -------------------- Render cards --------------------
area_col = pick_col(df_f, AREA_COL_CANDIDATES)

for i in range(start, end):
    row = df_f.iloc[i]

    src = clean_val(row.get("แหล่งข้อมูล", "-"))
    common = clean_val(row.get(COL_COMMON, "-"))
    cas = clean_val(row.get(COL_CAS, "-"))
    chem = clean_val(row.get(COL_CHEM, "-"))
    maxc = clean_val(row.get(COL_MAXC, "-"))
    usecase = clean_val(row.get(COL_USECASE, "-"))
    cond = clean_val(row.get(COL_COND, "-"))
    order = clean_val(row.get(COL_ORDER, "-"))

    # เฉพาะ allowed เท่านั้น: บริเวณที่ใช้
    area_val = "-"
    if src == "วัตถุอาจใช้เป็นส่วนผสม" and area_col is not None:
        area_val = clean_val(row.get(area_col, "-"))

    title = build_title(common, cas)

    with st.container(border=True):
        # Title: Common (ไม่ใส่ CAS บนหัว)
        st.markdown(f'<div class="card-title">{title}</div>', unsafe_allow_html=True)

        # Subtitle: "วัตถุกันเสีย • ลำดับ: 1" (ตัด CAS ออกไป)
        subtitle_parts = []
        if src != "-":
            subtitle_parts.append(src)
        if order != "-":
            subtitle_parts.append(f"ลำดับ: {order}")
        subtitle = " • ".join(subtitle_parts)
        if subtitle:
            st.markdown(f'<div class="card-subtitle">{subtitle}</div>', unsafe_allow_html=True)

        # Summary row (เพิ่ม CAS เป็นหัวข้อแยก)
        a, b, c, d = st.columns([1.1, 1.1, 1.1, 2.2])
        with a:
            st.markdown('<span class="pill">CAS</span>', unsafe_allow_html=True)
            st.write(cas)
        with b:
            st.markdown('<span class="pill">ความเข้มข้นสูงสุด</span>', unsafe_allow_html=True)
            st.write(maxc)
        with c:
            st.markdown('<span class="pill">กรณีที่ใช้</span>', unsafe_allow_html=True)
            st.write(usecase)
        with d:
            st.markdown('<span class="pill">Chemical Name</span>', unsafe_allow_html=True)
            st.write(chem)

        # เฉพาะ allowed: บริเวณที่ใช้
        if src == "วัตถุอาจใช้เป็นส่วนผสม" and area_val != "-":
            st.markdown('<div class="section-title">การนำไปใช้</div>', unsafe_allow_html=True)
            st.write(area_val)

        # เงื่อนไข
        st.markdown('<div class="section-title">เงื่อนไขการใช้งาน</div>', unsafe_allow_html=True)
        st.write(cond)
