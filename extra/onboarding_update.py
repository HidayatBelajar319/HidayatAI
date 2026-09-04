import re

file_path = r'd:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# ─────────────────────────────────────────────────────────────────
# 1. ONBOARDING: Add OpenRouter prompt after Gemini auth
# ─────────────────────────────────────────────────────────────────

# Replace the line that goes directly to _show_intro after auth
old_auth_end = "            QTimer.singleShot(1800, self._show_intro)"
new_auth_end = "            QTimer.singleShot(1800, self._show_or_prompt)"
text = text.replace(old_auth_end, new_auth_end)

# Insert the OpenRouter prompt method + OR input page right before _show_intro
or_prompt_code = '''
    def _show_or_prompt(self):
        """After Gemini verified, ask if user wants to add OpenRouter too."""
        self._s3_box.hide()
        page = self._stack.widget(2)
        lay = page.layout()

        self._or_prompt_widget = QFrame()
        self._or_prompt_widget.setFixedSize(460, 200)
        self._or_prompt_widget.setStyleSheet("""
            QFrame {
                background: rgba(8, 10, 16, 220);
                border: 1px solid rgba(255, 170, 48, 0.15);
                border-radius: 20px;
            }
        """)
        prom_lay = QVBoxLayout(self._or_prompt_widget)
        prom_lay.setContentsMargins(32, 28, 32, 24)
        prom_lay.setSpacing(8)

        q_title = QLabel("Secondary Intelligence")
        q_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        q_title.setStyleSheet("color: #ffffff; background: transparent; border: none;")
        prom_lay.addWidget(q_title)

        q_sub = QLabel("Would you like to configure OpenRouter as well?\\nThis is optional and can be done later in Settings.")
        q_sub.setFont(QFont("Segoe UI", 10))
        q_sub.setWordWrap(True)
        q_sub.setStyleSheet("color: rgba(255,255,255,0.4); background: transparent; border: none;")
        prom_lay.addWidget(q_sub)

        prom_lay.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        skip_btn = QPushButton("Skip")
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        skip_btn.setFixedHeight(42)
        skip_btn.setFont(QFont("Segoe UI", 11))
        skip_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255,255,255,0.4);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 0 24px;
            }
            QPushButton:hover {
                color: rgba(255,255,255,0.7);
                border: 1px solid rgba(255,255,255,0.25);
            }
        """)
        skip_btn.clicked.connect(self._skip_or)
        btn_row.addWidget(skip_btn)

        yes_btn = QPushButton("Configure OpenRouter")
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setFixedHeight(42)
        yes_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        yes_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 170, 48, 0.1);
                color: #ffaa30;
                border: 1px solid rgba(255, 170, 48, 0.35);
                border-radius: 12px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background: rgba(255, 170, 48, 0.2);
                border: 1px solid rgba(255, 170, 48, 0.6);
            }
        """)
        yes_btn.clicked.connect(self._show_or_input)
        btn_row.addWidget(yes_btn)

        prom_lay.addLayout(btn_row)

        lay.insertWidget(lay.count() - 1, self._or_prompt_widget, 0, Qt.AlignmentFlag.AlignCenter)

    def _skip_or(self):
        """User chose to skip OpenRouter, go straight to intro."""
        self._or_key_value = ""
        self._or_prompt_widget.hide()
        self._show_intro_final()

    def _show_or_input(self):
        """User wants to add OpenRouter."""
        self._or_prompt_widget.hide()
        page = self._stack.widget(2)
        lay = page.layout()

        self._or_box = QFrame()
        self._or_box.setFixedSize(480, 230)
        self._or_box.setStyleSheet("""
            QFrame {
                background: rgba(8, 10, 16, 220);
                border: 1px solid rgba(255, 170, 48, 0.2);
                border-radius: 20px;
            }
        """)
        or_blay = QVBoxLayout(self._or_box)
        or_blay.setContentsMargins(32, 28, 32, 28)
        or_blay.setSpacing(6)

        or_title = QLabel("OpenRouter")
        or_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        or_title.setStyleSheet("color: rgba(255,255,255,0.8); background: transparent; border: none;")
        or_blay.addWidget(or_title)

        or_sub = QLabel("Paste your OpenRouter API Key")
        or_sub.setFont(QFont("Segoe UI", 10))
        or_sub.setStyleSheet("color: rgba(255,255,255,0.4); background: transparent; border: none;")
        or_blay.addWidget(or_sub)

        or_blay.addSpacing(12)

        self._or_input = QLineEdit()
        self._or_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._or_input.setPlaceholderText("sk-or-************************")
        self._or_input.setFont(QFont("Consolas", 12))
        self._or_input.setFixedHeight(48)
        self._or_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.03);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 0 16px;
                letter-spacing: 1px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 170, 48, 0.5);
            }
        """)
        self._or_input.setText((self._defaults.get("openrouter_api_key") or "").strip())
        or_blay.addWidget(self._or_input)

        or_blay.addStretch()

        or_btn_row = QHBoxLayout()
        or_skip = QPushButton("Skip")
        or_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        or_skip.setFixedHeight(42)
        or_skip.setFont(QFont("Segoe UI", 11))
        or_skip.setStyleSheet("""
            QPushButton { background: transparent; color: rgba(255,255,255,0.4); border: none; }
            QPushButton:hover { color: rgba(255,255,255,0.7); }
        """)
        or_skip.clicked.connect(self._skip_or)
        or_btn_row.addWidget(or_skip)

        or_save = QPushButton("Save & Continue")
        or_save.setCursor(Qt.CursorShape.PointingHandCursor)
        or_save.setFixedHeight(42)
        or_save.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        or_save.setStyleSheet("""
            QPushButton {
                background: rgba(255, 170, 48, 0.1);
                color: #ffaa30;
                border: 1px solid rgba(255, 170, 48, 0.35);
                border-radius: 12px;
                padding: 0 24px;
            }
            QPushButton:hover {
                background: rgba(255, 170, 48, 0.2);
                border: 1px solid rgba(255, 170, 48, 0.6);
            }
        """)
        or_save.clicked.connect(self._save_or_key)
        or_btn_row.addWidget(or_save)

        or_blay.addLayout(or_btn_row)

        lay.insertWidget(lay.count() - 1, self._or_box, 0, Qt.AlignmentFlag.AlignCenter)

    def _save_or_key(self):
        self._or_key_value = self._or_input.text().strip()
        self._or_box.hide()
        self._show_intro_final()

    def _show_intro_final(self):
        """Show the Brahma Echo intro sequence."""
        page = self._stack.widget(2)
        lay = page.layout()
        self._intro_widget.setParent(None)
        lay.insertWidget(lay.count() - 1, self._intro_widget, 0, Qt.AlignmentFlag.AlignCenter)
        self._intro_widget.show()
        self._intro_reveal_idx = 0
        self._intro_timer = QTimer(self)
        self._intro_timer.timeout.connect(self._intro_tick)
        self._intro_timer.start(600)

'''

# Insert before _show_intro
text = text.replace("    def _show_intro(self):", or_prompt_code + "    def _show_intro(self):")

# Update done.emit to include the OR key
old_emit = 'QTimer.singleShot(1200, lambda: self.done.emit(self._key_input.text().strip(), "", self._sel_os))'
new_emit = 'QTimer.singleShot(1200, lambda: self.done.emit(self._key_input.text().strip(), getattr(self, "_or_key_value", ""), self._sel_os))'
text = text.replace(old_emit, new_emit)

# ─────────────────────────────────────────────────────────────────
# 2. SETTINGS TAB: Update _provider_row to show "Already Added"
# ─────────────────────────────────────────────────────────────────

old_provider_row = '''    def _provider_row(self, name: str, key: str, model: str, setting_key: str):
        row = QFrame()
        row.setStyleSheet("QFrame { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 14px; } QFrame:hover { background: rgba(255, 170, 48, 0.04); border: 1px solid rgba(255, 170, 48, 0.3); }")
        r = QHBoxLayout(row)
        r.setContentsMargins(14, 12, 14, 12)
        r.setSpacing(12)
        icon = QLabel(name[:1].upper())
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        icon.setStyleSheet(f"background: rgba(255, 170, 48,0.12); color: {C.WHITE}; border: 1px solid rgba(255, 170, 48,0.38); border-radius: 21px;")
        r.addWidget(icon)
        meta = QVBoxLayout()
        title = QLabel(name)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.WHITE}; border: none;")
        status = QLabel("Connected" if key else "Not connected")
        status.setStyleSheet(f"color: {C.GREEN if key else C.PRI}; border: none;")
        model_lbl = QLabel(f"Current model: {model}")
        model_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; border: none;")
        api_lbl = QLabel(self._provider_key_preview(key))
        api_lbl.setStyleSheet(f"color: {C.TEXT_MED}; border: none;")
        meta.addWidget(title)
        meta.addWidget(status)
        meta.addWidget(model_lbl)
        meta.addWidget(api_lbl)
        r.addLayout(meta, 1)
        btn_lay = QVBoxLayout()
        btn_lay.setSpacing(8)
        edit = QPushButton("Edit API Key")
        edit.clicked.connect(lambda: self._open_api_keys())
        test = QPushButton("Test Connection")
        test.clicked.connect(lambda: self._test_provider(setting_key))
        btn_lay.addWidget(edit)
        btn_lay.addWidget(test)
        r.addLayout(btn_lay)
        return row, status, api_lbl'''

new_provider_row = '''    def _provider_row(self, name: str, key: str, model: str, setting_key: str):
        row = QFrame()
        if key:
            row.setStyleSheet("QFrame { background: rgba(55, 255, 95, 0.02); border: 1px solid rgba(55, 255, 95, 0.1); border-radius: 14px; } QFrame:hover { background: rgba(55, 255, 95, 0.05); border: 1px solid rgba(55, 255, 95, 0.25); }")
        else:
            row.setStyleSheet("QFrame { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 14px; } QFrame:hover { background: rgba(255, 170, 48, 0.04); border: 1px solid rgba(255, 170, 48, 0.3); }")
        r = QHBoxLayout(row)
        r.setContentsMargins(14, 12, 14, 12)
        r.setSpacing(12)
        icon = QLabel(name[:1].upper())
        icon.setFixedSize(42, 42)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        if key:
            icon.setStyleSheet(f"background: rgba(55, 255, 95, 0.12); color: {C.GREEN}; border: 1px solid rgba(55, 255, 95, 0.3); border-radius: 21px;")
        else:
            icon.setStyleSheet(f"background: rgba(255, 170, 48, 0.12); color: {C.WHITE}; border: 1px solid rgba(255, 170, 48, 0.38); border-radius: 21px;")
        r.addWidget(icon)
        meta = QVBoxLayout()
        title = QLabel(name)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.WHITE}; border: none;")
        if key:
            status = QLabel("\\u2713  Already Added")
            status.setStyleSheet(f"color: {C.GREEN}; border: none; font-weight: bold;")
        else:
            status = QLabel("Not configured")
            status.setStyleSheet(f"color: {C.TEXT_DIM}; border: none;")
        model_lbl = QLabel(f"Current model: {model}")
        model_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; border: none;")
        api_lbl = QLabel(self._provider_key_preview(key))
        api_lbl.setStyleSheet(f"color: {C.TEXT_MED}; border: none;")
        meta.addWidget(title)
        meta.addWidget(status)
        meta.addWidget(model_lbl)
        meta.addWidget(api_lbl)
        r.addLayout(meta, 1)
        btn_lay = QVBoxLayout()
        btn_lay.setSpacing(8)
        if key:
            edit = QPushButton("Edit API Key")
        else:
            edit = QPushButton("Add API Key")
            edit.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 170, 48, 0.1);
                    color: #ffaa30;
                    border: 1px solid rgba(255, 170, 48, 0.3);
                    border-radius: 12px;
                    padding: 10px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(255, 170, 48, 0.2);
                    border: 1px solid rgba(255, 170, 48, 0.5);
                }
            """)
        edit.clicked.connect(lambda: self._open_api_keys())
        test = QPushButton("Test Connection")
        test.clicked.connect(lambda: self._test_provider(setting_key))
        btn_lay.addWidget(edit)
        btn_lay.addWidget(test)
        r.addLayout(btn_lay)
        return row, status, api_lbl'''

text = text.replace(old_provider_row, new_provider_row)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('SUCCESS: Added OpenRouter prompt to onboarding + updated settings tab')
