import csv
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

APP_TITLE = "Specified Allowable Concentration Search System"

# Dataset dropdown
DATASETS = [
    ("ทั้งหมด (2 ไฟล์)", None),
    ("วัตถุกันเสีย", "preservatives.csv"),
    ("วัตถุอาจใช้เป็นส่วนผสม", "allowed.csv"),
]

DISPLAY_COLUMNS = [
    "ลำดับ",
    "Chemical Name/ Other Name",
    "Name of Common Ingredients Glossary",
    "CAS Number",
    "กรณีที่ใช้",
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)",
    "เงื่อนไข",
]

# Search only these columns
SEARCH_COLUMNS = [
    "Name of Common Ingredients Glossary",
    "CAS Number",
]

MAX_SHOW = 600

# Truncate long text in table for readability
TRUNCATE_LIMIT = {
    "Chemical Name/ Other Name": 52,
    "Name of Common Ingredients Glossary": 42,
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)": 48,
    "เงื่อนไข": 80,
}

# Column widths (table side)
COLUMN_WIDTH = {
    "ลำดับ": 60,
    "Chemical Name/ Other Name": 310,
    "Name of Common Ingredients Glossary": 250,
    "CAS Number": 140,
    "กรณีที่ใช้": 140,
    "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)": 340,
    "เงื่อนไข": 520,
}

PLACEHOLDER = "พิมพ์ชื่อสามัญ (Common) หรือ CAS เช่น 101-20-2 …"


def normalize(s):
    return (s or "").strip().lower()


def truncate_text(s, limit):
    s = "" if s is None else str(s)
    s = " ".join(s.split())
    if limit and len(s) > limit:
        return s[: max(0, limit - 1)] + "…"
    return s


def read_csv_as_dicts(path):
    for enc in ("utf-8-sig", "utf-8", "cp874"):
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                headers = reader.fieldnames or []
            return headers, rows
        except UnicodeDecodeError:
            continue
    raise RuntimeError("อ่านไฟล์ไม่ได้: %s" % path)


def contains_match(row, query, cols):
    q = normalize(query)
    if not q:
        return True
    for c in cols:
        if q in normalize(str(row.get(c, ""))):
            return True
    return False


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        # base dir (where app.py is)
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        # --- Modern-ish styling ---
        self.title(APP_TITLE)
        self.geometry("1400x820")
        self.minsize(1100, 680)

        bg = "#F6F7FB"
        card_bg = "#FFFFFF"
        muted = "#5B5F6A"

        self.configure(bg=bg)
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("TFrame", background=bg)
        self.style.configure("Card.TFrame", background=card_bg)
        self.style.configure("TLabel", background=bg)
        self.style.configure("Muted.TLabel", foreground=muted, background=bg)
        self.style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), background=bg)
        self.style.configure("H2.TLabel", font=("Segoe UI", 11, "bold"), background=bg)
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))
        self.style.configure("TButton", padding=(12, 7))

        # --- Data ---
        self.headers_by_ds = []
        self.rows_by_ds = []
        self.last_shown_rows = []
        self.current_display_cols = []

        # --- Header (with FDA image) ---
        header = ttk.Frame(self, padding=(16, 14))
        header.pack(fill="x")

        header_row = ttk.Frame(header)
        header_row.pack(fill="x")

        # Load FDA image (Python 2.7 safest: GIF)
        # Put "fda.gif" in same folder as app.py
        self.fda_img = None
        img_candidates = ["fda.gif", "fda.GIF", "fda"]  # allow no extension too
        for name in img_candidates:
            p = os.path.join(self.base_dir, name)
            if os.path.exists(p):
                try:
                    self.fda_img = tk.PhotoImage(file=p)
                    # resize if too big (increase numbers to make smaller)
                    self.fda_img = self.fda_img.subsample(2, 2)
                    ttk.Label(header_row, image=self.fda_img).pack(side="left", padx=(0, 12))
                    break
                except Exception:
                    self.fda_img = None

        title_col = ttk.Frame(header_row)
        title_col.pack(side="left", fill="x", expand=True)

        ttk.Label(
            title_col, text="Specified Allowable Concentration Search System", style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            title_col,
            text="ระบบค้นหาปริมาณที่กำหนดให้ใช้ได้สำหรับสารกันเสีย และวัตถุที่อาจใช้เป็นส่วนผสมในการผลิตเครื่องสำอาง",
            style="Muted.TLabel",
            wraplength=1250,
        ).pack(anchor="w", pady=(4, 0))

        # --- Controls Card ---
        controls = ttk.Frame(self, style="Card.TFrame", padding=14)
        controls.pack(fill="x", padx=16, pady=(0, 12))
        controls.columnconfigure(2, weight=1)

        ttk.Label(controls, text="ชุดข้อมูล", style="H2.TLabel").grid(row=0, column=0, sticky="w")
        self.ds_var = tk.StringVar(value=DATASETS[0][0])
        self.ds_combo = ttk.Combobox(
            controls,
            textvariable=self.ds_var,
            values=[d[0] for d in DATASETS],
            state="readonly",
            width=26,
        )
        self.ds_combo.grid(row=0, column=1, sticky="w", padx=(10, 18))
        self.ds_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())

        ttk.Label(controls, text="ค้นหา", style="H2.TLabel").grid(row=0, column=2, sticky="w")

        self.q_var = tk.StringVar()
        self.q_entry = ttk.Entry(controls, textvariable=self.q_var)
        self.q_entry.grid(row=0, column=2, sticky="ew", padx=(60, 12))

        # Placeholder + realtime search
        self._placeholder_active = True
        self.q_entry.insert(0, PLACEHOLDER)
        self.q_entry.configure(foreground=muted)
        self.q_entry.bind("<FocusIn>", self._on_focus_in)
        self.q_entry.bind("<FocusOut>", self._on_focus_out)
        self.q_entry.bind("<KeyRelease>", lambda e: self.apply_filter_realtime())

        ttk.Button(controls, text="ล้าง", command=self.clear_search).grid(row=0, column=3, sticky="e")

        self.status = ttk.Label(self, text="กำลังโหลดไฟล์...", style="Muted.TLabel")
        self.status.pack(fill="x", padx=18)

        # --- Main splitter (left table / right detail) ---
        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # LEFT: table card (wider)
        table_card = ttk.Frame(main, style="Card.TFrame", padding=10)
        table_card.rowconfigure(1, weight=1)
        table_card.columnconfigure(0, weight=1)

        ttk.Label(table_card, text="ผลการค้นหา", style="H2.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.tree = ttk.Treeview(table_card, show="headings")
        yscroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        yscroll.grid(row=1, column=1, sticky="ns")
        xscroll.grid(row=2, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_detail())

        # RIGHT: detail card (narrower)
        detail_card = ttk.Frame(main, style="Card.TFrame", padding=12)
        detail_card.columnconfigure(1, weight=1)
        detail_card.rowconfigure(8, weight=1)

        ttk.Label(detail_card, text="รายละเอียด", style="H2.TLabel").grid(row=0, column=0, sticky="w", columnspan=2)

        self._fields = [
            ("แหล่งข้อมูล", "_source"),
            ("ลำดับ", "ลำดับ"),
            ("Common", "Name of Common Ingredients Glossary"),
            ("CAS", "CAS Number"),
            ("กรณีที่ใช้", "กรณีที่ใช้"),
            ("Chemical", "Chemical Name/ Other Name"),
            ("ความเข้มข้นสูงสุด", "ความเข้มข้นสูงสุดในเครื่องสำอางพร้อมใช้ (%w/w)"),
        ]

        self.value_vars = {}
        r = 1
        for label, key in self._fields:
            ttk.Label(detail_card, text=label, style="Muted.TLabel").grid(
                row=r, column=0, sticky="nw", pady=4, padx=(0, 10)
            )
            var = tk.StringVar(value="-")
            self.value_vars[key] = var
            ttk.Label(detail_card, textvariable=var, wraplength=420, justify="left").grid(
                row=r, column=1, sticky="nw", pady=4
            )
            r += 1

        ttk.Label(detail_card, text="เงื่อนไข", style="Muted.TLabel").grid(
            row=r, column=0, sticky="nw", pady=(10, 4), padx=(0, 10)
        )
        self.condition_text = tk.Text(detail_card, height=10, wrap="word", relief="solid", bd=1)
        self.condition_text.grid(row=r, column=1, sticky="nsew", pady=(10, 4))
        self.condition_text.configure(state="disabled")

        # add panes with weights (left bigger than right)
        main.add(table_card, weight=4)
        main.add(detail_card, weight=2)

        # start with right pane narrower (optional)
        try:
            self.after(80, lambda: main.sashpos(0, 980))
        except Exception:
            pass

        # --- Load data ---
        self.load_all()
        self.q_entry.focus_set()

    # ---------- Placeholder ----------
    def _on_focus_in(self, _e):
        if self._placeholder_active:
            self.q_entry.delete(0, "end")
            self.q_entry.configure(foreground="#111111")
            self._placeholder_active = False

    def _on_focus_out(self, _e):
        if not self.q_var.get().strip():
            self._placeholder_active = True
            self.q_entry.delete(0, "end")
            self.q_entry.insert(0, PLACEHOLDER)
            self.q_entry.configure(foreground="#5B5F6A")

    def clear_search(self):
        self.q_var.set("")
        self._placeholder_active = True
        self.q_entry.delete(0, "end")
        self.q_entry.insert(0, PLACEHOLDER)
        self.q_entry.configure(foreground="#5B5F6A")
        self.apply_filter()

    def get_query(self):
        if self._placeholder_active:
            return ""
        return self.q_var.get()

    # ---------- Data ----------
    def load_all(self):
        self.headers_by_ds = []
        self.rows_by_ds = []

        # load real files (index 1,2 in DATASETS)
        for name, fname in DATASETS[1:]:
            path = os.path.join(self.base_dir, fname)
            try:
                headers, rows = read_csv_as_dicts(path)
            except Exception as e:
                messagebox.showerror("Error", str(e))
                headers, rows = [], []
            self.headers_by_ds.append(headers)
            self.rows_by_ds.append(rows)

        self.apply_filter()

    def resolve_columns(self, headers):
        display = [c for c in DISPLAY_COLUMNS if c in headers]
        search = [c for c in SEARCH_COLUMNS if c in headers]
        if not search:
            search = display
        return display, search

    def setup_columns(self, cols):
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            w = COLUMN_WIDTH.get(c, 200)
            self.tree.column(c, width=w, stretch=True)

    def get_selected_indices(self):
        sel = self.ds_var.get()
        if sel == "ทั้งหมด (2 ไฟล์)":
            return [0, 1]
        if sel == "วัตถุกันเสีย":
            return [0]
        return [1]

    # ---------- Realtime apply (debounce) ----------
    def apply_filter_realtime(self):
        if hasattr(self, "_after_id") and self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.after(120, self.apply_filter)

    # ---------- Filter ----------
    def apply_filter(self):
        q = self.get_query()
        idx_list = self.get_selected_indices()

        # union headers
        union_headers = []
        for idx in idx_list:
            for h in self.headers_by_ds[idx]:
                if h not in union_headers:
                    union_headers.append(h)

        display_cols, _ = self.resolve_columns(union_headers)
        self.current_display_cols = display_cols
        self.setup_columns(display_cols)

        raw_rows = []
        total_rows = 0
        total_match = 0

        for idx in idx_list:
            headers = self.headers_by_ds[idx]
            rows = self.rows_by_ds[idx]
            total_rows += len(rows)

            _, search_cols = self.resolve_columns(headers)
            filtered = [r for r in rows if contains_match(r, q, search_cols)]
            total_match += len(filtered)

            source_label = "วัตถุกันเสีย" if idx == 0 else "วัตถุอาจใช้เป็นส่วนผสม"
            for r in filtered:
                r2 = dict(r)
                r2["_source"] = source_label
                raw_rows.append(r2)

        self.last_shown_rows = raw_rows[:MAX_SHOW]

        self.tree.delete(*self.tree.get_children())
        for r in self.last_shown_rows:
            vals = []
            for c in self.current_display_cols:
                limit = TRUNCATE_LIMIT.get(c)
                vals.append(truncate_text(r.get(c, ""), limit))
            self.tree.insert("", "end", values=vals)

        if normalize(q):
            self.status.config(text="พบ %s แถว (แสดง %s)" % (total_match, len(self.last_shown_rows)))
        else:
            self.status.config(text="โหลดแล้ว %s แถว — พิมพ์ Common หรือ CAS เพื่อค้นหา" % total_rows)

        self._clear_detail()

    # ---------- Detail ----------
    def _clear_detail(self):
        for var in self.value_vars.values():
            var.set("-")
        self.condition_text.configure(state="normal")
        self.condition_text.delete("1.0", "end")
        self.condition_text.insert("1.0", "-")
        self.condition_text.configure(state="disabled")

    def get_selected_row(self):
        sel = self.tree.selection()
        if not sel:
            return None
        i = self.tree.index(sel[0])
        if 0 <= i < len(self.last_shown_rows):
            return self.last_shown_rows[i]
        return None

    def show_detail(self):
        row = self.get_selected_row()
        if not row:
            return

        for _, key in self._fields:
            v = row.get(key, "")
            self.value_vars[key].set(v if str(v).strip() else "-")

        cond = row.get("เงื่อนไข", "")
        self.condition_text.configure(state="normal")
        self.condition_text.delete("1.0", "end")
        self.condition_text.insert("1.0", cond if str(cond).strip() else "-")
        self.condition_text.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()
