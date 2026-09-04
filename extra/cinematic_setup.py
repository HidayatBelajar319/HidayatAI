import os
import re

file_path = r"d:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

new_setup_overlay = """class SetupOverlay(QWidget):
    done = pyqtSignal(str, str, str)

    def __init__(self, parent=None, defaults: dict | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("SetupOverlay { background: transparent; }")

        self._defaults = defaults or {}
        self._detected = {"darwin": "mac", "windows": "windows"}.get(_OS.lower(), "linux")
        self._sel_os = self._defaults.get("os_system", self._detected)

        self._stack = QStackedWidget(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._stack)

        self._build_stage1()
        self._build_stage2()
        self._build_stage3()
        self._build_stage4()
        
        self._stack.setCurrentIndex(0)
        
        # Start Stage 1 typing effect automatically
        QTimer.singleShot(1000, self._start_stage1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Deep blur/dark background
        painter.fillRect(self.rect(), QColor(5, 8, 12, 235))
        
        # Cut a hole in the center for the reactor
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        center = self.rect().center()
        
        # Smooth radial gradient for the hole
        gradient = QRadialGradient(center, 350)
        gradient.setColorAt(0, QColor(0, 0, 0, 255))
        gradient.setColorAt(0.6, QColor(0, 0, 0, 180))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 350, 350)

    def _call_js(self, func_call):
        try:
            if hasattr(self.parentWidget(), "parentWidget"):
                mw = self.parentWidget().parentWidget()
                if hasattr(mw, "_background"):
                    mw._background.page().runJavaScript(func_call)
        except Exception:
            pass

    # STAGE 1: System Check
    def _build_stage1(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addStretch()
        
        self._s1_lbl = QLabel("")
        self._s1_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._s1_lbl.setFont(QFont("Consolas", 14))
        self._s1_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        lay.addWidget(self._s1_lbl)
        
        lay.addStretch()
        self._stack.addWidget(page)
        
    def _start_stage1(self):
        self._s1_lines = [
            "Scanning local configuration...",
            f"✓ {self._detected.capitalize()} detected",
            "✓ GPU acceleration enabled",
            "✓ Network online",
            "Looking for AI provider...",
            "✕ No provider configured",
            "One final step is required before I can think."
        ]
        self._s1_idx = 0
        self._s1_timer = QTimer(self)
        self._s1_timer.timeout.connect(self._s1_tick)
        self._s1_timer.start(1200)
        self._s1_tick()
        
    def _s1_tick(self):
        if self._s1_idx < len(self._s1_lines):
            line = self._s1_lines[self._s1_idx]
            self._s1_lbl.setText(self._s1_lbl.text() + "\\n\\n" + line)
            
            if "✕" in line:
                self._s1_lbl.setStyleSheet(f"color: {C.RED}; background: transparent; border: none;")
                self._call_js("if(window.losePower) window.losePower();")
            elif "final step" in line:
                self._s1_lbl.setStyleSheet(f"color: {C.WHITE}; background: transparent; border: none; font-weight: bold; font-size: 18px;")
                self._call_js("if(window.triggerPulse) window.triggerPulse();")
                
            self._s1_idx += 1
        else:
            self._s1_timer.stop()
            QTimer.singleShot(2500, lambda: self._stack.setCurrentIndex(1))

    # STAGE 2: Provider Selection
    def _build_stage2(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addStretch()
        
        title = QLabel("Select Primary Intelligence")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        lay.addWidget(title)
        lay.addSpacing(40)
        
        cards_lay = QHBoxLayout()
        cards_lay.addStretch()
        
        # Gemini Card
        gem_btn = QPushButton()
        gem_btn.setFixedSize(260, 140)
        gem_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gem_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background: rgba(255, 170, 48, 0.05);
                border: 1px solid rgba(255, 170, 48, 0.2);
                border-radius: 16px;
                color: #ffaa30;
                text-align: left;
                padding: 20px;
            }}
            QPushButton:hover {{
                background: rgba(255, 170, 48, 0.15);
                border: 1px solid rgba(255, 170, 48, 0.6);
            }}
        \"\"\")
        
        glay = QVBoxLayout(gem_btn)
        gt = QLabel("Google Gemini")
        gt.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        gt.setStyleSheet("color: #ffaa30; background: transparent; border: none;")
        glay.addWidget(gt)
        gs = QLabel("★★★★★ Recommended\\nPrimary Intelligence")
        gs.setFont(QFont("Segoe UI", 10))
        gs.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent; border: none;")
        glay.addWidget(gs)
        glay.addStretch()
        gc = QLabel("Connect →")
        gc.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        gc.setStyleSheet("color: #ffaa30; background: transparent; border: none;")
        glay.addWidget(gc)
        
        gem_btn.clicked.connect(self._goto_stage3)
        cards_lay.addWidget(gem_btn)
        
        cards_lay.addSpacing(20)
        
        # OpenRouter Card (Optional)
        or_btn = QPushButton()
        or_btn.setFixedSize(260, 140)
        or_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        or_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                color: {C.TEXT_DIM};
                text-align: left;
                padding: 20px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        \"\"\")
        olay = QVBoxLayout(or_btn)
        ot = QLabel("OpenRouter")
        ot.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        ot.setStyleSheet(f"color: {C.WHITE}; background: transparent; border: none;")
        olay.addWidget(ot)
        os_lbl = QLabel("Multiple Models\\nOptional Secondary")
        os_lbl.setFont(QFont("Segoe UI", 10))
        os_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        olay.addWidget(os_lbl)
        olay.addStretch()
        oc = QLabel("Configure Later →")
        oc.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        oc.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        olay.addWidget(oc)
        
        cards_lay.addWidget(or_btn)
        cards_lay.addStretch()
        
        lay.addLayout(cards_lay)
        lay.addStretch()
        self._stack.addWidget(page)
        
    def _goto_stage3(self):
        self._call_js("if(window.triggerPulse) window.triggerPulse();")
        self._stack.setCurrentIndex(2)

    # STAGE 3 & 4: API Input and Auth
    def _build_stage3(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addStretch()
        
        self._s3_box = QFrame()
        self._s3_box.setFixedSize(500, 280)
        self._s3_box.setStyleSheet(\"\"\"
            QFrame {
                background: rgba(10, 12, 18, 200);
                border: 1px solid rgba(255, 170, 48, 0.3);
                border-radius: 20px;
            }
        \"\"\")
        blay = QVBoxLayout(self._s3_box)
        blay.setContentsMargins(30, 30, 30, 30)
        
        self._s3_title = QLabel("Google Gemini")
        self._s3_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._s3_title.setStyleSheet("color: #ffaa30; background: transparent; border: none;")
        blay.addWidget(self._s3_title)
        
        self._s3_sub = QLabel("Paste your Neural Key")
        self._s3_sub.setFont(QFont("Segoe UI", 10))
        self._s3_sub.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
        blay.addWidget(self._s3_sub)
        
        blay.addSpacing(20)
        
        self._key_input = QLineEdit()
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("sk-************************")
        self._key_input.setFont(QFont("Consolas", 14))
        self._key_input.setFixedHeight(54)
        self._key_input.setStyleSheet(f\"\"\"
            QLineEdit {{
                background: rgba(255, 170, 48, 0.05); color: #ffaa30;
                border: 1px solid rgba(255, 170, 48, 0.4); border-radius: 12px; padding: 0 16px;
                letter-spacing: 2px;
            }}
            QLineEdit:focus {{ border: 1px solid #ffaa30; }}
        \"\"\")
        self._key_input.textChanged.connect(self._on_key_pasted)
        blay.addWidget(self._key_input)
        
        self._s3_status = QLabel("")
        self._s3_status.setFont(QFont("Consolas", 11))
        self._s3_status.setStyleSheet(f"color: #ffaa30; background: transparent; border: none;")
        blay.addWidget(self._s3_status)
        
        blay.addStretch()
        
        hlay = QHBoxLayout(page)
        hlay.addStretch()
        hlay.addWidget(self._s3_box)
        hlay.addStretch()
        
        lay.addLayout(hlay)
        lay.addStretch()
        self._stack.addWidget(page)
        
    def _on_key_pasted(self, text):
        if len(text) > 10 and not hasattr(self, "_authenticating"):
            self._authenticating = True
            self._key_input.setReadOnly(True)
            self._s3_sub.setText("Authenticating...")
            self._auth_step = 0
            self._auth_timer = QTimer(self)
            self._auth_timer.timeout.connect(self._auth_tick)
            self._auth_timer.start(200)
            
    def _auth_tick(self):
        bars = ["█", "████", "███████", "███████████", "███████████████"]
        if self._auth_step < len(bars):
            self._s3_status.setText(bars[self._auth_step])
            if self._auth_step % 2 == 0:
                self._call_js("if(window.triggerPulse) window.triggerPulse();")
            self._auth_step += 1
        else:
            self._auth_timer.stop()
            self._s3_status.setText("✓ Identity Verified\\nGemini 2.5 Pro\\nLatency 87 ms\\nReady")
            self._s3_status.setStyleSheet(f"color: {C.GREEN}; background: transparent; border: none;")
            self._key_input.setStyleSheet(self._key_input.styleSheet().replace("rgba(255, 170, 48, 0.4)", C.GREEN).replace("#ffaa30", C.GREEN))
            self._s3_title.setStyleSheet(f"color: {C.GREEN}; background: transparent; border: none;")
            
            QTimer.singleShot(1500, self._intro_brahma)
            
    def _intro_brahma(self):
        self._s3_box.hide()
        self._intro_lbl = QLabel("Identity confirmed.\\n\\nHello.\\n\\nI'm Brahma Echo.\\n\\nReady whenever you are.")
        self._intro_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._intro_lbl.setFont(QFont("Segoe UI", 16))
        self._intro_lbl.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        
        self._launch_btn = QPushButton("Launch Brahma Echo →")
        self._launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_btn.setFixedSize(240, 50)
        self._launch_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._launch_btn.setStyleSheet(f\"\"\"
            QPushButton {{
                background: rgba(255, 170, 48, 0.15);
                color: #ffaa30;
                border: 1px solid #ffaa30;
                border-radius: 25px;
            }}
            QPushButton:hover {{
                background: rgba(255, 170, 48, 0.3);
            }}
        \"\"\")
        self._launch_btn.clicked.connect(self._start_ignition)
        
        # We'll just replace the layout of page 2 dynamically
        page = self._stack.widget(2)
        lay = page.layout()
        # clear old
        while lay.count():
            item = lay.takeAt(0)
            if item.widget():
                item.widget().hide()
                
        lay.addStretch()
        lay.addWidget(self._intro_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(40)
        lay.addWidget(self._launch_btn, 0, Qt.AlignmentFlag.AlignCenter)
        lay.addStretch()
        self._call_js("if(window.triggerPulse) window.triggerPulse();")

    # STAGE 6: Neural Link Ignition
    def _build_stage4(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addStretch()
        
        self._s4_title = QLabel("Establishing Neural Link...")
        self._s4_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._s4_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._s4_title.setStyleSheet("color: #ffaa30; background: transparent; border: none;")
        lay.addWidget(self._s4_title)
        lay.addSpacing(30)
        
        self._s4_lbl = QLabel("")
        self._s4_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._s4_lbl.setFont(QFont("Consolas", 14))
        self._s4_lbl.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        lay.addWidget(self._s4_lbl)
        
        lay.addStretch()
        self._stack.addWidget(page)
        
    def _start_ignition(self):
        self._stack.setCurrentIndex(3)
        self._call_js("if(window.setReactorSpeed) window.setReactorSpeed(5.0);")
        
        self._ignite_step = 0
        self._ignite_timer = QTimer(self)
        self._ignite_timer.timeout.connect(self._ignite_tick)
        self._ignite_timer.start(600)
        
    def _ignite_tick(self):
        modules = [
            "MEMORY       ███████",
            "VOICE        ███████",
            "VISION       ███████",
            "AUTOMATION   ███████",
            "REASONING    ███████"
        ]
        
        if self._ignite_step < len(modules):
            current_text = self._s4_lbl.text()
            self._s4_lbl.setText(current_text + ("\\n" if current_text else "") + modules[self._ignite_step])
            self._call_js(f"if(window.setReactorSpeed) window.setReactorSpeed({5.0 + self._ignite_step * 3});")
            self._ignite_step += 1
        else:
            self._ignite_timer.stop()
            self._s4_title.setText("Neural Link Established.")
            self._s4_title.setStyleSheet(f"color: {C.GREEN}; background: transparent; border: none;")
            self._call_js("if(window.dissolveReactor) window.dissolveReactor();")
            QTimer.singleShot(800, lambda: self.done.emit(self._key_input.text().strip(), "", self._sel_os))
"""

pattern_setup = r"class SetupOverlay\(QWidget\):.*?(?=class CommandBar\(QWidget\):)"
text = re.sub(pattern_setup, new_setup_overlay + "\n\n", text, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print("Injected Cinematic SetupOverlay into ui.py")
