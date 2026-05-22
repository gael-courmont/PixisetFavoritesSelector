"""
Pixieset Favorites Selector
----------------------------
Paste favorited filenames from Pixieset, pick your local photo folder,
and copy all matched photos into the export folder.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
from pathlib import Path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Backgrounds ──────────────────────────────────────────────────────────────
BG        = "#edede9"   # main window background
SURFACE   = "#d6ccc2"   # config strip, footer
CARD      = "#f5ebe0"   # header, buttons, input backgrounds
ACCENT    = "#d6ccc2"   # borders, hover, checkbutton highlight
SELECT_BG = "#817F82"   # text selection background
SELECT_FG = "#ffffff"   # text selection foreground

# ── Buttons ──────────────────────────────────────────────────────────────────
BTN_BG        = "#f5ebe0"   # button background
BTN_FG        = "#000000"   # button text
BTN_ACTIVE_BG = "#e3d5ca"   # button background on hover/click
BTN_ACTIVE_FG = "#000000"   # button text on hover/click
BTN_BORDER    = "#d6ccc2"   # button border color (via highlightbackground)
BTN_BORDER_W  = 1           # button border width (0 to disable)

# ── Text colors ──────────────────────────────────────────────────────────────
TEXT      = "#000000"   # primary text (labels, listbox, inputs)
MUTED     = "#666666"   # secondary text (hints, folder paths, subtitles)

# ── Status colors ────────────────────────────────────────────────────────────
SUCCESS   = "#8fbf8f"   # matched files / done
WARNING   = "#c8a96e"   # partial match stats
DANGER    = "#c47f7f"   # missing files
STATUS_FG = "#e3d5ca"   # status label in footer (uses ACCENT by default)

# ── Section label color ───────────────────────────────────────────────────────
LABEL_ACCENT = "#000000"  # "① Paste…", "② Match results", folder labels

# ── Fonts ────────────────────────────────────────────────────────────────────
FONT_HEADER  = ("Segoe UI Semibold", 15)  # app title
FONT_SUBHEAD = ("Segoe UI", 11)            # subtitle under header
FONT_LABEL   = ("Segoe UI Semibold", 14)  # section labels, folder row labels
FONT_BUTTON  = ("Segoe UI", 14)           # all buttons
FONT_HINT    = ("Segoe UI", 11)            # small hint text, stats, checkboxes
FONT_MONO    = ("Consolas", 14)           # paste area, folder paths, listbox

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def normalize(name: str) -> str:
    return Path(name.strip()).stem.lower()



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pixieset Favorites Selector")
        self.geometry("860x780")
        self.minsize(720, 640)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.source_folder = tk.StringVar()
        self.export_folder = tk.StringVar()
        self.filter_raw    = tk.BooleanVar(value=True)
        self.filter_jpeg   = tk.BooleanVar(value=True)
        self._matched: list[tuple[str, str]] = []
        self._missing: list[str] = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg=CARD, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="✦  Pixieset Favorites Selector",
                 font=FONT_HEADER, fg=TEXT, bg=CARD).pack()
        tk.Label(header, text="Match client favorites · Copy to export folder",
                 font=FONT_SUBHEAD, fg=MUTED, bg=CARD).pack()

        # ── Config strip ──
        config = tk.Frame(self, bg=SURFACE, pady=12)
        config.pack(fill="x", padx=18, pady=(12, 0))

        row2 = tk.Frame(config, bg=SURFACE)
        row2.pack(fill="x", pady=(0, 6))
        tk.Label(row2, text="Source folder", font=FONT_LABEL, fg=LABEL_ACCENT,
                 bg=SURFACE, width=14, anchor="w").pack(side="left")
        tk.Label(row2, textvariable=self.source_folder, font=FONT_MONO,
                 fg=MUTED, bg=CARD, relief="flat", anchor="w", padx=8
                 ).pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(row2, text="Browse…", font=FONT_BUTTON,
                  fg=BTN_FG, bg=BTN_BG, relief="flat", cursor="hand2", padx=10,
                  activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG,
                  highlightbackground=BTN_BORDER, highlightthickness=BTN_BORDER_W,
                  command=lambda: self._pick_folder(self.source_folder)
                  ).pack(side="left", padx=(6, 0))



        row3 = tk.Frame(config, bg=SURFACE)
        row3.pack(fill="x")
        tk.Label(row3, text="Export folder", font=FONT_LABEL, fg=LABEL_ACCENT,
                 bg=SURFACE, width=14, anchor="w").pack(side="left")
        tk.Label(row3, textvariable=self.export_folder, font=FONT_MONO,
                 fg=MUTED, bg=CARD, relief="flat", anchor="w", padx=8
                 ).pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(row3, text="Browse…", font=FONT_BUTTON,
                  fg=BTN_FG, bg=BTN_BG, relief="flat", cursor="hand2", padx=10,
                  activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG,
                  highlightbackground=BTN_BORDER, highlightthickness=BTN_BORDER_W,
                  command=lambda: self._pick_folder(self.export_folder)
                  ).pack(side="left", padx=(6, 0))

        # ── Footer ──
        footer = tk.Frame(self, bg=SURFACE, pady=12)
        footer.pack(fill="x", side="bottom")

        self.btn_scan = self._btn(footer, "🔍  Scan & Match", self._run_scan, bg=CARD)
        self.btn_scan.pack(side="left", padx=(18, 8))

        self.btn_copy = self._btn(footer, "📁  Copy to export folder", self._run_copy, bg=ACCENT)
        self.btn_copy.pack(side="left")
        self.btn_copy.configure(state="disabled")

        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=160)
        self.progress.pack(side="right", padx=18)

        self.lbl_status = tk.Label(footer, text="", font=FONT_HINT, fg=STATUS_FG, bg=SURFACE)
        self.lbl_status.pack(side="right", padx=6)

        #body
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=14)
        body.columnconfigure(0, weight=10)  # left column
        body.columnconfigure(1, weight=15)  # right column gets 2x the space
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        # ── Left: paste area ──
        self._section_label(left, "① Paste favorited filenames")
        tk.Label(left, text="Comma-separated from Pixieset, e.g.  photo-01, photo-02, photo-03",
                 font=FONT_HINT, fg=MUTED, bg=BG).pack(anchor="w")


        txt_frame = tk.Frame(left, bg=ACCENT, padx=1, pady=1)
        txt_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.txt_names = tk.Text(
            txt_frame, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            font=FONT_MONO, relief="flat", wrap="word",
            selectbackground=SELECT_BG, selectforeground=SELECT_FG,
            padx=8, pady=8, width=1, undo=True
        )
    
        sb = ttk.Scrollbar(txt_frame, command=self.txt_names.yview)
        self.txt_names.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_names.pack(fill="both", expand=True)

        tk.Button(left, text="✕  Clear", font=FONT_HINT,
                  fg=BTN_FG, bg=BTN_BG, relief="flat", cursor="hand2",
                  activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG,
                  highlightbackground=BTN_BORDER, highlightthickness=BTN_BORDER_W,
                  command=lambda: self.txt_names.delete("1.0", "end")
                  ).pack(anchor="e", pady=(4, 0))

        # ── Extension filter ──
        filter_row = tk.Frame(left, bg=BG)
        filter_row.pack(anchor="w", pady=(8, 0))
        tk.Label(filter_row, text="Include:", font=FONT_HINT,
                 fg=MUTED, bg=BG).pack(side="left", padx=(0, 8))

        for text, var in [("RAW", self.filter_raw), ("JPEG", self.filter_jpeg)]:
            tk.Checkbutton(
                filter_row, text=text, variable=var,
                font=FONT_HINT, fg=TEXT, bg=BG,
                selectcolor=CARD, activebackground=BG,
                activeforeground=TEXT
            ).pack(side="left", padx=(0, 10))

        # ── Right: results ──
        self._section_label(right, "② Match results")
        list_frame = tk.Frame(right, bg=ACCENT, padx=1, pady=1)
        list_frame.pack(fill="both", expand=True)

        inner = tk.Frame(list_frame, bg=SURFACE)
        inner.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            inner, bg=SURFACE, fg=TEXT, font=FONT_MONO,
            relief="flat", selectbackground=CARD,
            activestyle="none", highlightthickness=0, borderwidth=0
        )
        sb2 = ttk.Scrollbar(inner, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)

        self.lbl_stats = tk.Label(right, text="No scan yet.",
                                  font=FONT_HINT, fg=MUTED, bg=BG, anchor="w")
        self.lbl_stats.pack(anchor="w", pady=(4, 0))



        # ── ttk styles ──
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar",
                        background=CARD, troughcolor=SURFACE,
                        arrowcolor=MUTED, bordercolor=SURFACE)
        style.configure("TProgressbar", troughcolor=SURFACE, background=ACCENT)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _section_label(self, parent, text, pady_top=0):
        tk.Label(parent, text=text, font=FONT_LABEL, fg=LABEL_ACCENT, bg=BG
                 ).pack(anchor="w", pady=(pady_top, 2))

    def _btn(self, parent, text, cmd, bg=BTN_BG):
        return tk.Button(parent, text=text, font=FONT_BUTTON,
                         fg=BTN_FG, bg=bg, relief="flat", cursor="hand2",
                         activebackground=BTN_ACTIVE_BG, activeforeground=BTN_ACTIVE_FG,
                         highlightbackground=BTN_BORDER, highlightthickness=BTN_BORDER_W,
                         padx=14, pady=6, command=cmd)

    def _pick_folder(self, var: tk.StringVar):
        path = filedialog.askdirectory(title="Select folder")
        if path:
            var.set(path)

    def _set_status(self, msg, color=STATUS_FG):
        self.lbl_status.configure(text=msg, fg=color)

    def _get_dest_folder(self) -> str | None:
        export = self.export_folder.get().strip()
        if not export or not os.path.isdir(export):
            messagebox.showwarning("No export folder", "Please select a valid export folder.")
            return None
        return export

    def _parse_names(self) -> list[str]:
        raw = self.txt_names.get("1.0", "end")
        # normalize: replace all whitespace (newlines, tabs, spaces around commas)
        # then split cleanly on commas
        import re
        tokens = []
        seen = set()
        for token in re.split(r'[\s,]+', raw):
            token = token.strip()
            if token and token not in seen:
                seen.add(token)
                tokens.append(token)
        return tokens

    # ── Scan ─────────────────────────────────────────────────────────────────

    def _run_scan(self):
        names  = self._parse_names()
        folder = self.source_folder.get()

        if not names:
            messagebox.showwarning("Nothing to search", "Please paste at least one filename.")
            return
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("No source folder", "Please select a valid source photo folder.")
            return

        self.btn_scan.configure(state="disabled")
        self.btn_copy.configure(state="disabled")
        self.progress.start(12)
        self._set_status("Scanning…")
        threading.Thread(target=self._do_scan, args=(names, folder), daemon=True).start()

    RAW_EXTS  = {".cr2", ".cr3", ".nef", ".arw", ".orf", ".raf",
                 ".rw2", ".dng", ".pef", ".srw", ".x3f"}
    JPEG_EXTS = {".jpg", ".jpeg"}

    def _do_scan(self, names: list[str], folder: str):
        allowed: set[str] = set()
        if self.filter_raw.get():
            allowed |= self.RAW_EXTS
        if self.filter_jpeg.get():
            allowed |= self.JPEG_EXTS

        index: dict[str, str] = {}
        for root, _, files in os.walk(folder):
            for f in files:
                if f.startswith("._") or f.startswith("."):
                    continue
                if allowed and Path(f).suffix.lower() not in allowed:
                    continue
                stem = normalize(f)
                full = os.path.join(root, f)
                if stem not in index:
                    index[stem] = full

        matched, missing = [], []
        for name in names:
            key = normalize(name)
            if key in index:
                matched.append((name, index[key]))
            else:
                missing.append(name)

        # pass results directly, don't rely on self state across threads
        self.after(0, lambda: self._show_results(matched, missing))

    def _show_results(self, matched: list, missing: list):
        # only assign to self once we're back on the main thread
        self._matched = matched
        self._missing = missing

        self.progress.stop()
        self.btn_scan.configure(state="normal")
        self.listbox.delete(0, "end")

        for name, path in self._matched:
            ext_found = Path(path).suffix
            ext_req = Path(name).suffix
            note = f"  [{ext_req} → {ext_found}]" if ext_req and ext_req.lower() != ext_found.lower() else ""
            self.listbox.insert("end", f"  ✓  {name}{note}")
            self.listbox.itemconfig("end", fg=SUCCESS)

        for name in self._missing:
            self.listbox.insert("end", f"  ✗  {name}")
            self.listbox.itemconfig("end", fg=DANGER)

        print(self._matched)
        print(self._missing)
        n_match, n_miss = len(self._matched), len(self._missing)
        self.lbl_stats.configure(
            text=f"{n_match + n_miss} requested  ·  {n_match} found  ·  {n_miss} missing",
            fg=SUCCESS if n_miss == 0 else WARNING
        )
        self._set_status("Scan complete.", SUCCESS)

        if self._matched:
            self.btn_copy.configure(state="normal")

    # ── Copy ─────────────────────────────────────────────────────────────────

    def _run_copy(self):
        if not self._matched:
            return

        dest = self._get_dest_folder()
        if dest is None:
            return

        self.btn_copy.configure(state="disabled")
        self.btn_scan.configure(state="disabled")
        self.progress.start(12)
        self._set_status("Copying…")
        threading.Thread(target=self._do_copy, args=(dest,), daemon=True).start()

    def _do_copy(self, dest: str):
        os.makedirs(dest, exist_ok=True)
        errors = []
        for i, (name, src) in enumerate(self._matched):
            try:
                shutil.copy2(src, os.path.join(dest, Path(src).name))
            except Exception as e:
                errors.append(f"{name}: {e}")
            if i % 5 == 0:
                self.after(0, lambda n=i+1: self._set_status(f"Copying {n}/{len(self._matched)}…"))

        self.after(0, lambda: self._copy_done(dest, errors))

    def _copy_done(self, dest: str, errors: list[str]):
        self.progress.stop()
        self.btn_scan.configure(state="normal")
        self.btn_copy.configure(state="normal")

        if errors:
            messagebox.showerror("Some files failed",
                                 f"{len(errors)} file(s) could not be copied:\n\n" + "\n".join(errors[:10]))
            self._set_status(f"Done with {len(errors)} error(s).", WARNING)
        else:
            self._set_status(f"✓ {len(self._matched)} files copied!", SUCCESS)
            messagebox.showinfo("Done!", f"✓ {len(self._matched)} photo(s) copied to:\n\n{dest}")


if __name__ == "__main__":
    App().mainloop()