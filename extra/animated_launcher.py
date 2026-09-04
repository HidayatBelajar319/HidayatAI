import re

file_path = r'd:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Find and replace the FloatingLauncher class __init__ and paintEvent
old_init = '''class FloatingLauncher(QWidget):
    single_clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    action_requested = pyqtSignal(str)
    position_changed = pyqtSignal(int, int)

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(74, 74)
        self._state = "idle"
        self._status_line = "Ready"
        self._hovered = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._ring = QFrame()
        self._ring.setStyleSheet("")
        lay = QVBoxLayout(self._ring)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(0)

        lay.addWidget(_framed_logo(54, 36, bg="rgba(255,255,255,0.04)", border=C.BORDER, radius=26, inset=6))
        root.addWidget(self._ring)
        _attach_pulse_glow(self._ring, color=C.WHITE, blur_min=18.0, blur_max=34.0, alpha=135, period_ms=2300)

        self._single_timer = QTimer(self)
        self._single_timer.setSingleShot(True)
        self._single_timer.timeout.connect(self.single_clicked.emit)
        self._dragging = False
        self._drag_button = None
        self._drag_offset = QPoint(0, 0)
        self._press_pos = QPoint(0, 0)
        self._apply_state_style()'''

new_init = '''class FloatingLauncher(QWidget):
    single_clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    action_requested = pyqtSignal(str)
    position_changed = pyqtSignal(int, int)

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(82, 82)
        self._state = "idle"
        self._status_line = "Ready"
        self._hovered = False

        # Animation state
        self._anim_angle = 0.0
        self._breath_val = 0.0
        self._breath_dir = 1
        self._particle_angles = [i * 72.0 for i in range(5)]

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        self._anim_timer.start(30)  # ~33fps

        self._single_timer = QTimer(self)
        self._single_timer.setSingleShot(True)
        self._single_timer.timeout.connect(self.single_clicked.emit)
        self._dragging = False
        self._drag_button = None
        self._drag_offset = QPoint(0, 0)
        self._press_pos = QPoint(0, 0)
        self._apply_state_style()

    def _anim_tick(self):
        self._anim_angle = (self._anim_angle + 1.8) % 360.0
        self._breath_val += 0.03 * self._breath_dir
        if self._breath_val >= 1.0:
            self._breath_dir = -1
        elif self._breath_val <= 0.0:
            self._breath_dir = 1
        for i in range(len(self._particle_angles)):
            self._particle_angles[i] = (self._particle_angles[i] + 0.6 + i * 0.15) % 360.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0

        accent = self._get_accent_color()
        accent_r, accent_g, accent_b = self._hex_to_rgb(accent)
        breath = self._breath_val

        # 1. Outer glow (breathing)
        glow_alpha = int(30 + breath * 40)
        glow_radius = 38.0 + breath * 4.0
        glow_grad = QRadialGradient(cx, cy, glow_radius)
        glow_grad.setColorAt(0.0, QColor(accent_r, accent_g, accent_b, glow_alpha))
        glow_grad.setColorAt(0.7, QColor(accent_r, accent_g, accent_b, int(glow_alpha * 0.3)))
        glow_grad.setColorAt(1.0, QColor(accent_r, accent_g, accent_b, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow_grad))
        painter.drawEllipse(QPointF(cx, cy), glow_radius, glow_radius)

        # 2. Main dark circle background
        painter.setBrush(QBrush(QColor(6, 6, 12, 245)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 32.0, 32.0)

        # 3. Rotating arc (the cinematic ring)
        arc_pen = QPen(QColor(accent_r, accent_g, accent_b, int(140 + breath * 80)), 2.0)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRectF(cx - 34, cy - 34, 68, 68)
        start_angle = int(self._anim_angle * 16)
        span_angle = int(120 * 16)
        painter.drawArc(arc_rect, start_angle, span_angle)

        # Second arc (opposite side, thinner)
        arc_pen2 = QPen(QColor(accent_r, accent_g, accent_b, int(60 + breath * 40)), 1.2)
        arc_pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen2)
        start_angle2 = int((self._anim_angle + 180) * 16)
        span_angle2 = int(80 * 16)
        painter.drawArc(arc_rect, start_angle2, span_angle2)

        # 4. Inner subtle ring
        inner_pen = QPen(QColor(accent_r, accent_g, accent_b, int(35 + breath * 25)), 0.8)
        painter.setPen(inner_pen)
        painter.drawEllipse(QPointF(cx, cy), 28.0, 28.0)

        # 5. Tiny orbiting particles
        import math
        for i, angle_deg in enumerate(self._particle_angles):
            rad = math.radians(angle_deg)
            orbit_r = 36.0 + (i % 2) * 3.0
            px = cx + math.cos(rad) * orbit_r
            py = cy + math.sin(rad) * orbit_r
            dot_size = 1.5 + (i % 3) * 0.5
            dot_alpha = int(80 + breath * 120)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(accent_r, accent_g, accent_b, dot_alpha)))
            painter.drawEllipse(QPointF(px, py), dot_size, dot_size)

        # 6. Logo text "B" in center
        painter.setPen(QPen(QColor(accent_r, accent_g, accent_b, int(200 + breath * 55))))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(QRectF(cx - 15, cy - 12, 30, 24), Qt.AlignmentFlag.AlignCenter, "B")

        painter.end()

    def _get_accent_color(self):
        return {
            "idle": "#ffaa30",
            "listening": "#4ef0ff",
            "thinking": "#9fd8ff",
            "executing": "#ffb14a",
            "error": "#ff6b6b",
        }.get(self._state, "#ffaa30")

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def enterEvent(self, event):
        self._hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        super().leaveEvent(event)'''

text = text.replace(old_init, new_init)

# Also need to remove the old _apply_state_style since it references self._ring which no longer exists
# Replace it with a simpler version
old_apply = '''    def _apply_state_style(self):
        state = self._state
        accent = {
            "idle": "#00BFFF",
            "listening": "#4ef0ff",
            "thinking": "#9fd8ff",
            "executing": "#ffb14a",
            "error": "#ff6b6b",
        }.get(state, "#00BFFF")
        glow = {
            "idle": "rgba(0,191,255,0.18)",
            "listening": "rgba(78,240,255,0.26)",
            "thinking": "rgba(159,216,255,0.26)",
            "executing": "rgba(255,177,74,0.22)",
            "error": "rgba(255,107,107,0.24)",
        }.get(state, "rgba(0,191,255,0.18)")
        self._ring.setStyleSheet(f\"\"\"
            QFrame {{
                background: rgba(4, 4, 8, 234);
                border: 1px solid {accent};
                border-radius: 37px;
            }}
            QFrame:hover {{
                border: 1px solid {accent};
            }}
        \"\"\")
        self.setToolTip(f"Brahma Echo\\n{self._status_line}")'''

new_apply = '''    def _apply_state_style(self):
        self.setToolTip(f"Brahma Echo\\n{self._status_line}")
        self.update()'''

text = text.replace(old_apply, new_apply)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('SUCCESS: Replaced FloatingLauncher with animated version')
