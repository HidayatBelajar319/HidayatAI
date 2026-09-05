"""Floating gold orb + mini chat popup for Ultron Jarvis.

This module provides:

* ``UltronSphere``  - a reusable, animated gold sphere drawn with QPainter.
  It is used both for the main-window dashboard centrepiece and for the small
  floating corner orb.
* ``FloatingOrb``   - a frameless, always-on-top 64px orb pinned to the
  bottom-right corner of the screen. Left-click opens the mini chat popup;
  right-click opens a small menu (open the main window / quit).
* ``MiniChatPopup`` - a compact chat panel (message list + input + send)
  that wires into the same backend entry point the main chat uses.
* ``FloatingOrbController`` - ties the orb, popup and backend together.

English code/comments only. Gold/amber palette, never red.
"""

from __future__ import annotations

import random
from typing import Callable, Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QAction, QBrush, QColor, QMouseEvent, QPainter, QPen,
    QRadialGradient, QScreen,
)
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton,
    QSizePolicy, QTextBrowser, QVBoxLayout, QWidget,
)

# Shared gold palette (matches the app accent, amber not red).
GOLD_CORE   = QColor(255, 244, 200)   # bright warm highlight
GOLD_MID    = QColor(255, 214, 90)    # rich gold
GOLD_MAIN   = QColor(255, 179, 0)     # primary app accent
GOLD_DEEP   = QColor(150, 96, 6)      # dark amber edge
GOLD_GLOW   = QColor(255, 179, 0)     # outer glow colour


class UltronSphere(QWidget):
    """Animated layered gold sphere with rotating orbit rings.

    The sphere diameter is recomputed on resize to be
    ``min(55% width, 55% height)`` of the widget so it scales nicely on
    laptop screens. A ``QTimer`` drives the animation at roughly 30 fps.
    Call :meth:`set_active` to start/stop the timer (e.g. when the tab that
    hosts the sphere is hidden) to keep CPU usage low.
    """

    def __init__(self, parent: QWidget | None = None, *, fixed_diameter: int = 0):
        super().__init__(parent)
        # No automatic background fill: when this is a child widget the
        # parent's animated background shows through; when hosted inside the
        # floating orb the orb's translucent top-level window handles it.
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # A fixed diameter (used by the small floating orb) overrides the
        # responsive sizing used in the main window.
        self._fixed_diameter = int(fixed_diameter)

        self._tick = 0
        self._ring1_angle = 0.0
        self._ring2_angle = 0.0
        self._pulse = 0.0
        self._pulse_dir = 1

        # Slow-drifting background particles (subtle, on near-black).
        self._particles: list[list[float]] = []
        self._seed_particles()

        # ~30 fps animation.
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._timer.setInterval(33)
        self._timer.start()

    # ------------------------------------------------------------------ #
    # Lifecycle / animation control
    # ------------------------------------------------------------------ #
    def set_active(self, active: bool) -> None:
        """Start or stop the animation timer (used to save CPU when hidden)."""
        if active and not self._timer.isActive():
            self._timer.start()
        elif not active and self._timer.isActive():
            self._timer.stop()

    def is_active(self) -> bool:
        return self._timer.isActive()

    def _seed_particles(self) -> None:
        self._particles = []
        count = 26
        for _ in range(count):
            self._particles.append([
                random.uniform(0.0, 1.0),   # x (relative)
                random.uniform(0.0, 1.0),   # y (relative)
                random.uniform(0.001, 0.003),  # drift speed
                random.uniform(0.0, 360.0),    # phase
                random.uniform(0.7, 1.6),      # size
                random.uniform(0.10, 0.28),    # alpha
            ])

    def _step(self) -> None:
        self._tick += 1
        self._ring1_angle = (self._ring1_angle + 1.1) % 360.0
        self._ring2_angle = (self._ring2_angle - 0.8) % 360.0
        self._pulse += 0.02 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse_dir = 1

        # Drift particles slowly upward, wrap around.
        for p in self._particles:
            p[1] -= p[2]
            if p[1] < -0.05:
                p[1] = 1.05
                p[0] = random.uniform(0.0, 1.0)

        self.update()

    # ------------------------------------------------------------------ #
    # Geometry
    # ------------------------------------------------------------------ #
    def _diameter(self) -> float:
        if self._fixed_diameter > 0:
            return float(self._fixed_diameter)
        side = min(self.width(), self.height())
        return max(40.0, side * 0.55)

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        # Re-seed relative particle positions on resize is unnecessary; the
        # relative coords already adapt. Just repaint.
        self.update()

    # ------------------------------------------------------------------ #
    # Painting
    # ------------------------------------------------------------------ #
    def paintEvent(self, a0) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        d = self._diameter()
        r = d / 2.0

        # ---- 0. Subtle background particles (near-black) ----
        self._paint_background(painter, w, h)

        # ---- 1. Soft outer glow ----
        glow_radius = r * 1.55
        glow_alpha = int(38 + 20 * self._pulse)
        glow = QRadialGradient(cx, cy, glow_radius)
        glow.setColorAt(0.0, QColor(GOLD_GLOW.red(), GOLD_GLOW.green(), GOLD_GLOW.blue(), glow_alpha))
        glow.setColorAt(0.55, QColor(GOLD_GLOW.red(), GOLD_GLOW.green(), GOLD_GLOW.blue(), int(glow_alpha * 0.35)))
        glow.setColorAt(1.0, QColor(GOLD_GLOW.red(), GOLD_GLOW.green(), GOLD_GLOW.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QPointF(cx, cy), glow_radius, glow_radius)

        # ---- 2. Orbit rings (drawn behind the core) ----
        self._paint_rings(painter, cx, cy, r)

        # ---- 3. Layered gold sphere core ----
        # Base radial gradient: bright top-left highlight -> rich gold -> dark
        # amber edge for a convincing 3D ball.
        grad = QRadialGradient(cx - r * 0.35, cy - r * 0.35, r * 1.15)
        grad.setColorAt(0.0, GOLD_CORE)
        grad.setColorAt(0.35, GOLD_MID)
        grad.setColorAt(0.72, GOLD_MAIN)
        grad.setColorAt(1.0, GOLD_DEEP)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Inner rim light for a metallic edge.
        rim_pen = QPen(QColor(255, 236, 160, int(120 + 40 * self._pulse)), max(1.0, r * 0.03))
        painter.setPen(rim_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r * 0.97, r * 0.97)

        # Specular highlight (small bright blob top-left).
        hl_r = r * 0.42
        hl = QRadialGradient(cx - r * 0.38, cy - r * 0.42, hl_r)
        hl.setColorAt(0.0, QColor(255, 250, 225, 210))
        hl.setColorAt(0.5, QColor(255, 250, 225, 70))
        hl.setColorAt(1.0, QColor(255, 250, 225, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(hl))
        painter.drawEllipse(QPointF(cx - r * 0.38, cy - r * 0.42), hl_r, hl_r * 0.9)

        # A faint concentric energy ring just inside the edge.
        inner_pen = QPen(QColor(255, 214, 90, int(70 + 30 * self._pulse)), max(0.6, r * 0.015))
        inner_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(inner_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r * 0.82, r * 0.82)

        painter.end()

    def _paint_background(self, painter: QPainter, w: int, h: int) -> None:
        # Faint vignette so the orb area reads as near-black, keeping it
        # subtle so surrounding text stays readable.
        painter.fillRect(QRectF(0, 0, w, h), QColor(0, 0, 0, 0))
        for p in self._particles:
            px = p[0] * w
            py = p[1] * h
            size = p[4]
            alpha = int(p[5] * 255)
            colour = QColor(GOLD_MAIN.red(), GOLD_MAIN.green(), GOLD_MAIN.blue(), alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(colour))
            painter.drawEllipse(QPointF(px, py), size, size)

    def _paint_rings(self, painter: QPainter, cx: float, cy: float, r: float) -> None:
        # Ring 1: horizontal orbit ring (tilted for a 3D look).
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-18.0)
        pen1 = QPen(QColor(255, 214, 90, int(150 + 60 * self._pulse)), max(1.0, r * 0.025))
        pen1.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen1)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(-r * 1.18, -r * 0.34, r * 2.36, r * 0.68))
        painter.restore()

        # Ring 2: a thinner counter-rotating arc that sweeps around the orb.
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._ring2_angle)
        pen2 = QPen(QColor(255, 236, 160, 170), max(0.8, r * 0.02))
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect2 = QRectF(-r * 1.28, -r * 1.28, r * 2.56, r * 2.56)
        painter.drawArc(rect2, int(self._ring1_angle * 16), int(95 * 16))
        painter.restore()


class FloatingOrb(QWidget):
    """Frameless, always-on-top 64px gold orb pinned to a screen corner.

    Left-click opens the mini chat popup (without showing the main window).
    Right-click opens a small menu with options to open the main window or
    quit the app.
    """

    # Callbacks wired by the controller.
    on_open_popup: Optional[Callable[[], None]] = None
    on_open_main: Optional[Callable[[], None]] = None
    on_quit: Optional[Callable[[], None]] = None

    def __init__(self, *, size: int = 64, corner_offset: int = 24):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(size, size)
        self.setToolTip("Ultron Jarvis")

        self._size = int(size)
        self._corner_offset = int(corner_offset)

        # The sphere widget fills the orb window.
        self._sphere = UltronSphere(self, fixed_diameter=self._size)
        self._sphere.setGeometry(0, 0, self._size, self._size)

        self._position_bottom_right()

    def _position_bottom_right(self) -> None:
        screen = QApplication_screen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self._size - self._corner_offset
        y = geo.bottom() - self._size - self._corner_offset
        self.move(x, y)

    def show_orb(self) -> None:
        self._position_bottom_right()
        self.show()
        self.raise_()

    # ------------------------------------------------------------------ #
    # Mouse handling
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0 is not None and a0.button() == Qt.MouseButton.RightButton:
            self._show_menu(a0.globalPosition().toPoint())
            a0.accept()
            return
        super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0 is not None and a0.button() == Qt.MouseButton.LeftButton:
            if self.on_open_popup:
                self.on_open_popup()
            a0.accept()
            return
        super().mouseReleaseEvent(a0)

    def _show_menu(self, global_pos) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(8, 8, 8, 245);
                color: #ffffff;
                border: 1px solid rgba(255, 179, 0, 0.25);
                border-radius: 10px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 18px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: rgba(255, 179, 0, 0.18);
            }
        """)
        open_main = QAction("Open Main Window", self)
        quit_action = QAction("Quit", self)
        menu.addAction(open_main)
        menu.addAction(quit_action)
        open_main.triggered.connect(self._menu_open_main)
        quit_action.triggered.connect(self._menu_quit)
        menu.exec(global_pos)

    def _menu_open_main(self):
        if self.on_open_main:
            self.on_open_main()

    def _menu_quit(self):
        if self.on_quit:
            self.on_quit()


class MiniChatPopup(QWidget):
    """Compact always-on-top chat panel used by the floating orb.

    Sending is delegated to a callback (the same backend the main chat uses)
    via :attr:`on_send`. Replies are appended externally by the controller
    through :meth:`append_assistant` / :meth:`append_error`.
    """

    on_send: Optional[Callable[[str], None]] = None

    def __init__(self, *, width: int = 340, height: int = 460):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(width, height)

        self._thinking = False
        # Pending messages as (kind, text) pairs; kind in {"user","assistant","error"}.
        self._entries: list[tuple[str, str]] = []

        self._build_ui()

        # Escape closes the popup.
        from PyQt6.QtGui import QKeySequence, QShortcut
        sc = QShortcut(QKeySequence("Escape"), self)
        sc.activated.connect(self.hide)

    def _build_ui(self) -> None:
        outer = QFrame(self)
        outer.setGeometry(self.rect())
        outer.setStyleSheet("""
            QFrame {
                background: rgba(10, 12, 16, 245);
                border: 1px solid rgba(255, 179, 0, 0.30);
                border-radius: 14px;
            }
        """)
        lay = QVBoxLayout(outer)
        lay.setContentsMargins(12, 10, 12, 12)
        lay.setSpacing(8)

        # Header row.
        header = QHBoxLayout()
        title = QLabel("Ultron Jarvis")
        title.setStyleSheet("color: #ffb300; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #ffffff; border: none;
                font-size: 16px; border-radius: 11px;
            }
            QPushButton:hover { background: rgba(255, 179, 0, 0.20); color: #ffb300; }
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        lay.addLayout(header)

        # Message list.
        self._messages = QTextBrowser()
        self._messages.setOpenExternalLinks(False)
        self._messages.setStyleSheet("""
            QTextBrowser {
                background: rgba(0, 0, 0, 60);
                border: 1px solid rgba(255, 179, 0, 0.12);
                border-radius: 10px;
                color: #f4f6f8;
                font-size: 12px;
                padding: 8px;
            }
        """)
        lay.addWidget(self._messages, stretch=1)

        # Input row.
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask Ultron Jarvis...")
        self._input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 179, 0, 0.20);
                border-radius: 8px;
                color: #ffffff;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid rgba(255, 179, 0, 0.60); }
        """)
        self._input.returnPressed.connect(self._send)
        input_row.addWidget(self._input, stretch=1)

        send_btn = QPushButton("Send")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 179, 0, 0.18);
                color: #ffb300; border: 1px solid rgba(255, 179, 0, 0.40);
                border-radius: 8px; padding: 6px 12px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background: rgba(255, 179, 0, 0.30); }
        """)
        send_btn.clicked.connect(self._send)
        input_row.addWidget(send_btn)
        lay.addLayout(input_row)

    # ------------------------------------------------------------------ #
    # API used by the controller
    # ------------------------------------------------------------------ #
    def _send(self) -> None:
        text = self._input.text().strip()
        if not text or self._thinking:
            return
        self._input.clear()
        self.append_user(text)
        if self.on_send:
            self.on_send(text)

    def append_user(self, text: str) -> None:
        self._entries.append(("user", text))
        self._render()

    def append_assistant(self, text: str) -> None:
        self._thinking = False
        self._entries.append(("assistant", text))
        self._render()

    def append_error(self, text: str) -> None:
        self._thinking = False
        self._entries.append(("error", text))
        self._render()

    def set_thinking(self, thinking: bool) -> None:
        if thinking == self._thinking:
            return
        self._thinking = thinking
        self._render()

    def _render(self) -> None:
        self._messages.clear()
        for kind, text in self._entries:
            if kind == "user":
                self._messages.append(f'<div style="color:#c5cad2;">You: {_esc(text)}</div>')
            elif kind == "assistant":
                self._messages.append(f'<div style="color:#f4f6f8;"><b style="color:#ffb300;">Ultron Jarvis:</b> {_esc(text)}</div>')
            elif kind == "error":
                self._messages.append(f'<div style="color:#ff6b5e;">Error: {_esc(text)}</div>')
        if self._thinking:
            self._messages.append('<div style="color:#8e949d; font-style:italic;">thinking...</div>')
        sb = self._messages.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def show_near(self, orb: QWidget) -> None:
        geo = orb.geometry()
        screen = QApplication_screen()
        if screen is not None:
            sgeo = screen.availableGeometry()
            x = geo.left() - self.width() - 12
            if x < sgeo.left() + 8:
                x = geo.right() + 12
            y = geo.bottom() - self.height()
            y = max(sgeo.top() + 8, min(y, sgeo.bottom() - self.height() - 8))
            self.move(x, y)
        else:
            self.move(geo.left() - self.width() - 12, geo.bottom() - self.height())
        self.show()
        self.raise_()
        self._input.setFocus()


def _esc(text: str) -> str:
    import html as _html
    return _html.escape(str(text))


def QApplication_screen() -> QScreen | None:
    """Return the primary screen's available geometry helper."""
    app = QApplication.instance()
    if app is None:
        return None
    return app.primaryScreen()  # type: ignore[attr-defined]


class FloatingOrbController:
    """Wires the floating orb + popup to the existing chat backend.

    The controller is created by the UI layer with a reference to the
    ``MainWindow`` (or anything exposing ``submit_command`` and ``_log_sig``).
    It reuses the single command entry point so no AI-client logic is
    duplicated.
    """

    def __init__(self, window, *, enabled: bool = True):
        self._window = window
        self._enabled = bool(enabled)

        self.orb = FloatingOrb()
        self.popup = MiniChatPopup()

        self.orb.on_open_popup = self._open_popup
        self.orb.on_open_main = self._open_main
        self.orb.on_quit = self._quit

        self.popup.on_send = self._send

        if self._enabled:
            # Capture replies routed back through the shared log signal.
            try:
                window._log_sig.connect(self._on_log)
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    def show(self) -> None:
        if self._enabled:
            self.orb.show_orb()

    def hide(self) -> None:
        self.orb.hide()
        self.popup.hide()

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.show()
        else:
            self.hide()

    # ------------------------------------------------------------------ #
    def _open_popup(self) -> None:
        self.popup.show_near(self.orb)

    def _open_main(self) -> None:
        self.popup.hide()
        win = self._window
        try:
            win.showNormal()
        except Exception:
            win.show()
        win.raise_()
        win.activateWindow()

    def _quit(self) -> None:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _send(self, text: str) -> None:
        self.popup.set_thinking(True)
        submit = getattr(self._window, "submit_command", None)
        if submit is None:
            self.popup.set_thinking(False)
            self.popup.append_error("Chat backend unavailable.")
            return
        try:
            submit(text)
        except Exception as exc:
            self.popup.set_thinking(False)
            self.popup.append_error(str(exc))

    # ------------------------------------------------------------------ #
    def _on_log(self, text: str) -> None:
        raw = (text or "").strip()
        low = raw.lower()
        if low.startswith("ultron jarvis:"):
            reply = raw.split(":", 1)[1].strip()
            self.popup.append_assistant(reply)
        elif low.startswith("err:"):
            err = raw.split(":", 1)[1].strip()
            self.popup.append_error(err)
