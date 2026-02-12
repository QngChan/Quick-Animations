"""
QuickAnimations - SVG to Manim Animation Tool
Modern dark-themed GUI with built-in dependency installer.
Downloads Python embeddable + creates venv + installs Manim automatically.
"""

import sys
import os
import tempfile
import subprocess
import threading
import urllib.request
import zipfile
import shutil
import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path


# ─── Color Palette ────────────────────────────────────────────────────────────
C = {
    "bg":           "#0f0f13",
    "surface":      "#1a1a24",
    "surface2":     "#22222f",
    "surface3":     "#2a2a3a",
    "border":       "#333346",
    "border_hover": "#5555aa",
    "accent":       "#7c5cfc",
    "accent_hover": "#9b80ff",
    "accent_press": "#6344e0",
    "success":      "#3dd68c",
    "error":        "#ff5c6c",
    "warning":      "#ffb84d",
    "text":         "#e8e8f0",
    "text_dim":     "#8888a0",
    "text_muted":   "#55556a",
}

# ─── Paths ────────────────────────────────────────────────────────────────────
APP_DIR = os.path.join(os.path.expanduser("~"), ".quickanimations")
VENV_DIR = os.path.join(APP_DIR, "venv")
PYTHON_EMBED_DIR = os.path.join(APP_DIR, "python")
PYTHON_EXE = os.path.join(VENV_DIR, "Scripts", "python.exe")
PIP_EXE = os.path.join(VENV_DIR, "Scripts", "pip.exe")
SETUP_MARKER = os.path.join(APP_DIR, "setup_complete.json")

PYTHON_VERSION = "3.11.9"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


# ─── Dependency Checker ──────────────────────────────────────────────────────
def is_setup_complete():
    """Check if the environment is fully configured. Loads custom paths from marker."""
    global PYTHON_EXE
    if not os.path.isfile(SETUP_MARKER):
        return False

    # Load saved python path from marker
    try:
        with open(SETUP_MARKER, "r", encoding="utf-8") as f:
            marker = json.load(f)
        saved_exe = marker.get("python_exe", PYTHON_EXE)
        if os.path.isfile(saved_exe):
            PYTHON_EXE = saved_exe
    except Exception:
        pass

    if not os.path.isfile(PYTHON_EXE):
        return False

    # Quick check: can we import manim?
    try:
        result = subprocess.run(
            [PYTHON_EXE, "-c", "import manim; print('ok')"],
            capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.stdout.strip() == "ok"
    except Exception:
        return False


def find_system_python():
    """Find a working system Python 3.8+ to bootstrap the venv."""
    candidates = [
        shutil.which("python"),
        shutil.which("python3"),
        shutil.which("py"),
    ]
    # Also check common install locations
    for ver in ["311", "312", "310", "39", "313"]:
        candidates.append(os.path.join(
            os.environ.get("LOCALAPPDATA", ""), f"Programs\\Python\\Python{ver}\\python.exe"
        ))
        candidates.append(os.path.join(f"C:\\Python{ver}\\python.exe"))

    for path in candidates:
        if path and os.path.isfile(path):
            try:
                result = subprocess.run(
                    [path, "--version"], capture_output=True, text=True, timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                ver_str = result.stdout.strip()
                if "Python 3." in ver_str:
                    # Extract minor version
                    parts = ver_str.split(".")
                    if len(parts) >= 2:
                        minor = int(parts[1])
                        if minor >= 8:
                            return path
            except Exception:
                continue
    return None


# ─── Rounded Rectangle Helper ────────────────────────────────────────────────
def round_rect(canvas, x1, y1, x2, y2, radius=16, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y2 - radius,
        x2, y2, x2 - radius, y2,
        x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y1 + radius,
        x1, y1, x1 + radius, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ─── Modern Button ───────────────────────────────────────────────────────────
class ModernButton(tk.Canvas):
    def __init__(self, parent, text="", icon="", command=None,
                 width=200, height=44, bg=None, fg=None, hover_bg=None,
                 font_size=11, corner_radius=10, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0, **kwargs)
        self.command = command
        self.w = width
        self.h = height
        self.radius = corner_radius
        self.bg_color = bg or C["accent"]
        self.fg_color = fg or "#ffffff"
        self.hover_color = hover_bg or C["accent_hover"]
        self.press_color = C["accent_press"]
        self.label_text = f"{icon}  {text}" if icon else text
        self.font_size = font_size
        self._disabled = False

        self._draw(self.bg_color)

        self.bind("<Enter>", lambda e: self._on_enter())
        self.bind("<Leave>", lambda e: self._on_leave())
        self.bind("<ButtonPress-1>", lambda e: self._on_press())
        self.bind("<ButtonRelease-1>", lambda e: self._on_release())

    def _draw(self, color):
        self.delete("all")
        round_rect(self, 2, 2, self.w - 2, self.h - 2,
                   radius=self.radius, fill=color, outline="")
        self.create_text(self.w // 2, self.h // 2, text=self.label_text,
                         fill=self.fg_color,
                         font=("Segoe UI Semibold", self.font_size))

    def _on_enter(self):
        if not self._disabled:
            self._draw(self.hover_color)
            self.config(cursor="hand2")

    def _on_leave(self):
        if not self._disabled:
            self._draw(self.bg_color)
            self.config(cursor="")

    def _on_press(self):
        if not self._disabled:
            self._draw(self.press_color)

    def _on_release(self):
        if not self._disabled:
            self._draw(self.hover_color)
            if self.command:
                self.command()

    def set_disabled(self, disabled):
        self._disabled = disabled
        if disabled:
            self.fg_color = C["text_muted"]
            self._draw(C["surface3"])
        else:
            self.fg_color = "#ffffff"
            self._draw(self.bg_color)


# ─── Progress Bar ────────────────────────────────────────────────────────────
class GlowProgressBar(tk.Canvas):
    def __init__(self, parent, width=400, height=6, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self._progress = 0
        self._animating = False
        self._draw()

    def _draw(self):
        self.delete("all")
        round_rect(self, 0, 0, self.w, self.h, radius=3,
                   fill=C["surface3"], outline="")
        if self._progress > 0:
            fill_w = max(8, int(self.w * self._progress))
            round_rect(self, 0, 0, fill_w, self.h, radius=3,
                       fill=C["accent"], outline="")

    def set_progress(self, value):
        self._progress = max(0, min(1, value))
        self._draw()

    def start_indeterminate(self):
        self._animating = True
        self._ind_pos = 0
        self._animate_indeterminate()

    def stop_indeterminate(self):
        self._animating = False

    def _animate_indeterminate(self):
        if not self._animating:
            return
        self.delete("all")
        round_rect(self, 0, 0, self.w, self.h, radius=3,
                   fill=C["surface3"], outline="")
        bar_w = int(self.w * 0.3)
        x1 = int((self.w + bar_w) * (self._ind_pos / 100)) - bar_w
        x2 = x1 + bar_w
        x1 = max(0, x1)
        x2 = min(self.w, x2)
        if x2 > x1:
            round_rect(self, x1, 0, x2, self.h, radius=3,
                       fill=C["accent"], outline="")
        self._ind_pos = (self._ind_pos + 1.5) % 100
        self.after(20, self._animate_indeterminate)


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP SCREEN — Downloads Python + creates venv + installs Manim
# ═══════════════════════════════════════════════════════════════════════════════
class SetupScreen:
    """Full-screen setup wizard for first-time dependency installation."""

    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        self.frame = tk.Frame(root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)
        self._installing = False
        self._build_ui()

    def _build_ui(self):
        f = self.frame

        # ── Spacer ──
        tk.Frame(f, bg=C["bg"], height=60).pack()

        # ── Icon ──
        tk.Label(f, text="📦", font=("Segoe UI Emoji", 48),
                 bg=C["bg"]).pack()

        # ── Title ──
        tk.Label(f, text="Ortam Kurulumu",
                 font=("Segoe UI Semibold", 22), bg=C["bg"],
                 fg=C["text"]).pack(pady=(12, 4))
        tk.Label(f, text="Python ve Manim bağımlılıkları otomatik olarak indirilecek",
                 font=("Segoe UI", 10), bg=C["bg"],
                 fg=C["text_dim"]).pack()

        # ── Checklist Card ──
        card = tk.Frame(f, bg=C["surface"], highlightbackground=C["border"],
                        highlightthickness=1)
        card.pack(fill="x", padx=50, pady=(28, 0))

        self.checks = {}
        items = [
            ("python",  "Python Interpreter",     "Sistem Python'u bulunacak veya indirilecek"),
            ("venv",    "Sanal Ortam (venv)",      "İzole bir Python ortamı oluşturulacak"),
            ("pip",     "pip Paket Yöneticisi",    "pip kurulacak"),
            ("manim",   "Manim Community",         "Manim ve bağımlılıkları yüklenecek"),
            ("ffmpeg",  "FFmpeg",                  "Video kodlama aracı kontrol edilecek"),
        ]

        for i, (key, title, desc) in enumerate(items):
            row = tk.Frame(card, bg=C["surface"])
            row.pack(fill="x", padx=16, pady=(12 if i == 0 else 4, 12 if i == len(items) - 1 else 0))

            dot = tk.Canvas(row, width=20, height=20, bg=C["surface"],
                            highlightthickness=0)
            dot.pack(side="left", padx=(0, 12))
            # Default: gray circle
            dot.create_oval(4, 4, 16, 16, outline=C["text_muted"], width=2, fill="")

            col = tk.Frame(row, bg=C["surface"])
            col.pack(side="left", fill="x")
            lbl_title = tk.Label(col, text=title, font=("Segoe UI Semibold", 10),
                                 bg=C["surface"], fg=C["text"])
            lbl_title.pack(anchor="w")
            lbl_desc = tk.Label(col, text=desc, font=("Segoe UI", 8),
                                bg=C["surface"], fg=C["text_muted"])
            lbl_desc.pack(anchor="w")

            self.checks[key] = {"dot": dot, "title": lbl_title, "desc": lbl_desc}

        # ── Progress ──
        self.progress = GlowProgressBar(f, width=460, height=5)
        self.progress.pack(padx=50, pady=(20, 0))

        # ── Status ──
        self.status_var = tk.StringVar(value="Kuruluma başlamak için butona tıklayın")
        self.status_label = tk.Label(f, textvariable=self.status_var,
                                     font=("Segoe UI", 9), bg=C["bg"],
                                     fg=C["text_dim"])
        self.status_label.pack(pady=(8, 0))

        # ── Install Button ──
        btn_frame = tk.Frame(f, bg=C["bg"])
        btn_frame.pack(pady=(20, 0))

        self.install_btn = ModernButton(
            btn_frame, text="Kurulumu Başlat", icon="⬇",
            command=self._start_install, width=460, height=48,
            font_size=12, corner_radius=12
        )
        self.install_btn.pack()

        # ── Skip Setup Button ──
        self.skip_btn = ModernButton(
            btn_frame, text="Kurulumu Geç — Mevcut Python kullan", icon="⏭",
            command=self._skip_setup, width=460, height=40,
            bg=C["surface2"], hover_bg=C["surface3"],
            font_size=10, corner_radius=10
        )
        self.skip_btn.pack(pady=(10, 0))

        # ── Paths hint ──
        tk.Label(f, text=f"Kurulum dizini:  {APP_DIR}",
                 font=("Segoe UI", 8), bg=C["bg"],
                 fg=C["text_muted"]).pack(side="bottom", pady=(0, 16))

    # ── Checklist visual updates ──────────────────────────────────────────
    def _set_check(self, key, state):
        """state: 'pending' | 'active' | 'done' | 'error'"""
        dot = self.checks[key]["dot"]
        title_lbl = self.checks[key]["title"]
        dot.delete("all")
        if state == "pending":
            dot.create_oval(4, 4, 16, 16, outline=C["text_muted"], width=2, fill="")
            title_lbl.config(fg=C["text_dim"])
        elif state == "active":
            dot.create_oval(4, 4, 16, 16, outline=C["accent"], width=2, fill="")
            title_lbl.config(fg=C["text"])
        elif state == "done":
            dot.create_oval(2, 2, 18, 18, outline="", fill=C["success"])
            dot.create_text(10, 10, text="✓", fill="#fff",
                            font=("Segoe UI", 8, "bold"))
            title_lbl.config(fg=C["success"])
        elif state == "error":
            dot.create_oval(2, 2, 18, 18, outline="", fill=C["error"])
            dot.create_text(10, 10, text="✗", fill="#fff",
                            font=("Segoe UI", 8, "bold"))
            title_lbl.config(fg=C["error"])

    def _update_status(self, text, check_key=None, check_state=None):
        self.root.after(0, lambda: self.status_var.set(text))
        if check_key and check_state:
            self.root.after(0, lambda: self._set_check(check_key, check_state))

    def _update_desc(self, key, text):
        self.root.after(0, lambda: self.checks[key]["desc"].config(text=text))

    # ── Skip Setup (use existing install) ───────────────────────────────────
    def _skip_setup(self):
        """Let the user pick their existing python.exe that already has manim."""
        if self._installing:
            return

        chosen = filedialog.askopenfilename(
            title="Manim yüklü Python.exe dosyasını seçin",
            filetypes=[("Python", "python.exe"), ("Tüm dosyalar", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        if not chosen:
            return

        # Validate: can this python import manim?
        self.status_var.set("Seçilen Python kontrol ediliyor…")
        self.install_btn.set_disabled(True)
        self.skip_btn.set_disabled(True)

        def validate():
            try:
                result = subprocess.run(
                    [chosen, "-c", "import manim; print('ok')"],
                    capture_output=True, text=True, timeout=20,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.stdout.strip() == "ok":
                    # Success — write marker with custom path
                    os.makedirs(APP_DIR, exist_ok=True)
                    with open(SETUP_MARKER, "w", encoding="utf-8") as f:
                        json.dump({
                            "python_version": "custom",
                            "venv_dir": os.path.dirname(os.path.dirname(chosen)),
                            "python_exe": chosen,
                            "skipped_setup": True,
                        }, f, indent=2)

                    # Update global path
                    global PYTHON_EXE
                    PYTHON_EXE = chosen

                    self.root.after(0, lambda: self._on_skip_success(chosen))
                else:
                    err = result.stderr[:200] if result.stderr else "manim import edilemedi"
                    self.root.after(0, lambda: self._on_skip_fail(err))
            except Exception as e:
                self.root.after(0, lambda: self._on_skip_fail(str(e)))

        threading.Thread(target=validate, daemon=True).start()

    def _on_skip_success(self, python_path):
        for key in self.checks:
            self._set_check(key, "done")
        self.status_var.set(f"✅  Mevcut kurulum doğrulandı: {python_path}")
        self.progress.set_progress(1.0)
        self.root.after(1200, self._transition)

    def _on_skip_fail(self, error):
        self.status_var.set(f"❌  Bu Python'da manim bulunamadı: {error}")
        self.install_btn.set_disabled(False)
        self.skip_btn.set_disabled(False)

    # ── Install Orchestration ─────────────────────────────────────────────
    def _start_install(self):
        if self._installing:
            return
        self._installing = True
        self.install_btn.set_disabled(True)
        self.skip_btn.set_disabled(True)
        self.progress.start_indeterminate()
        thread = threading.Thread(target=self._install_worker, daemon=True)
        thread.start()

    def _install_worker(self):
        try:
            os.makedirs(APP_DIR, exist_ok=True)

            # ── Step 1: Find or download Python ──
            self._update_status("Python interpreter aranıyor…",
                                "python", "active")

            system_python = find_system_python()

            if system_python:
                python_for_venv = system_python
                self._update_desc("python", f"Bulundu: {system_python}")
                self._update_status("Sistem Python'u bulundu",
                                    "python", "done")
            else:
                # Download Python embeddable and install full Python via nuget-style
                self._update_status(
                    f"Python {PYTHON_VERSION} indiriliyor… (bu biraz sürebilir)",
                    "python", "active"
                )
                python_for_venv = self._download_python()
                if not python_for_venv:
                    self._fail("Python indirilemedi. İnternet bağlantınızı kontrol edin.",
                               "python")
                    return
                self._update_desc("python", f"İndirildi: Python {PYTHON_VERSION}")
                self._update_status("Python başarıyla indirildi", "python", "done")

            # ── Step 2: Create venv ──
            self._update_status("Sanal ortam oluşturuluyor…", "venv", "active")

            if os.path.isdir(VENV_DIR):
                shutil.rmtree(VENV_DIR, ignore_errors=True)

            result = subprocess.run(
                [python_for_venv, "-m", "venv", VENV_DIR],
                capture_output=True, text=True, timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode != 0:
                self._fail(f"venv oluşturulamadı: {result.stderr[:200]}", "venv")
                return

            self._update_desc("venv", VENV_DIR)
            self._update_status("Sanal ortam oluşturuldu", "venv", "done")

            # ── Step 3: Ensure pip ──
            self._update_status("pip kontrol ediliyor…", "pip", "active")

            # The venv should have pip, but let's make sure
            venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")

            result = subprocess.run(
                [venv_python, "-m", "pip", "--version"],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode != 0:
                # Download get-pip.py and install pip
                self._update_status("pip indiriliyor…", "pip", "active")
                get_pip_path = os.path.join(APP_DIR, "get-pip.py")
                self._download_file(GET_PIP_URL, get_pip_path)
                result = subprocess.run(
                    [venv_python, get_pip_path],
                    capture_output=True, text=True, timeout=120,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode != 0:
                    self._fail(f"pip kurulamadı: {result.stderr[:200]}", "pip")
                    return
                try:
                    os.remove(get_pip_path)
                except OSError:
                    pass

            # Upgrade pip
            subprocess.run(
                [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True, text=True, timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            self._update_desc("pip", "pip hazır")
            self._update_status("pip hazır", "pip", "done")

            # ── Step 4: Install Manim ──
            self._update_status(
                "Manim yükleniyor… (bu birkaç dakika sürebilir)",
                "manim", "active"
            )

            result = subprocess.run(
                [venv_python, "-m", "pip", "install", "manim"],
                capture_output=True, text=True, timeout=600,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode != 0:
                self._fail(f"Manim yüklenemedi: {result.stderr[:300]}", "manim")
                return

            self._update_desc("manim", "Manim Community Edition yüklendi")
            self._update_status("Manim yüklendi", "manim", "done")

            # ── Step 5: Check FFmpeg ──
            self._update_status("FFmpeg kontrol ediliyor…", "ffmpeg", "active")

            ffmpeg_ok = False
            try:
                result = subprocess.run(
                    [venv_python, "-c",
                     "from manim.utils.file_ops import *; print('ok')"],
                    capture_output=True, text=True, timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                # Also directly check ffmpeg
                ff_result = subprocess.run(
                    ["ffmpeg", "-version"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if ff_result.returncode == 0:
                    ffmpeg_ok = True
            except FileNotFoundError:
                pass

            if not ffmpeg_ok:
                # Try to install ffmpeg via pip (imageio-ffmpeg provides it)
                subprocess.run(
                    [venv_python, "-m", "pip", "install", "imageio[ffmpeg]"],
                    capture_output=True, text=True, timeout=120,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self._update_desc("ffmpeg", "imageio-ffmpeg ile sağlandı")
            else:
                self._update_desc("ffmpeg", "Sistem FFmpeg bulundu")

            self._update_status("FFmpeg hazır", "ffmpeg", "done")

            # ── Done: Write marker ──
            with open(SETUP_MARKER, "w", encoding="utf-8") as f:
                json.dump({
                    "python_version": PYTHON_VERSION,
                    "venv_dir": VENV_DIR,
                    "python_exe": PYTHON_EXE,
                }, f, indent=2)

            self.root.after(0, self._on_install_complete)

        except Exception as e:
            self._fail(f"Beklenmeyen hata: {str(e)[:200]}")

    def _download_python(self):
        """Download Python embeddable and use nuget/standalone installer approach.
        Falls back to using 'py' launcher if available."""
        try:
            # Try using the Python nuget package (standalone, no admin needed)
            nuget_dir = os.path.join(APP_DIR, "python_standalone")
            os.makedirs(nuget_dir, exist_ok=True)

            # Download embeddable Python
            zip_path = os.path.join(APP_DIR, "python_embed.zip")
            self._download_file(PYTHON_EMBED_URL, zip_path)

            # Extract
            embed_dir = os.path.join(APP_DIR, "python_embed")
            if os.path.isdir(embed_dir):
                shutil.rmtree(embed_dir)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(embed_dir)

            os.remove(zip_path)

            # Embeddable Python can't create venv directly.
            # We need to install the full Python. Let's try winget or direct MSI.
            # Simplest approach: use the embeddable Python + get-pip to bootstrap,
            # then install full Python via pip's python-build-standalone,
            # or just download the installer silently.

            # Actually, let's download the full Python installer and run it silently
            installer_url = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-amd64.exe"
            installer_path = os.path.join(APP_DIR, "python_installer.exe")

            self._update_status("Python yükleyicisi indiriliyor…")
            self._download_file(installer_url, installer_path)

            # Install Python silently to APP_DIR/python
            python_install_dir = os.path.join(APP_DIR, "python")
            self._update_status("Python yükleniyor…")

            result = subprocess.run(
                [installer_path,
                 "/quiet", "InstallAllUsers=0",
                 f"TargetDir={python_install_dir}",
                 "PrependPath=0",
                 "Include_test=0",
                 "Include_launcher=0",
                 "Include_pip=1"],
                capture_output=True, text=True, timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            try:
                os.remove(installer_path)
            except OSError:
                pass

            # Clean up embeddable
            shutil.rmtree(embed_dir, ignore_errors=True)

            python_exe = os.path.join(python_install_dir, "python.exe")
            if os.path.isfile(python_exe):
                return python_exe

            return None

        except Exception:
            return None

    def _download_file(self, url, dest):
        """Download a file with progress reporting."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "QuickAnimations/1.0"
            })
            with urllib.request.urlopen(req, timeout=120) as response:
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 65536

                with open(dest, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = downloaded / total
                            mb_done = downloaded / (1024 * 1024)
                            mb_total = total / (1024 * 1024)
                            self._update_status(
                                f"İndiriliyor… {mb_done:.1f} / {mb_total:.1f} MB ({pct*100:.0f}%)"
                            )
        except Exception as e:
            raise RuntimeError(f"İndirme hatası: {e}")

    def _fail(self, message, check_key=None):
        if check_key:
            self.root.after(0, lambda: self._set_check(check_key, "error"))
        self.root.after(0, lambda: self.progress.stop_indeterminate())
        self.root.after(0, lambda: self.progress.set_progress(0))
        self.root.after(0, lambda: self.status_var.set(f"❌  {message}"))
        self.root.after(0, lambda: self.install_btn.set_disabled(False))
        self._installing = False

    def _on_install_complete(self):
        self.progress.stop_indeterminate()
        self.progress.set_progress(1.0)
        self.status_var.set("✅  Kurulum tamamlandı! Uygulama başlatılıyor…")
        self.root.after(1500, self._transition)

    def _transition(self):
        self.frame.destroy()
        self.on_complete()

    def destroy(self):
        self.frame.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
class QuickAnimationsApp:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        if not root:
            self.root.title("QuickAnimations")
            self.root.configure(bg=C["bg"])
            self.root.resizable(False, False)
            win_w, win_h = 560, 640
            sx = (self.root.winfo_screenwidth() - win_w) // 2
            sy = (self.root.winfo_screenheight() - win_h) // 2
            self.root.geometry(f"{win_w}x{win_h}+{sx}+{sy}")
            self.root.attributes("-alpha", 0.97)

        self.svg_path = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Bir SVG dosyası seçerek başlayın")
        self.is_processing = False

        self.main_frame = tk.Frame(self.root, bg=C["bg"])
        self.main_frame.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self):
        f = self.main_frame

        # ── Title Bar ─────────────────────────────────────────────────────
        title_frame = tk.Frame(f, bg=C["bg"], height=70)
        title_frame.pack(fill="x", padx=28, pady=(24, 0))
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="⚡", font=("Segoe UI Emoji", 22),
                 bg=C["bg"], fg=C["accent"]).pack(side="left")
        title_col = tk.Frame(title_frame, bg=C["bg"])
        title_col.pack(side="left", padx=(10, 0))
        tk.Label(title_col, text="QuickAnimations",
                 font=("Segoe UI Semibold", 18), bg=C["bg"],
                 fg=C["text"]).pack(anchor="w")
        tk.Label(title_col, text="SVG → Manim MP4 · Hızlı animasyon aracı",
                 font=("Segoe UI", 9), bg=C["bg"],
                 fg=C["text_dim"]).pack(anchor="w")

        # ── Separator ────────────────────────────────────────────────────
        sep = tk.Canvas(f, height=1, bg=C["bg"], highlightthickness=0)
        sep.pack(fill="x", padx=28, pady=(16, 0))
        sep.create_line(0, 0, 600, 0, fill=C["border"], width=1)

        # ── Drop Zone Card ───────────────────────────────────────────────
        self.drop_frame = tk.Frame(f, bg=C["surface"],
                                   highlightbackground=C["border"],
                                   highlightthickness=1, highlightcolor=C["border"])
        self.drop_frame.pack(fill="x", padx=28, pady=(20, 0), ipady=30)

        self.drop_icon = tk.Label(self.drop_frame, text="📂",
                                  font=("Segoe UI Emoji", 36),
                                  bg=C["surface"], fg=C["accent"])
        self.drop_icon.pack(pady=(10, 4))

        self.drop_label = tk.Label(self.drop_frame,
                                   text="SVG dosyası seçmek için tıklayın",
                                   font=("Segoe UI", 11), bg=C["surface"],
                                   fg=C["text_dim"])
        self.drop_label.pack()

        self.file_label = tk.Label(self.drop_frame, text="",
                                   font=("Segoe UI", 9), bg=C["surface"],
                                   fg=C["text_muted"], wraplength=450)
        self.file_label.pack(pady=(4, 4))

        for widget in [self.drop_frame, self.drop_icon, self.drop_label, self.file_label]:
            widget.bind("<Button-1>", lambda e: self._browse_file())
            widget.bind("<Enter>", lambda e: self._drop_hover(True))
            widget.bind("<Leave>", lambda e: self._drop_hover(False))

        # ── Settings Card ────────────────────────────────────────────────
        settings_card = tk.Frame(f, bg=C["surface"],
                                 highlightbackground=C["border"],
                                 highlightthickness=1, highlightcolor=C["border"])
        settings_card.pack(fill="x", padx=28, pady=(16, 0))

        settings_header = tk.Frame(settings_card, bg=C["surface"])
        settings_header.pack(fill="x", padx=16, pady=(12, 8))
        tk.Label(settings_header, text="⚙️  Ayarlar",
                 font=("Segoe UI Semibold", 11),
                 bg=C["surface"], fg=C["text"]).pack(anchor="w")

        # Resolution
        row1 = tk.Frame(settings_card, bg=C["surface"])
        row1.pack(fill="x", padx=16, pady=(0, 6))
        tk.Label(row1, text="Çözünürlük", font=("Segoe UI", 10),
                 bg=C["surface"], fg=C["text_dim"], width=12,
                 anchor="w").pack(side="left")
        self.res_var = tk.StringVar(value="3840x2160 (4K)")
        res_options = ["1920x1080 (Full HD)", "2560x1440 (2K)", "3840x2160 (4K)"]
        self.res_menu = tk.OptionMenu(row1, self.res_var, *res_options)
        self.res_menu.config(bg=C["surface2"], fg=C["text"],
                             font=("Segoe UI", 10),
                             highlightthickness=0, relief="flat",
                             activebackground=C["surface3"],
                             activeforeground=C["text"], borderwidth=0)
        self.res_menu["menu"].config(bg=C["surface2"], fg=C["text"],
                                     activebackground=C["accent"],
                                     activeforeground="#fff",
                                     font=("Segoe UI", 10), borderwidth=0)
        self.res_menu.pack(side="right")

        # FPS
        row2 = tk.Frame(settings_card, bg=C["surface"])
        row2.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(row2, text="FPS", font=("Segoe UI", 10),
                 bg=C["surface"], fg=C["text_dim"], width=12,
                 anchor="w").pack(side="left")
        self.fps_var = tk.StringVar(value="60")
        fps_options = ["24", "30", "60"]
        self.fps_menu = tk.OptionMenu(row2, self.fps_var, *fps_options)
        self.fps_menu.config(bg=C["surface2"], fg=C["text"],
                             font=("Segoe UI", 10),
                             highlightthickness=0, relief="flat",
                             activebackground=C["surface3"],
                             activeforeground=C["text"], borderwidth=0)
        self.fps_menu["menu"].config(bg=C["surface2"], fg=C["text"],
                                     activebackground=C["accent"],
                                     activeforeground="#fff",
                                     font=("Segoe UI", 10), borderwidth=0)
        self.fps_menu.pack(side="right")

        # ── Render Button ────────────────────────────────────────────────
        btn_frame = tk.Frame(f, bg=C["bg"])
        btn_frame.pack(fill="x", padx=28, pady=(20, 0))

        self.render_btn = ModernButton(
            btn_frame, text="Animasyonu Oluştur", icon="▶",
            command=self._start_render, width=504, height=48,
            font_size=12, corner_radius=12
        )
        self.render_btn.pack()

        # ── Progress Bar ─────────────────────────────────────────────────
        self.progress = GlowProgressBar(f, width=504, height=5)
        self.progress.pack(padx=28, pady=(12, 0))

        # ── Status Bar ───────────────────────────────────────────────────
        status_frame = tk.Frame(f, bg=C["bg"])
        status_frame.pack(fill="x", padx=28, pady=(8, 0))

        self.status_dot = tk.Canvas(status_frame, width=8, height=8,
                                    bg=C["bg"], highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8), pady=2)
        self._draw_dot(C["text_muted"])

        self.status_label = tk.Label(status_frame,
                                     textvariable=self.status_text,
                                     font=("Segoe UI", 9), bg=C["bg"],
                                     fg=C["text_dim"], anchor="w")
        self.status_label.pack(side="left", fill="x")

        # ── Footer ───────────────────────────────────────────────────────
        footer = tk.Label(f,
                          text="Manim Community Edition tarafından desteklenmektedir",
                          font=("Segoe UI", 8), bg=C["bg"], fg=C["text_muted"])
        footer.pack(side="bottom", pady=(0, 14))

    # ── Helpers ───────────────────────────────────────────────────────────
    def _draw_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(1, 1, 7, 7, fill=color, outline="")

    def _drop_hover(self, entering):
        if entering:
            self.drop_frame.config(highlightbackground=C["border_hover"])
            for w in [self.drop_frame, self.drop_icon, self.drop_label, self.file_label]:
                w.config(cursor="hand2")
        else:
            self.drop_frame.config(highlightbackground=C["border"])
            for w in [self.drop_frame, self.drop_icon, self.drop_label, self.file_label]:
                w.config(cursor="")

    def _browse_file(self):
        if self.is_processing:
            return
        path = filedialog.askopenfilename(
            title="SVG Dosyası Seç",
            filetypes=[("SVG dosyaları", "*.svg"), ("Tüm dosyalar", "*.*")]
        )
        if path:
            self.svg_path.set(path)
            name = Path(path).name
            self.drop_icon.config(text="✅")
            self.drop_label.config(text=name, fg=C["text"])
            self.file_label.config(text=path)
            self._set_status("Hazır — Oluştur butonuna basın", C["success"])

    def _set_status(self, text, dot_color=None):
        self.status_text.set(text)
        if dot_color:
            self._draw_dot(dot_color)

    def _parse_resolution(self):
        val = self.res_var.get()
        if "3840" in val:
            return "3840,2160"
        elif "2560" in val:
            return "2560,1440"
        else:
            return "1920,1080"

    # ── Render Logic ──────────────────────────────────────────────────────
    def _start_render(self):
        svg = self.svg_path.get()
        if not svg or not os.path.isfile(svg):
            self._set_status("⚠  Lütfen geçerli bir SVG dosyası seçin", C["warning"])
            return
        if self.is_processing:
            return

        self.is_processing = True
        self.render_btn.set_disabled(True)
        self._set_status("Render başlatılıyor…", C["accent"])
        self.progress.start_indeterminate()

        thread = threading.Thread(target=self._render_worker, args=(svg,),
                                  daemon=True)
        thread.start()

    def _render_worker(self, svg_path):
        try:
            file_name_no_ext = Path(svg_path).stem
            temp_dir = tempfile.gettempdir()
            script_path = os.path.join(temp_dir, "manim_temp.py")
            output_path = os.path.join(
                os.path.expanduser("~/Desktop"),
                f"{file_name_no_ext}_animation.mp4"
            )
            svg_escaped = svg_path.replace("\\", "\\\\")
            resolution = self._parse_resolution()
            fps = self.fps_var.get()

            python_code = (
                "from manim import *\n"
                "class LogoAnimation(Scene):\n"
                "    def construct(self):\n"
                f"        m = SVGMobject(r'{svg_escaped}').scale(1).shift(UP)\n"
                f"        t = Text(r'{file_name_no_ext}').scale(1.5).next_to(m, DOWN)\n"
                "        self.play(Write(m, run_time=2))\n"
                "        self.play(Write(t, run_time=1))\n"
                "        self.wait(2)\n"
            )

            try:
                os.remove(script_path)
            except FileNotFoundError:
                pass

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(python_code)

            self.root.after(0, lambda: self._set_status(
                "Manim render ediliyor… bu biraz sürebilir", C["accent"]))

            command = (
                f'"{PYTHON_EXE}" -m manim "{script_path}" LogoAnimation '
                f'-r {resolution} -f {fps} --renderer=cairo --write_to_movie '
                f'--output_file "{output_path}"'
            )

            result = subprocess.run(command, shell=True,
                                    capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)

            try:
                os.remove(script_path)
            except FileNotFoundError:
                pass

            if os.path.isfile(output_path):
                self.root.after(0, lambda: self._on_render_success(output_path))
            else:
                err = result.stderr[-300:] if result.stderr else "Bilinmeyen hata"
                self.root.after(0, lambda: self._on_render_error(err))

        except Exception as e:
            self.root.after(0, lambda: self._on_render_error(str(e)))

    def _on_render_success(self, output_path):
        self.progress.stop_indeterminate()
        self.progress.set_progress(1.0)
        self.is_processing = False
        self.render_btn.set_disabled(False)
        self._set_status(f"✓  Tamamlandı — {Path(output_path).name}", C["success"])
        self._show_toast("Animasyon başarıyla oluşturuldu!", output_path)

    def _on_render_error(self, error_msg):
        self.progress.stop_indeterminate()
        self.progress.set_progress(0)
        self.is_processing = False
        self.render_btn.set_disabled(False)
        self._set_status("✗  Render başarısız oldu", C["error"])

    def _show_toast(self, message, file_path):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=C["surface"])

        tw, th = 380, 100
        sx = self.root.winfo_x() + (self.root.winfo_width() - tw) // 2
        sy = self.root.winfo_y() + self.root.winfo_height() - th - 60
        toast.geometry(f"{tw}x{th}+{sx}+{sy}")

        inner = tk.Frame(toast, bg=C["surface"],
                         highlightbackground=C["success"],
                         highlightthickness=1)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="✅  " + message,
                 font=("Segoe UI Semibold", 10), bg=C["surface"],
                 fg=C["success"]).pack(padx=16, pady=(14, 4), anchor="w")
        tk.Label(inner, text=Path(file_path).name,
                 font=("Segoe UI", 9), bg=C["surface"],
                 fg=C["text_dim"]).pack(padx=16, anchor="w")

        def open_folder():
            os.startfile(os.path.dirname(file_path))

        link = tk.Label(inner, text="📁 Klasörü Aç",
                        font=("Segoe UI", 9),
                        bg=C["surface"], fg=C["accent"], cursor="hand2")
        link.pack(padx=16, anchor="w", pady=(2, 0))
        link.bind("<Button-1>", lambda e: open_folder())

        toast.after(5000, toast.destroy)

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT — Auto-detects environment and shows Setup or Main screen
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    if len(sys.argv) > 1:
        # CLI mode — skip GUI
        arg = sys.argv[1]
        if arg == "--setup":
            # Force setup screen
            root = tk.Tk()
            root.title("QuickAnimations — Kurulum")
            root.configure(bg=C["bg"])
            root.resizable(False, False)
            win_w, win_h = 560, 640
            sx = (root.winfo_screenwidth() - win_w) // 2
            sy = (root.winfo_screenheight() - win_h) // 2
            root.geometry(f"{win_w}x{win_h}+{sx}+{sy}")
            root.attributes("-alpha", 0.97)
            SetupScreen(root, lambda: _launch_main_in_root(root))
            root.mainloop()
        elif arg == "--cli":
            if len(sys.argv) > 2:
                _process_svg_cli(sys.argv[2])
            else:
                print('Kullanım: python QuickAnimations.py --cli "dosya.svg"')
        else:
            _process_svg_cli(arg)
    else:
        # GUI mode
        root = tk.Tk()
        root.title("QuickAnimations")
        root.configure(bg=C["bg"])
        root.resizable(False, False)
        win_w, win_h = 560, 640
        sx = (root.winfo_screenwidth() - win_w) // 2
        sy = (root.winfo_screenheight() - win_h) // 2
        root.geometry(f"{win_w}x{win_h}+{sx}+{sy}")
        root.attributes("-alpha", 0.97)

        if is_setup_complete():
            QuickAnimationsApp(root)
        else:
            SetupScreen(root, lambda: _launch_main_in_root(root))

        root.mainloop()


def _launch_main_in_root(root):
    """Transition from setup to main app within the same window."""
    QuickAnimationsApp(root)


def _process_svg_cli(svg_path):
    """Headless CLI render."""
    if not os.path.isfile(svg_path):
        print(f"Hata: Dosya bulunamadı: {svg_path}")
        return

    if not is_setup_complete():
        print("Hata: Ortam henüz kurulmamış. Önce GUI'yi çalıştırın: python QuickAnimations.py")
        return

    file_name_no_ext = Path(svg_path).stem
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "manim_temp.py")
    output_path = os.path.join(
        os.path.expanduser("~/Desktop"),
        f"{file_name_no_ext}_animation.mp4"
    )
    svg_escaped = svg_path.replace("\\", "\\\\")

    python_code = (
        "from manim import *\n"
        "class LogoAnimation(Scene):\n"
        "    def construct(self):\n"
        f"        m = SVGMobject(r'{svg_escaped}').scale(1).shift(UP)\n"
        f"        t = Text(r'{file_name_no_ext}').scale(1.5).next_to(m, DOWN)\n"
        "        self.play(Write(m, run_time=2))\n"
        "        self.play(Write(t, run_time=1))\n"
        "        self.wait(2)\n"
    )

    try:
        os.remove(script_path)
    except FileNotFoundError:
        pass
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(python_code)

    command = (
        f'"{PYTHON_EXE}" -m manim "{script_path}" LogoAnimation '
        f'-r 3840,2160 -f 60 --renderer=cairo --write_to_movie '
        f'--output_file "{output_path}"'
    )
    subprocess.run(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    try:
        os.remove(script_path)
    except FileNotFoundError:
        pass

    if os.path.isfile(output_path):
        print(f"✓ Video oluşturuldu: {output_path}")
    else:
        print("✗ Video oluşturulamadı.")


if __name__ == "__main__":
    main()
