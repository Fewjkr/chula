import pandas as pd
import streamlit as st
import time

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

# ตัดข้อความใน "ตาราง" ให้พอดีช่อง (แต่รายละเอียดแสดงเต็ม)
TRUNC_LIMIT = {
    "Chemical Name/ Other Name": 55,
    "Name of Common Ingredients Glossary": 40,
    "กรณีที่ใช้": 35,
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)": 55,
    "เงื่อนไข": 70,
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

def normalize_str_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().str.strip()

# ---------------- UI ----------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสีย และวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง")

# โหลดข้อมูล
df_pres = load_csv("preservatives.csv")
df_allow = load_csv("allowed.csv")
df_pres["แหล่งข้อมูล"] = "วัตถุกันเสีย"
df_allow["แหล่งข้อมูล"] = "วัตถุอาจใช้เป็นส่วนผสม"

# -------- Controls --------
c1, c2 = st.columns([1.2, 2.8])
with c1:
    dataset = st.selectbox("ชุดข้อมูล", ["ทั้งหมด (2 ไฟล์)", "วัตถุกันเสีย", "วัตถุอาจใช้เป็นส่วนผสม"])
with c2:
    q = st.text_input("ค้นหา (Common หรือ CAS)", placeholder="เช่น Piroctone olamine หรือ 101-20-2", key="q")

# debounce เล็กน้อยกัน rerun กระตุก (ทำงานฝั่ง client ไม่ได้ 100% แต่ช่วย UX)
if "last_typing" not in st.session_state:
    st.session_state.last_typing = 0.0

st.session_state.last_typing = time.time()
time.sleep(0.10)

# เลือก dataset
if dataset == "วัตถุกันเสีย":
    df = df_pres.copy()
elif dataset == "วัตถุอาจใช้เป็นส่วนผสม":
    df = df_allow.copy()
else:
    df = pd.concat([df_pres, df_allow], ignore_index=True)

cols = safe_cols(df, DISPLAY_COLUMNS)
show_cols = ["แหล่งข้อมูล"] + cols

# -------- Filter --------
df_f = df.copy()
qq = q.strip()
if qq:
    ql = qq.lower()
    mask = False
    if SEARCH_COMMON in df_f.columns:
        mask = mask | normalize_str_series(df_f[SEARCH_COMMON]).str.contains(ql, na=False)
    if SEARCH_CAS in df_f.columns:
        mask = mask | normalize_str_series(df_f[SEARCH_CAS]).str.contains(ql, na=False)
    df_f = df_f[mask].copy()

df_f = df_f.reset_index(drop=True)

st.write(f"พบ {len(df_f):,} แถว")

# -------- Layout --------
left, right = st.columns([3.6, 1.4])

with left:
    st.subheader("ผลการค้นหา")

    if len(df_f) == 0:
        st.info("ไม่พบข้อมูล")
        st.stop()

    # สร้างตารางสำหรับแสดง (ตัดคำ)
    df_view = df_f[show_cols].copy()
    for col, lim in TRUNC_LIMIT.items():
        if col in df_view.columns:
            df_view[col] = df_view[col].apply(lambda x: trunc(x, lim))

    # เพิ่มคอลัมน์เลือกแถว
    if "เลือก" not in st.session_state:
        st.session_state["เลือก"] = 0

    # data_editor ให้เลือก row ได้ผ่าน radio column
    df_show = df_view.copy()
    df_show.insert(0, "เลือก", False)

    # ให้ row ที่เคยเลือกเป็น True
    sel = st.session_state.get("selected_row", 0)
    sel = min(max(int(sel), 0), len(df_show) - 1)
    df_show.loc[:, "เลือก"] = False
    df_show.loc[sel, "เลือก"] = True

    edited = st.data_editor(
        df_show,
        use_container_width=True,
        height=640,
        hide_index=True,
        disabled=[c for c in df_show.columns if c != "เลือก"],
        column_config={"เลือก": st.column_config.CheckboxColumn(width="small")},
    )

    # หาแถวที่ถูกติ๊ก
    checked_idx = edited.index[edited["เลือก"] == True].tolist()
    if checked_idx:
        st.session_state["selected_row"] = int(checked_idx[0])

with right:
    st.subheader("รายละเอียด")
    idx = int(st.session_state.get("selected_row", 0))
    idx = min(max(idx, 0), len(df_f) - 1)

    row = df_f.iloc[idx]

    def show_kv(label, key):
        val = row.get(key, "-")
        if pd.isna(val) or str(val).strip() == "":
            val = "-"
        st.markdown(f"**{label}**")
        st.write(val)

    st.markdown("### ข้อมูลหลัก")
    show_kv("แหล่งข้อมูล", "แหล่งข้อมูล")
    show_kv("ลำดับ", "ลำดับ")
    show_kv("Common", SEARCH_COMMON)
    show_kv("CAS", SEARCH_CAS)
    show_kv("กรณีที่ใช้", "กรณีที่ใช้")

    st.markdown("---")
    st.markdown("### รายละเอียดสาร")
    show_kv("Chemical Name/Other Name", "Chemical Name/ Other Name")
    show_kv("ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)", "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)")

    st.markdown("---")
    st.markdown("### เงื่อนไข")
    cond = row.get("เงื่อนไข", "-")
    if pd.isna(cond) or str(cond).strip() == "":
        cond = "-"
    st.text_area("", value=str(cond), height=240)
