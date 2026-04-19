"""
Pixieset Favorites Selector
----------------------------
Paste favorited filenames from Pixieset, pick your local photo folder,
and copy all matched photos into a "CLIENTNAME_FavoritesPhotos" subfolder.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
from pathlib import Path


# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#1e1e1e"
SURFACE   = "#2a2a2a"
CARD      = "#333333"
ACCENT    = "#555555"
ACCENT2   = "#aaaaaa"
TEXT      = "#e8e8e8"
MUTED     = "#666666"
SUCCESS   = "#8fbf8f"
WARNING   = "#c8a96e"
DANGER    = "#c47f7f"
FONT_BODY = ("Segoe UI", 10)
FONT_HEAD = ("Segoe UI Semibold", 11)
FONT_MONO = ("Consolas", 9)


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
        self.client_name = tk.StringVar()
        self.filter_raw = tk.BooleanVar(value=True)
        self.filter_jpeg = tk.BooleanVar(value=True)
        self._matched: list[tuple[str, str]] = []
        self._missing: list[str] = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg=CARD, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="✦  Pixieset Favorites Selector",
                 font=("Segoe UI Semibold", 15), fg=TEXT, bg=CARD).pack()
        tk.Label(header, text="Match client favorites · Copy to export folder",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD).pack()

        # ── Config strip (client name + folders) ──
        config = tk.Frame(self, bg=SURFACE, pady=12)
        config.pack(fill="x", padx=18, pady=(12, 0))

        # Client name
        row1 = tk.Frame(config, bg=SURFACE)
        row1.pack(fill="x", pady=(0, 8))
        tk.Label(row1, text="Client name", font=FONT_HEAD, fg=ACCENT2,
                 bg=SURFACE, width=14, anchor="w").pack(side="left")
        tk.Entry(row1, textvariable=self.client_name, font=FONT_MONO,
                 bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat",
                 highlightthickness=1, highlightbackground=MUTED,
                 highlightcolor=ACCENT).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))

        # Preview label
        self.lbl_preview = tk.Label(row1, text="", font=("Segoe UI", 9),
                                    fg=MUTED, bg=SURFACE)
        self.lbl_preview.pack(side="left")
        self.client_name.trace_add("write", self._update_preview)

        # Source folder
        row2 = tk.Frame(config, bg=SURFACE)
        row2.pack(fill="x", pady=(0, 6))
        tk.Label(row2, text="Source folder", font=FONT_HEAD, fg=ACCENT2,
                 bg=SURFACE, width=14, anchor="w").pack(side="left")
        tk.Label(row2, textvariable=self.source_folder, font=FONT_MONO,
                 fg=MUTED, bg=CARD, relief="flat", anchor="w", padx=8
                 ).pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(row2, text="Browse…", font=FONT_BODY, fg=TEXT, bg=CARD,
                  relief="flat", cursor="hand2", padx=10,
                  activebackground=ACCENT, activeforeground=TEXT,
                  command=lambda: self._pick_folder(self.source_folder)
                  ).pack(side="left", padx=(6, 0))

        # Export folder
        row3 = tk.Frame(config, bg=SURFACE)
        row3.pack(fill="x")
        tk.Label(row3, text="Export folder", font=FONT_HEAD, fg=ACCENT2,
                 bg=SURFACE, width=14, anchor="w").pack(side="left")
        tk.Label(row3, textvariable=self.export_folder, font=FONT_MONO,
                 fg=MUTED, bg=CARD, relief="flat", anchor="w", padx=8
                 ).pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(row3, text="Browse…", font=FONT_BODY, fg=TEXT, bg=CARD,
                  relief="flat", cursor="hand2", padx=10,
                  activebackground=ACCENT, activeforeground=TEXT,
                  command=lambda: self._pick_folder(self.export_folder)
                  ).pack(side="left", padx=(6, 0))

        # ── Body ──
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=14)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(body, bg=BG)
        right.pack(side="right", fill="both", expand=True)

        # ── Left: paste area ──
        self._section_label(left, "① Paste favorited filenames")
        tk.Label(left, text="Comma-separated from Pixieset, e.g.  photo-01, photo-02, photo-03",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(anchor="w")

        txt_frame = tk.Frame(left, bg=ACCENT, padx=1, pady=1)
        txt_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.txt_names = tk.Text(
            txt_frame, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            font=FONT_MONO, relief="flat", wrap="none",
            selectbackground=ACCENT, selectforeground=TEXT,
            padx=8, pady=8
        )
        sb = ttk.Scrollbar(txt_frame, command=self.txt_names.yview)
        self.txt_names.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_names.pack(fill="both", expand=True)

        tk.Button(left, text="✕  Clear", font=("Segoe UI", 9), fg=MUTED,
                  bg=SURFACE, relief="flat", cursor="hand2",
                  activebackground=CARD, activeforeground=TEXT,
                  command=lambda: self.txt_names.delete("1.0", "end")
                  ).pack(anchor="e", pady=(4, 0))

        # ── Extension filter ──
        filter_row = tk.Frame(left, bg=BG)
        filter_row.pack(anchor="w", pady=(8, 0))
        tk.Label(filter_row, text="Include:", font=("Segoe UI", 9),
                 fg=MUTED, bg=BG).pack(side="left", padx=(0, 8))

        for text, var in [("RAW", self.filter_raw), ("JPEG", self.filter_jpeg)]:
            tk.Checkbutton(
                filter_row, text=text, variable=var,
                font=("Segoe UI", 9), fg=TEXT, bg=BG,
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
                                  font=("Segoe UI", 9), fg=MUTED, bg=BG, anchor="w")
        self.lbl_stats.pack(anchor="w", pady=(4, 0))

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

        self.lbl_status = tk.Label(footer, text="", font=("Segoe UI", 9), fg=ACCENT2, bg=SURFACE)
        self.lbl_status.pack(side="right", padx=6)

        # ── ttk styles ──
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar",
                        background=CARD, troughcolor=SURFACE,
                        arrowcolor=MUTED, bordercolor=SURFACE)
        style.configure("TProgressbar", troughcolor=SURFACE, background=ACCENT)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _section_label(self, parent, text, pady_top=0):
        tk.Label(parent, text=text, font=FONT_HEAD, fg=ACCENT2, bg=BG
                 ).pack(anchor="w", pady=(pady_top, 2))

    def _btn(self, parent, text, cmd, bg=CARD):
        return tk.Button(parent, text=text, font=FONT_BODY,
                         fg=TEXT, bg=bg, relief="flat", cursor="hand2",
                         activebackground=ACCENT, activeforeground=TEXT,
                         padx=14, pady=6, command=cmd)

    def _pick_folder(self, var: tk.StringVar):
        path = filedialog.askdirectory(title="Select folder")
        if path:
            var.set(path)

    def _set_status(self, msg, color=ACCENT2):
        self.lbl_status.configure(text=msg, fg=color)

    def _update_preview(self, *_):
        name = self.client_name.get().strip()
        if name:
            folder_name = f"{name}_FavoritesPhotos"
            self.lbl_preview.configure(text=f"→ {folder_name}", fg=ACCENT2)
        else:
            self.lbl_preview.configure(text="")

    def _get_dest_folder(self) -> str | None:
        """Build and return the destination path, or None if inputs are invalid."""
        client = self.client_name.get().strip()
        export = self.export_folder.get().strip()

        if not client:
            messagebox.showwarning("Missing client name", "Please enter a client name.")
            return None
        if not export or not os.path.isdir(export):
            messagebox.showwarning("No export folder", "Please select a valid export folder.")
            return None

        folder_name = f"{client}_FavoritesPhotos"
        return os.path.join(export, folder_name)

    def _parse_names(self) -> list[str]:
        raw = self.txt_names.get("1.0", "end").strip()
        tokens = []
        for chunk in raw.replace("\n", ",").split(","):
            token = chunk.strip()
            if token:
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

    RAW_EXTS = {".cr2", ".cr3", ".nef", ".arw", ".orf", ".raf",
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

        self._matched = matched
        self._missing = missing
        self.after(0, self._show_results)

    def _show_results(self):
        self.progress.stop()
        self.btn_scan.configure(state="normal")
        self.listbox.delete(0, "end")

        for name, path in self._matched:
            ext_found = Path(path).suffix
            ext_req   = Path(name).suffix
            note = f"  [{ext_req} → {ext_found}]" if ext_req and ext_req.lower() != ext_found.lower() else ""
            self.listbox.insert("end", f"  ✓  {name}{note}")
            self.listbox.itemconfig("end", fg=SUCCESS)

        for name in self._missing:
            self.listbox.insert("end", f"  ✗  {name}")
            self.listbox.itemconfig("end", fg=DANGER)

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

        if os.path.isdir(dest):
            if not messagebox.askyesno(
                "Folder exists",
                f"'{os.path.basename(dest)}' already exists in the export folder.\n"
                "Existing files may be overwritten. Continue?"
            ):
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