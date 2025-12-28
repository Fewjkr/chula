import pandas as pd
import streamlit as st

APP_TITLE = "Specified Allowable Concentration Search System for Cosmetic Preservatives and Ingredients"

# ---- Column names (หลัก ๆ ตามไฟล์เดิม) ----
COL_COMMON = "Name of Common Ingredients Glossary"
COL_CAS = "CAS Number"
COL_CHEM = "Chemical Name/ Other Name"
COL_MAXC = "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)"
COL_USECASE = "กรณีที่ใช้"
COL_COND = "เงื่อนไข"
COL_ORDER = "ลำดับ"

# ---- allowed.csv (ไฟล์ใหม่) อาจมีคอลัมน์ "บริเวณที่ใช้" / ชื่ออื่นคล้าย ๆ ----
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
    """คืนชื่อคอลัมน์ตัวแรกที่เจอใน df จาก candidates"""
    for c in candidates:
        if c in df.columns:
            return c
    return None

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    # รองรับ encoding ที่เจอบ่อยกับไฟล์ไทย
    last_err = None
    for enc in ["utf-8-sig", "utf-8", "cp874", "tis-620"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_err = e
    # fallback
    try:
        return pd.read_csv(path)
    except Exception:
        raise last_err

def build_title(common: str, cas: str) -> str:
    # หัวการ์ด: Common • CAS (ไม่ใส่แหล่งข้อมูลในบรรทัดนี้เพื่อกันยาวเกิน)
    c1 = common if common != "-" else ""
    c2 = cas if cas != "-" else ""
    if c1 and c2:
        return f"{c1} • {c2}"
    return c1 or c2 or "-"

# -------------------- Page config --------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")

# -------------------- CSS (Light + modern cards) --------------------
st.markdown(
    """
<style>
/* ===== Page ===== */
.stApp { background: #f8fafc !important; }
html, body, [class*="css"] {
  font-family: "Segoe UI", "Noto Sans Thai", "Noto Sans", sans-serif !important;
}

/* Force readable text on light bg */
.stApp, .stApp * { color: #0f172a !important; }
.stCaption, .stCaption * { color: #334155 !important; opacity: 1 !important; }

h1, h2, h3, h4, h5, h6 { color: #0f172a !important; }

/* Inputs */
input, textarea {
  background: #ffffff !important;
  color: #0f172a !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 12px !important;
}
div[data-baseweb="select"] > div{
  background: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 12px !important;
}
div[data-baseweb="select"] span{ color: #0f172a !important; }
label { font-weight: 700 !important; }

/* Divider */
hr { border-color: #e2e8f0 !important; }

/* Container cards (st.container(border=True)) */
div[data-testid="stContainer"]{
  background: #ffffff !important;
  border: 1px solid #bfdbfe !important;
  border-left: 6px solid #2563eb !important;
  border-radius: 16px !important;
  padding: 18px !important;
  margin-bottom: 16px !important;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06) !important;
}

/* Card title/subtitle with ellipsis */
.card-title{
  font-size: 24px !important;
  font-weight: 800 !important;
  line-height: 1.2 !important;
  margin: 0 0 6px 0 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.card-subtitle{
  font-size: 13px !important;
  color: #334155 !important;
  opacity: 1 !important;
  margin: 0 0 12px 0 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Small label pills */
.pill{
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8 !important;
  margin-right: 8px;
}

/* Section titles in card */
.section-title{
  font-size: 14px;
  font-weight: 800;
  margin: 10px 0 6px 0;
  color: #0f172a !important;
}

/* Main content spacing */
.block-container { padding-top: 1.2rem !important; }

/* Make columns more compact on wide */
@media (min-width: 1200px){
  .block-container { max-width: 1250px; }
}
</style>
""",
    unsafe_allow_html=True,
)

# -------------------- Header --------------------
st.markdown(f"## {APP_TITLE}")
st.caption("ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสีย และวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง")

# -------------------- Load data --------------------
try:
    df_pres = load_csv("preservatives.csv")
except Exception:
    df_pres = None

try:
    df_allow = load_csv("allowed.csv")
except Exception:
    df_allow = None

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

# -------------------- Filter realtime --------------------
df_f = df.copy()
qq = (q or "").strip()
if qq:
    ql = qq.lower()
    mask = False

    # common + cas เท่านั้น (ตามที่ต้องการ)
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
    st.caption("แสดงแบบ Block ครบทุกข้อมูล ไม่ต้องกดดูรายละเอียด")

if len(df_f) == 0:
    st.info("ไม่พบข้อมูล")
    st.stop()

start = (page - 1) * show_per_page
end = min(start + show_per_page, len(df_f))

st.divider()

# -------------------- Render cards --------------------
# ใช้หัวข้อ "บริเวณที่ใช้" เฉพาะตอน dataset = allowed หรือ รวมทั้งหมดแต่แถวที่มาจาก allowed
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

    # เฉพาะ allowed เท่านั้น
    area_val = "-"
    if src == "วัตถุอาจใช้เป็นส่วนผสม" and area_col is not None:
        area_val = clean_val(row.get(area_col, "-"))

    title = build_title(common, cas)

    with st.container(border=True):
        # title + subtitle (ไม่ให้ยาวจนเพี้ยน)
        st.markdown(f'<div class="card-title">{title}</div>', unsafe_allow_html=True)

        subtitle_parts = []
        if src != "-":
            subtitle_parts.append(src)
        if order != "-":
            subtitle_parts.append(f"ลำดับ: {order}")
        subtitle = " • ".join(subtitle_parts) if subtitle_parts else ""
        if subtitle:
            st.markdown(f'<div class="card-subtitle">{subtitle}</div>', unsafe_allow_html=True)

        # Summary row
        a, b, c = st.columns([1.2, 1.2, 2.4])
        with a:
            st.markdown('<span class="pill">ความเข้มข้นสูงสุด</span>', unsafe_allow_html=True)
            st.write(maxc)
        with b:
            st.markdown('<span class="pill">กรณีที่ใช้</span>', unsafe_allow_html=True)
            st.write(usecase)
        with c:
            st.markdown('<span class="pill">Chemical Name</span>', unsafe_allow_html=True)
            st.write(chem)

        # (เพิ่มเฉพาะ allowed) บริเวณที่ใช้
        if src == "วัตถุอาจใช้เป็นส่วนผสม" and area_val != "-":
            st.markdown('<div class="section-title">บริเวณที่ใช้</div>', unsafe_allow_html=True)
            st.write(area_val)

        st.markdown('<div class="section-title">เงื่อนไขการใช้งาน</div>', unsafe_allow_html=True)
        st.write(cond)
