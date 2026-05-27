#!/usr/bin/env python3
"""
Zeno AutoClicker
- Tecla configurada (teclado OU botão extra do mouse): toggle ON/OFF
- Uma mesma tecla pode ativar múltiplos painéis ao mesmo tempo
- Com o clicker ativo + botão físico pressionado: clica no CPS configurado
- SendInput (Windows API) para compatibilidade com jogos
- Sons de clique reais via pygame (MP3)
"""

import customtkinter as ctk
import threading
import time
import random
import json
import os
import ctypes
import ctypes.wintypes
import sys

from pynput.keyboard import Key, KeyCode, Listener as KeyListener
from pynput.mouse import Button, Listener as MouseListener

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pygame
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False

try:
    import pystray
    PYSTRAY_OK = True
except ImportError:
    PYSTRAY_OK = False

# ── Constantes de visual ───────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG         = "#111111"
FRAME_BG   = "#1c1c1c"
BORDER_OFF = "#2a2a2a"
TEXT       = "#dddddd"
TEXT_DIM   = "#555555"
BTN_BG     = "#252525"
BTN_HOVER  = "#333333"

FONT_SM   = ("Segoe UI", 12)
FONT_MD   = ("Segoe UI", 13)
FONT_BOLD = ("Segoe UI", 13, "bold")

ACCENT_PRESETS = {
    "Vermelho": ("#cc2222", "#aa1111"),
    "Rosa":     ("#cc2277", "#aa1155"),
    "Roxo":     ("#8833cc", "#6611aa"),
    "Azul":     ("#2266cc", "#1144aa"),
    "Ciano":    ("#1199bb", "#0077aa"),
    "Verde":    ("#22aa44", "#118833"),
    "Laranja":  ("#cc6622", "#aa4411"),
    "Branco":   ("#aaaaaa", "#888888"),
}

# Nomes dos arquivos de som (na pasta do app)
SOUND_FILES = {
    "GPro Hero":    "mouse-clicks.mp3",
    "DeathAdder V3": "computer-mouse-click-1.mp3",
    "Model O":      "clicksoundeffect.mp3",
}


def resource_path(rel: str) -> str:
    try:
        base = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)


if getattr(sys, "frozen", False):
    _CFG_DIR = os.path.dirname(sys.executable)
else:
    _CFG_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS  = os.path.join(_CFG_DIR, "settings.json")
LOGO_PATH = resource_path("logo.png")
ICON_PATH = resource_path("logo.ico")


# ── Tema global ────────────────────────────────────────────────────────────────
class Theme:
    def __init__(self, color="#cc2222", dim="#aa1111"):
        self.color = color
        self.dim   = dim
        self._subs = []

    def subscribe(self, fn):
        self._subs.append(fn)

    def apply(self, color, dim):
        self.color = color
        self.dim   = dim
        for fn in self._subs:
            try:
                fn(color, dim)
            except Exception:
                pass


T = Theme()


# ── Reprodução de som ──────────────────────────────────────────────────────────
_sound_cache: dict = {}
_sound_lock  = threading.Lock()
_current_sound_file: str = "mouse-clicks.mp3"  # padrão: GPro Hero


def _set_sound_file(filename: str):
    global _current_sound_file
    _current_sound_file = filename


def _play_click():
    """Toca o som de clique atual (não bloqueante)."""
    if not PYGAME_OK or not _current_sound_file:
        return
    path = resource_path(_current_sound_file)
    if not os.path.exists(path):
        return
    def _do():
        try:
            with _sound_lock:
                if path not in _sound_cache:
                    _sound_cache[path] = pygame.mixer.Sound(path)
                snd = _sound_cache[path]
            snd.play()
        except Exception:
            pass
    threading.Thread(target=_do, daemon=True).start()


# ── Windows API – SendInput ────────────────────────────────────────────────────
_INPUT_MOUSE           = 0
_MOUSEEVENTF_MOVE      = 0x0001
_MOUSEEVENTF_LEFTDOWN  = 0x0002
_MOUSEEVENTF_LEFTUP    = 0x0004
_MOUSEEVENTF_RIGHTDOWN = 0x0008
_MOUSEEVENTF_RIGHTUP   = 0x0010


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          ctypes.c_long),
        ("dy",          ctypes.c_long),
        ("mouseData",   ctypes.c_ulong),
        ("dwFlags",     ctypes.c_ulong),
        ("time",        ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("_u", _INPUT_UNION)]


def _send_flag(flag: int):
    mi  = _MOUSEINPUT(dwFlags=flag)
    inp = _INPUT(type=_INPUT_MOUSE, _u=_INPUT_UNION(mi=mi))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


def _click_left():
    _send_flag(_MOUSEEVENTF_LEFTDOWN)
    time.sleep(0.007)
    _send_flag(_MOUSEEVENTF_LEFTUP)


def _click_right():
    _send_flag(_MOUSEEVENTF_RIGHTDOWN)
    time.sleep(0.007)
    _send_flag(_MOUSEEVENTF_RIGHTUP)


def _jitter_move(intensity: float):
    """Micro-movimento aleatório do mouse — simula o tremor do braço no jitter clicking."""
    # intensity 0-20 → deslocamento máximo de 1-4 pixels (normalizado)
    max_px = max(1, round((intensity / 20.0) * 4))
    dx = random.randint(-max_px, max_px)
    dy = random.randint(-max_px, max_px)
    # garante que sempre há algum deslocamento
    if dx == 0:
        dx = random.choice([-1, 1])
    mi  = _MOUSEINPUT(dx=dx, dy=dy, dwFlags=_MOUSEEVENTF_MOVE)
    inp = _INPUT(type=_INPUT_MOUSE, _u=_INPUT_UNION(mi=mi))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


# ── Rastreamento físico do mouse (WH_MOUSE_LL + filtro LLMHF_INJECTED) ────────
_phys_left  = False
_phys_right = False

_WH_MOUSE_LL    = 14
_WM_LBUTTONDOWN = 0x0201
_WM_LBUTTONUP   = 0x0202
_WM_RBUTTONDOWN = 0x0204
_WM_RBUTTONUP   = 0x0205
_LLMHF_INJECTED = 0x00000001


class _MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt",          ctypes.wintypes.POINT),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


_HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
)

_hook_proc_ref = None


def _start_mouse_tracker():
    global _hook_proc_ref

    _u32 = ctypes.WinDLL("user32.dll")

    _u32.SetWindowsHookExW.restype  = ctypes.c_void_p
    _u32.SetWindowsHookExW.argtypes = [
        ctypes.c_int, _HOOKPROC, ctypes.c_void_p, ctypes.wintypes.DWORD]
    _u32.CallNextHookEx.restype  = ctypes.c_long
    _u32.CallNextHookEx.argtypes = [
        ctypes.c_void_p, ctypes.c_int,
        ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
    _u32.UnhookWindowsHookEx.restype  = ctypes.wintypes.BOOL
    _u32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
    _u32.GetMessageW.restype  = ctypes.wintypes.BOOL
    _u32.GetMessageW.argtypes = [
        ctypes.POINTER(ctypes.wintypes.MSG),
        ctypes.wintypes.HWND,
        ctypes.wintypes.UINT,
        ctypes.wintypes.UINT]
    _u32.TranslateMessage.argtypes = [ctypes.POINTER(ctypes.wintypes.MSG)]
    _u32.DispatchMessageW.argtypes  = [ctypes.POINTER(ctypes.wintypes.MSG)]

    @_HOOKPROC
    def _proc(nCode, wParam, lParam):
        global _phys_left, _phys_right
        if nCode >= 0:
            info = ctypes.cast(lParam, ctypes.POINTER(_MSLLHOOKSTRUCT)).contents
            if not (info.flags & _LLMHF_INJECTED):
                if   wParam == _WM_LBUTTONDOWN: _phys_left  = True
                elif wParam == _WM_LBUTTONUP:   _phys_left  = False
                elif wParam == _WM_RBUTTONDOWN: _phys_right = True
                elif wParam == _WM_RBUTTONUP:   _phys_right = False
        return _u32.CallNextHookEx(None, nCode, wParam, lParam)

    _hook_proc_ref = _proc

    def _pump():
        hook = _u32.SetWindowsHookExW(_WH_MOUSE_LL, _proc, None, 0)
        if not hook:
            return
        msg = ctypes.wintypes.MSG()
        while _u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            _u32.TranslateMessage(ctypes.byref(msg))
            _u32.DispatchMessageW(ctypes.byref(msg))
        _u32.UnhookWindowsHookEx(hook)

    threading.Thread(target=_pump, daemon=True).start()


# ── Motor de cliques ───────────────────────────────────────────────────────────
class Clicker:
    def __init__(self, phys_flag: str, click_fn):
        self._flag     = phys_flag
        self._click_fn = click_fn
        self._active   = False
        self._cps      = 10.0
        self._jitter   = 0.0
        self._sound    = False
        self._lock     = threading.Lock()

    def _phys_held(self) -> bool:
        return bool(globals().get(self._flag, False))

    @property
    def active(self) -> bool:
        return self._active

    def set_cps(self, v: float):
        self._cps = max(1.0, min(20.0, float(v)))

    def set_jitter(self, v: float):
        self._jitter = max(0.0, min(20.0, float(v)))

    def set_sound(self, v: bool):
        self._sound = bool(v)

    def enable(self):
        with self._lock:
            if not self._active:
                self._active = True
                threading.Thread(target=self._loop, daemon=True).start()

    def disable(self):
        with self._lock:
            self._active = False

    def toggle(self):
        with self._lock:
            if self._active:
                self._active = False
            else:
                self._active = True
                threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self._active = False

    def _loop(self):
        while self._active:
            if self._phys_held():
                t0 = time.perf_counter()
                # Jitter: micro-movimento antes de clicar (simula tremor do braço)
                if self._jitter > 0.0:
                    _jitter_move(self._jitter)
                self._click_fn()
                if self._sound:
                    _play_click()
                # Intervalo base + variação aleatória de timing (também parte do jitter)
                interval = 1.0 / self._cps
                if self._jitter > 0.0:
                    max_var = interval * 0.35 * (self._jitter / 20.0)
                    interval += random.uniform(-max_var, max_var)
                interval = max(0.015, interval)
                elapsed = time.perf_counter() - t0
                remaining = interval - elapsed
                if remaining > 0:
                    time.sleep(remaining)
            else:
                time.sleep(0.004)


# ── Bind: tecla de teclado OU botão extra do mouse ────────────────────────────
class BindKey:
    """Encapsula uma tecla de teclado OU um botão de mouse como bind."""

    def __init__(self, kb_key=None, mouse_btn=None):
        self._kb = kb_key
        self._mb = mouse_btn  # ex: "button4"

    @property
    def is_set(self):
        return self._kb is not None or self._mb is not None

    def matches_key(self, key):
        if self._kb is None:
            return False
        return str(key) == str(self._kb)

    def matches_mouse(self, btn_name):
        return self._mb == btn_name

    def label(self):
        if self._kb is not None:
            return _key_label(self._kb)
        if self._mb is not None:
            return _mouse_btn_label(self._mb)
        return "NONE"

    def to_str(self):
        if self._kb is not None:
            return "kb:" + str(self._kb)
        if self._mb is not None:
            return "mb:" + self._mb
        return None

    @staticmethod
    def from_str(s):
        if s.startswith("kb:"):
            return BindKey(kb_key=key_from_str(s[3:]))
        if s.startswith("mb:"):
            return BindKey(mouse_btn=s[3:])
        # legado sem prefixo
        k = key_from_str(s)
        return BindKey(kb_key=k)


def _key_label(k):
    if k is None:
        return "NONE"
    try:
        if hasattr(k, "char") and k.char:
            return k.char.upper()
    except Exception:
        pass
    name = str(k).replace("Key.", "")
    table = {
        "space": "SPACE", "ctrl_l": "CTRL", "ctrl_r": "CTRL",
        "shift_l": "SHIFT", "shift_r": "SHIFT",
        "alt_l": "ALT", "alt_r": "ALT",
        "caps_lock": "CAPS", "tab": "TAB",
        "enter": "ENTER", "esc": "ESC",
        "backspace": "BKSP", "delete": "DEL",
        "up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT",
    }
    for i in range(1, 13):
        table[f"f{i}"] = f"F{i}"
    return table.get(name, name.upper()[:8])


def _mouse_btn_label(btn_name):
    mapping = {
        "button3": "M3", "button4": "M4", "button5": "M5",
        "button6": "M6", "button7": "M7", "button8": "M8",
    }
    return mapping.get(btn_name, btn_name.upper())


def key_from_str(s):
    try:
        if s.startswith("Key."):
            return Key[s[4:]]
        ch = s.strip("'\"")
        if ch:
            return KeyCode.from_char(ch)
    except Exception:
        pass
    return None


# ── Widgets ────────────────────────────────────────────────────────────────────
class AccentSlider(ctk.CTkSlider):
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            progress_color=T.color,
            button_color=T.color,
            button_hover_color=T.dim,
            **kwargs,
        )
        T.subscribe(lambda c, d: self.configure(
            progress_color=c, button_color=c, button_hover_color=d))


class Panel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, fg_color=FRAME_BG,
            border_color=BORDER_OFF, border_width=2,
            corner_radius=8, **kwargs)
        self._on = False
        T.subscribe(self._on_theme)

    def set_active(self, v):
        self._on = v
        self.configure(border_color=T.color if v else BORDER_OFF)

    def _on_theme(self, c, d):
        if self._on:
            self.configure(border_color=c)


class BindButton(ctk.CTkButton):
    """Captura tecla de teclado OU botão extra do mouse."""

    _BLOCKED_MOUSE = {"button1", "button2"}

    def __init__(self, master, on_start=None, on_bind=None, **kwargs):
        super().__init__(
            master, text="Bind: NONE",
            width=120, height=28, corner_radius=4,
            fg_color=BTN_BG, hover_color=BTN_HOVER,
            text_color=TEXT, font=FONT_SM, **kwargs)
        self._bind     = BindKey()
        self._on_start = on_start
        self._on_bind  = on_bind
        self._waiting  = False
        self._kb_lst   = None
        self._ms_lst   = None
        self.configure(command=self._start)

    @property
    def bind(self):
        return self._bind

    def load_bind(self, bk):
        self._bind = bk
        self.configure(text=f"Bind: {bk.label()}")

    def _start(self):
        if self._waiting:
            return
        self._waiting = True
        if self._on_start:
            self._on_start()
        self.configure(text="Pressione...", fg_color="#441111")
        self._kb_lst = KeyListener(on_press=self._capture_key)
        self._kb_lst.start()
        self._ms_lst = MouseListener(on_click=self._capture_mouse)
        self._ms_lst.start()

    def _finish(self, bk):
        self._bind    = bk
        self._waiting = False
        self.configure(text=f"Bind: {bk.label()}", fg_color=BTN_BG)
        try:
            self._kb_lst.stop()
        except Exception:
            pass
        try:
            self._ms_lst.stop()
        except Exception:
            pass
        if self._on_bind:
            self._on_bind(bk)

    def _capture_key(self, key):
        if not self._waiting:
            return False
        bk = BindKey(kb_key=key)
        self.after(0, lambda: self._finish(bk))
        return False

    def _capture_mouse(self, x, y, button, pressed):
        if not self._waiting or not pressed:
            return
        btn_name = str(button).replace("Button.", "button")
        if btn_name in self._BLOCKED_MOUSE:
            return
        bk = BindKey(mouse_btn=btn_name)
        self.after(0, lambda: self._finish(bk))
        return False


class SliderRow(ctk.CTkFrame):
    def __init__(self, master, label, from_=1.0, to=20.0,
                 initial=10.0, step=0.5, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._step = step
        self._cmd  = command
        self._raw  = ctk.DoubleVar(value=initial)
        self._disp = ctk.StringVar(value=f"{initial:.1f}")

        ctk.CTkLabel(self, textvariable=self._disp, width=40,
                     font=FONT_SM, text_color=TEXT, anchor="e").pack(side="left")

        self._sl = AccentSlider(self, from_=from_, to=to,
                                variable=self._raw, height=16,
                                command=self._slide)
        self._sl.pack(side="left", fill="x", expand=True, padx=6)

        ctk.CTkLabel(self, text=label, width=80,
                     font=FONT_SM, text_color=TEXT_DIM, anchor="w").pack(side="left")

    def _slide(self, val):
        s = round(round(val / self._step) * self._step, 2)
        self._raw.set(s)
        self._disp.set(f"{s:.1f}")
        if self._cmd:
            self._cmd(s)

    def get(self):
        return self._raw.get()

    def set(self, v):
        self._raw.set(float(v))
        self._disp.set(f"{float(v):.1f}")


# ── Listener global de mouse (botões extras como bind de ação) ────────────────
_global_mouse_listeners = []


def _add_global_mouse_trigger(callback):
    _global_mouse_listeners.append(callback)


def _start_global_mouse_listener():
    def on_click(x, y, button, pressed):
        if not pressed:
            return
        btn_name = str(button).replace("Button.", "button")
        if btn_name in ("button1", "button2"):
            return
        for cb in _global_mouse_listeners:
            try:
                cb(btn_name)
            except Exception:
                pass

    lst = MouseListener(on_click=on_click)
    lst.daemon = True
    lst.start()


# ── Aplicativo ─────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Zeno")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        if os.path.exists(ICON_PATH):
            self.iconbitmap(ICON_PATH)

        _start_mouse_tracker()
        _start_global_mouse_listener()

        self._lc     = Clicker("_phys_left",  _click_left)
        self._rc     = Clicker("_phys_right", _click_right)
        self._lc_on  = False
        self._rc_on  = False
        self._j_on   = False
        self._snd_on = False
        self._binding = False
        self._tray        = None
        self._tray_thread = None

        self._build_ui()
        self._start_global_kb_listener()
        _add_global_mouse_trigger(self._on_mouse_btn)
        self._load_settings()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color=FRAME_BG, corner_radius=10)
        hdr.pack(fill="x", padx=12, pady=(12, 0))
        self._build_logo(hdr)

        tc = ctk.CTkFrame(hdr, fg_color="transparent")
        tc.pack(side="left", pady=10)
        ctk.CTkLabel(tc, text="Zeno",
                     font=("Segoe UI", 15, "bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(tc, text="AutoClicker",
                     font=FONT_SM, text_color=TEXT_DIM).pack(anchor="w")

        cc = ctk.CTkFrame(hdr, fg_color="transparent")
        cc.pack(side="right", padx=10, pady=10)
        ctk.CTkLabel(cc, text="Cor", font=FONT_SM, text_color=TEXT_DIM).pack()
        dots = ctk.CTkFrame(cc, fg_color="transparent")
        dots.pack()
        for nm, (c, d) in ACCENT_PRESETS.items():
            ctk.CTkButton(
                dots, text="", width=20, height=20, corner_radius=10,
                fg_color=c, hover_color=d, border_width=0,
                command=lambda col=c, dim=d: self._set_color(col, dim),
            ).pack(side="left", padx=1, pady=2)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(padx=12, pady=12)

        left  = ctk.CTkFrame(body, fg_color="transparent")
        right = ctk.CTkFrame(body, fg_color="transparent")
        left.pack(side="left", padx=(0, 8), anchor="n")
        right.pack(side="left", anchor="n")

        # Left Clicker
        self._lc_panel = Panel(left)
        self._lc_panel.pack(fill="x", pady=(0, 8))
        self._lc_btn, self._lc_bind = self._make_header(
            self._lc_panel, "Left Clicker", self._toggle_lc)
        self._lc_cps = SliderRow(
            self._lc_panel, "CPS", initial=10,
            command=lambda v: (self._lc.set_cps(v), self._save()))
        self._lc_cps.pack(fill="x", padx=8, pady=(2, 8))

        # Right Clicker
        self._rc_panel = Panel(left)
        self._rc_panel.pack(fill="x")
        self._rc_btn, self._rc_bind = self._make_header(
            self._rc_panel, "Right Clicker", self._toggle_rc)
        self._rc_cps = SliderRow(
            self._rc_panel, "CPS", initial=10,
            command=lambda v: (self._rc.set_cps(v), self._save()))
        self._rc_cps.pack(fill="x", padx=8, pady=(2, 8))

        # Jitter
        self._j_panel = Panel(right)
        self._j_panel.pack(fill="x", pady=(0, 8))
        self._j_btn, self._j_bind = self._make_header(
            self._j_panel, "Jitter", self._toggle_jitter)
        self._j_spd = SliderRow(
            self._j_panel, "Intensidade",
            from_=0.0, to=20.0, initial=0.0, step=0.5,
            command=self._apply_jitter)
        self._j_spd.pack(fill="x", padx=8, pady=(2, 4))
        # Alvo do jitter: Esquerdo | Ambos | Direito
        self._j_target_var = ctk.StringVar(value="Ambos")
        self._j_target_seg = ctk.CTkSegmentedButton(
            self._j_panel,
            values=["Esquerdo", "Ambos", "Direito"],
            variable=self._j_target_var,
            command=self._on_jitter_target_change,
            fg_color=FRAME_BG,
            selected_color=T.color,
            selected_hover_color=T.dim,
            unselected_color=BTN_BG,
            unselected_hover_color=BTN_HOVER,
            text_color=TEXT,
            font=FONT_SM,
            height=26,
        )
        self._j_target_seg.pack(fill="x", padx=8, pady=(0, 8))
        T.subscribe(lambda c, d: self._j_target_seg.configure(
            selected_color=c, selected_hover_color=d))

        # Click Sounds
        self._snd_panel = Panel(right)
        self._snd_panel.pack(fill="x")
        self._snd_btn, self._snd_bind = self._make_header(
            self._snd_panel, "Click Sounds", self._toggle_sounds)
        snd_row = ctk.CTkFrame(self._snd_panel, fg_color="transparent")
        snd_row.pack(fill="x", padx=8, pady=(2, 8))
        self._sound_var = ctk.StringVar(value="GPro Hero")
        self._sound_menu = ctk.CTkOptionMenu(
            snd_row, variable=self._sound_var,
            values=list(SOUND_FILES.keys()),
            width=150, height=28,
            fg_color=BTN_BG, button_color=T.color,
            button_hover_color=T.dim,
            dropdown_fg_color=FRAME_BG,
            text_color=TEXT, font=FONT_SM,
            command=self._on_sound_change,
        )
        self._sound_menu.pack(side="left")
        T.subscribe(lambda c, d: self._sound_menu.configure(
            button_color=c, button_hover_color=d))

    def _build_logo(self, parent):
        if PIL_AVAILABLE and os.path.exists(LOGO_PATH):
            try:
                raw  = Image.open(LOGO_PATH).convert("RGBA").resize(
                    (52, 52), Image.LANCZOS)
                cimg = ctk.CTkImage(raw, size=(52, 52))
                ctk.CTkLabel(parent, image=cimg, text="").pack(
                    side="left", padx=(10, 8), pady=8)
                return
            except Exception:
                pass
        lbl = ctk.CTkLabel(parent, text="Z", width=52, height=52,
                           font=("Segoe UI", 20, "bold"), text_color=T.color)
        lbl.pack(side="left", padx=(10, 8), pady=8)
        T.subscribe(lambda c, d: lbl.configure(text_color=c))

    def _make_header(self, parent, label, cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(8, 4))
        btn = ctk.CTkButton(
            row, text=label, width=130, height=28, corner_radius=4,
            fg_color=BTN_BG, hover_color=BTN_HOVER,
            text_color=TEXT, font=FONT_BOLD, command=cmd)
        btn.pack(side="left")
        bind = BindButton(row, on_start=self._bind_started,
                          on_bind=self._bind_done)
        bind.pack(side="right")
        return btn, bind

    # ── Cor ────────────────────────────────────────────────────────────────────
    def _set_color(self, color, dim):
        T.apply(color, dim)
        for btn, on in [(self._lc_btn, self._lc_on),
                        (self._rc_btn, self._rc_on),
                        (self._j_btn,  self._j_on),
                        (self._snd_btn, self._snd_on)]:
            btn.configure(fg_color=T.color if on else BTN_BG)
        self._save()

    # ── Toggles ────────────────────────────────────────────────────────────────
    def _toggle_lc(self):
        self._lc_on = not self._lc_on
        if self._lc_on:
            self._lc.enable()
        else:
            self._lc.disable()
        self._lc_panel.set_active(self._lc_on)
        self._lc_btn.configure(fg_color=T.color if self._lc_on else BTN_BG)

    def _toggle_rc(self):
        self._rc_on = not self._rc_on
        if self._rc_on:
            self._rc.enable()
        else:
            self._rc.disable()
        self._rc_panel.set_active(self._rc_on)
        self._rc_btn.configure(fg_color=T.color if self._rc_on else BTN_BG)

    def _toggle_jitter(self):
        self._j_on = not self._j_on
        self._j_panel.set_active(self._j_on)
        self._j_btn.configure(fg_color=T.color if self._j_on else BTN_BG)
        self._apply_jitter(self._j_spd.get())

    def _toggle_sounds(self):
        self._snd_on = not self._snd_on
        self._snd_panel.set_active(self._snd_on)
        self._snd_btn.configure(fg_color=T.color if self._snd_on else BTN_BG)
        self._lc.set_sound(self._snd_on)
        self._rc.set_sound(self._snd_on)

    def _on_jitter_target_change(self, _val):
        self._apply_jitter(self._j_spd.get())
        self._save()

    def _apply_jitter(self, val):
        v = val if self._j_on else 0.0
        target = self._j_target_var.get() if hasattr(self, "_j_target_var") else "Ambos"
        self._lc.set_jitter(v if target in ("Esquerdo", "Ambos") else 0.0)
        self._rc.set_jitter(v if target in ("Direito",  "Ambos") else 0.0)
        self._save()

    def _on_sound_change(self, choice):
        filename = SOUND_FILES.get(choice, "")
        _set_sound_file(filename)
        self._save()

    # ── Listeners globais ───────────────────────────────────────────────────────
    def _bind_started(self):
        self._binding = True

    def _bind_done(self, _bk):
        self._binding = False
        self._save()

    def _start_global_kb_listener(self):
        lst = KeyListener(on_press=self._on_key)
        lst.daemon = True
        lst.start()

    def _on_key(self, key):
        if self._binding:
            return
        # SEM break — uma tecla pode acionar múltiplos painéis
        pairs = [
            (self._lc_bind, self._toggle_lc),
            (self._rc_bind, self._toggle_rc),
            (self._j_bind,  self._toggle_jitter),
            (self._snd_bind, self._toggle_sounds),
        ]
        for bb, action in pairs:
            if bb.bind.matches_key(key):
                self.after(0, action)

    def _on_mouse_btn(self, btn_name):
        if self._binding:
            return
        pairs = [
            (self._lc_bind, self._toggle_lc),
            (self._rc_bind, self._toggle_rc),
            (self._j_bind,  self._toggle_jitter),
            (self._snd_bind, self._toggle_sounds),
        ]
        for bb, action in pairs:
            if bb.bind.matches_mouse(btn_name):
                self.after(0, action)

    # ── Persistência ───────────────────────────────────────────────────────────
    def _save(self):
        data = {
            "lc_cps":     self._lc_cps.get(),
            "rc_cps":     self._rc_cps.get(),
            "jitter":     self._j_spd.get(),
            "j_target":   self._j_target_var.get(),
            "sound":      self._sound_var.get(),
            "accent":     T.color,
            "accent_dim": T.dim,
        }
        for attr, name in [
            ("_lc_bind", "lc_bind"),
            ("_rc_bind", "rc_bind"),
            ("_j_bind",  "j_bind"),
            ("_snd_bind","snd_bind"),
        ]:
            s = getattr(self, attr).bind.to_str()
            if s:
                data[name] = s
        try:
            with open(SETTINGS, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_settings(self):
        if not os.path.exists(SETTINGS):
            return
        try:
            with open(SETTINGS) as f:
                d = json.load(f)

            self._lc_cps.set(d.get("lc_cps", 10))
            self._rc_cps.set(d.get("rc_cps", 10))
            self._j_spd.set(d.get("jitter", 0))

            j_target = d.get("j_target", "Ambos")
            if j_target in ("Esquerdo", "Ambos", "Direito"):
                self._j_target_var.set(j_target)

            sound_name = d.get("sound", "GPro Hero")
            if sound_name in SOUND_FILES:
                self._sound_var.set(sound_name)
                _set_sound_file(SOUND_FILES[sound_name])

            accent = d.get("accent")
            dim    = d.get("accent_dim")
            if accent and dim:
                T.apply(accent, dim)

            for attr, name in [
                ("_lc_bind", "lc_bind"),
                ("_rc_bind", "rc_bind"),
                ("_j_bind",  "j_bind"),
                ("_snd_bind","snd_bind"),
            ]:
                s = d.get(name)
                if s:
                    bk = BindKey.from_str(s)
                    if bk.is_set:
                        getattr(self, attr).load_bind(bk)

            self._lc.set_cps(d.get("lc_cps", 10))
            self._rc.set_cps(d.get("rc_cps", 10))
        except Exception:
            pass

    def _on_close(self):
        """Fechar janela → minimiza para a bandeja do sistema."""
        self._save()
        if PYSTRAY_OK:
            self.withdraw()
            self._start_tray()
        else:
            self.iconify()

    def _start_tray(self):
        if self._tray_thread is not None and self._tray_thread.is_alive():
            return

        def _make_img():
            if PIL_AVAILABLE and os.path.exists(LOGO_PATH):
                try:
                    return Image.open(LOGO_PATH).convert("RGBA").resize(
                        (64, 64), Image.LANCZOS)
                except Exception:
                    pass
            # Fallback: círculo colorido
            from PIL import Image as _Img, ImageDraw
            img = _Img.new("RGBA", (64, 64), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse([4, 4, 60, 60], fill=(204, 34, 34, 255))
            return img

        def _run():
            if not PYSTRAY_OK:
                return
            menu = pystray.Menu(
                pystray.MenuItem("Mostrar Zeno", self._show_window, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", self._real_quit),
            )
            self._tray = pystray.Icon("Zeno", _make_img(), "Zeno AutoClicker", menu)
            self._tray.run()
            self._tray = None

        self._tray_thread = threading.Thread(target=_run, daemon=True)
        self._tray_thread.start()

    def _show_window(self, icon=None, item=None):
        if self._tray is not None:
            self._tray.stop()
        self.after(0, self.deiconify)
        self.after(100, self.lift)
        self.after(100, self.focus_force)

    def _real_quit(self, icon=None, item=None):
        if self._tray is not None:
            self._tray.stop()
        self._save()
        self._lc.stop()
        self._rc.stop()
        self.after(0, self.destroy)
        sys.exit(0)

    def _quit(self):
        self._real_quit()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
