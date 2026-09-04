import os
import re

file_path = r"d:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

new_setup_overlay = """class SetupOverlay(QWidget):
    done = pyqtSignal(str, str, str)

    def __init__(self, parent=None, defaults: dict | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("SetupOverlay { background: rgba(0, 0, 0, 215); }") # Dark backdrop blur equivalent

        self._defaults = defaults or {}
        self._detected = {"darwin": "mac", "windows": "windows"}.get(_OS.lower(), "linux")
        self._sel_os = self._defaults.get("os_system", self._detected)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)

        self.center_frame = QFrame()
        self.center_frame.setObjectName("SetupCenterFrame")
        self.center_frame.setFixedSize(540, 460)
        self.center_frame.setStyleSheet(\"\"\"
            QFrame#SetupCenterFrame {
                background: rgba(10, 12, 18, 250);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 20px;
            }
        \"\"\")

        try:
            glow = QGraphicsDropShadowEffect(self)
            glow.setBlurRadius(60)
            glow.setColor(QColor(0, 0, 0, 180))
            glow.setOffset(0, 12)
            self.center_frame.setGraphicsEffect(glow)
        except Exception:
            pass

        main_lay.addWidget(self.center_frame, 0, Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget(self.center_frame)
        frame_lay = QVBoxLayout(self.center_frame)
        frame_lay.setContentsMargins(40, 40, 40, 40)
        frame_lay.addWidget(self.stack)

        self._build_step1()
        self._build_step2()
        self._build_step3()
        self._build_step_boot()

        self.stack.setCurrentIndex(0)

    def _header(self, title, subtitle):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        t.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        l.addWidget(t)
        s = QLabel(subtitle)
        s.setFont(QFont("Segoe UI", 11))
        s.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        l.addWidget(s)
        return w

    def _btn(self, text, callback, primary=True):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        if primary:
            btn.setStyleSheet(f\"\"\"
                QPushButton {{
                    background: rgba(255, 170, 48, 0.1);
                    color: #ffaa30;
                    border: 1px solid rgba(255, 170, 48, 0.3);
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 170, 48, 0.15);
                    border: 1px solid rgba(255, 170, 48, 0.6);
                }}
            \"\"\")
        else:
            btn.setStyleSheet(f\"\"\"
                QPushButton {{
                    background: transparent;
                    color: {C.TEXT_DIM};
                    border: none;
                }}
                QPushButton:hover {{ color: {C.WHITE}; }}
            \"\"\")
        btn.clicked.connect(callback)
        return btn

    def _build_step1(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._header("BRAHMA ECHO", "First Time Setup\\nConnect your preferred AI provider to begin."))
        lay.addStretch()
        
        info = QLabel("Estimated time\\n20 seconds")
        info.setFont(QFont("Segoe UI", 9))
        info.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        lay.addWidget(info)
        lay.addSpacing(10)
        
        lay.addWidget(self._btn("Continue →", lambda: self.stack.setCurrentIndex(1)))
        self.stack.addWidget(page)

    def _build_step2(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._header("Primary AI", "Google Gemini"))
        lay.addSpacing(10)
        
        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("sk-************************")
        self._key_input.setFont(QFont("Consolas", 12))
        self._key_input.setFixedHeight(48)
        self._key_input.setStyleSheet(f\"\"\"
            QLineEdit {{
                background: rgba(255,255,255,0.03); color: {C.WHITE};
                border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 0 16px;
            }}
            QLineEdit:focus {{ border: 1px solid rgba(255, 170, 48, 0.4); }}
        \"\"\")
        self._key_input.setText((self._defaults.get("gemini_api_key") or "").strip())
        lay.addWidget(self._key_input)
        
        hint_lay = QHBoxLayout()
        hint = QLabel("Need one? <a href='https://aistudio.google.com/app/apikey' style='color:#ffaa30; text-decoration:none;'>Get API Key →</a>")
        hint.setFont(QFont("Segoe UI", 9))
        hint.setOpenExternalLinks(True)
        hint.setStyleSheet("background: transparent; border: none;")
        hint_lay.addWidget(hint)
        hint_lay.addStretch()
        
        toggle_pw = QPushButton("👁")
        toggle_pw.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_pw.setFixedSize(30, 30)
        toggle_pw.setStyleSheet("background: transparent; border: none; color: #aaa;")
        def _toggle():
            if self._key_input.echoMode() == QLineEdit.EchoMode.Password:
                self._key_input.setEchoMode(QLineEdit.EchoMode.Normal)
                toggle_pw.setStyleSheet("background: transparent; border: none; color: #fff;")
            else:
                self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
                toggle_pw.setStyleSheet("background: transparent; border: none; color: #aaa;")
        toggle_pw.clicked.connect(_toggle)
        hint_lay.addWidget(toggle_pw)
        lay.addLayout(hint_lay)
        
        lay.addStretch()
        
        self._gemini_err = QLabel("")
        self._gemini_err.setStyleSheet(f"color: {C.RED}; background: transparent; border: none;")
        lay.addWidget(self._gemini_err)
        
        nav = QHBoxLayout()
        nav.addWidget(self._btn("Back", lambda: self.stack.setCurrentIndex(0), primary=False))
        nav.addWidget(self._btn("Continue", self._validate_gemini))
        lay.addLayout(nav)
        self.stack.addWidget(page)
        
    def _validate_gemini(self):
        if not self._key_input.text().strip():
            self._gemini_err.setText("Gemini API key is required.")
            return
        self._gemini_err.setText("")
        self.stack.setCurrentIndex(2)

    def _build_step3(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._header("Optional AI & Platform", "OpenRouter and OS settings"))
        lay.addSpacing(10)
        
        lbl = QLabel("OpenRouter API Key")
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        lay.addWidget(lbl)
        
        self._or_input = QLineEdit()
        self._or_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._or_input.setPlaceholderText("sk-or-************************")
        self._or_input.setFont(QFont("Consolas", 11))
        self._or_input.setFixedHeight(44)
        self._or_input.setStyleSheet(f\"\"\"
            QLineEdit {{
                background: rgba(255,255,255,0.03); color: {C.WHITE};
                border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 0 16px;
            }}
            QLineEdit:focus {{ border: 1px solid rgba(255, 170, 48, 0.4); }}
        \"\"\")
        self._or_input.setText((self._defaults.get("openrouter_api_key") or "").strip())
        lay.addWidget(self._or_input)
        
        lay.addSpacing(14)
        lbl2 = QLabel("Choose Platform")
        lbl2.setFont(QFont("Segoe UI", 9))
        lbl2.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        lay.addWidget(lbl2)
        
        os_row = QHBoxLayout()
        self._os_btns = {}
        for key, icon, name in [("windows", "🪟", "Windows"), ("mac", "🍎", "macOS"), ("linux", "🐧", "Linux")]:
            btn = QPushButton(f"{icon} {name}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setFont(QFont("Segoe UI", 10))
            btn.clicked.connect(lambda _, k=key: self._sel(k))
            os_row.addWidget(btn)
            self._os_btns[key] = btn
        lay.addLayout(os_row)
        self._sel(self._sel_os)
        
        lay.addStretch()
        nav = QHBoxLayout()
        nav.addWidget(self._btn("Back", lambda: self.stack.setCurrentIndex(1), primary=False))
        nav.addWidget(self._btn("Finish", self._start_boot_sequence))
        lay.addLayout(nav)
        self.stack.addWidget(page)
        
    def _sel(self, key: str):
        self._sel_os = key
        for k, btn in self._os_btns.items():
            if k == key:
                btn.setStyleSheet(f\"\"\"
                    QPushButton {{
                        background: rgba(255, 170, 48, 0.12); color: #ffaa30;
                        border: 1px solid rgba(255, 170, 48, 0.4); border-radius: 10px; font-weight: bold;
                    }}
                \"\"\")
            else:
                btn.setStyleSheet(f\"\"\"
                    QPushButton {{
                        background: rgba(255, 255, 255, 0.02); color: {C.TEXT_DIM};
                        border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px;
                    }}
                    QPushButton:hover {{ background: rgba(255, 255, 255, 0.05); color: {C.WHITE}; }}
                \"\"\")

    def _build_step_boot(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        
        lay.addStretch()
        self._boot_lbl = QLabel("██████████░░  Loading Core")
        self._boot_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._boot_lbl.setFont(QFont("Consolas", 14))
        self._boot_lbl.setStyleSheet(f"color: #ffaa30; background: transparent; border: none;")
        lay.addWidget(self._boot_lbl)
        lay.addStretch()
        self.stack.addWidget(page)
        
    def _start_boot_sequence(self):
        self.stack.setCurrentIndex(3)
        # Attempt to accelerate background if parent has access
        try:
            if hasattr(self.parentWidget(), "parentWidget"):
                mw = self.parentWidget().parentWidget()
                if hasattr(mw, "_background"):
                    mw._background.page().runJavaScript("if (window.accelerateReactor) window.accelerateReactor();")
        except Exception:
            pass
            
        self._boot_step = 0
        self._boot_timer = QTimer(self)
        self._boot_timer.timeout.connect(self._boot_tick)
        self._boot_timer.start(700)
        
    def _boot_tick(self):
        steps = [
            "██████████░░  Loading Core",
            "████████████  Verifying Gemini",
            "████████████  Initializing Memory",
            "████████████  Starting Voice Engine",
            "████████████  Launching Brahma Echo"
        ]
        self._boot_step += 1
        if self._boot_step < len(steps):
            self._boot_lbl.setText(steps[self._boot_step])
        else:
            self._boot_timer.stop()
            self.done.emit(self._key_input.text().strip(), self._or_input.text().strip(), self._sel_os)
"""

# Replace SetupOverlay class
pattern_setup = r"class SetupOverlay\(QWidget\):.*?def _submit\(self\):.*?self\.done\.emit\(key, or_key, self\._sel_os\)"
text = re.sub(pattern_setup, new_setup_overlay, text, flags=re.DOTALL)

# Update _show_setup in BrahmaUI to make overlay full screen
new_show_setup = """    def _show_setup(self, defaults: dict | None = None):
        if self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
        ov = SetupOverlay(self.centralWidget(), defaults=defaults or self._load_api_defaults())
        cw = self.centralWidget()
        ov.setGeometry(0, 0, cw.width(), cw.height()) # Full screen to cover and blur everything
        ov.done.connect(self._on_setup_done)
        ov.show()
        ov.raise_()
        ov.activateWindow()
        self._overlay = ov"""

pattern_show = r"    def _show_setup\(self, defaults: dict \| None = None\):.*?self\._overlay = ov"
text = re.sub(pattern_show, new_show_setup, text, flags=re.DOTALL)

# Handle window resize to keep overlay full screen
new_resize = """    def resizeEvent(self, event):
        super().resizeEvent(event)
        cw = self.centralWidget()
        if cw:
            if self._web_view:
                self._web_view.setGeometry(cw.rect())
            if self._overlay:
                self._overlay.setGeometry(cw.rect())"""

# Check if resizeEvent already handles overlay, if not, update it
if "if self._overlay:" not in text:
    pattern_resize = r"    def resizeEvent\(self, event\):.*?self\._web_view\.setGeometry\(cw\.rect\(\)\)"
    text = re.sub(pattern_resize, new_resize, text, flags=re.DOTALL)
else:
    # already there, just ensure it sets geometry to cw.rect()
    text = re.sub(r"if self\._overlay:.*?self\._overlay\.setGeometry\(.*?\)", "if self._overlay:\n                self._overlay.setGeometry(cw.rect())", text, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Updated SetupOverlay and _show_setup")
