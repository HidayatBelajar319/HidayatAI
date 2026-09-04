import os

file_path = r"d:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    (
        "QFrame#SettingsCard {\n                background: rgba(10,11,15,235);\n                border: 1px solid rgba(255, 170, 48,0.18);\n                border-radius: 18px;\n            }",
        "QFrame#SettingsCard {\n                background: rgba(255, 255, 255, 0.02);\n                border: 1px solid rgba(255, 255, 255, 0.06);\n                border-radius: 18px;\n            }"
    ),
    (
        'row.setStyleSheet("QFrame { background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; }")',
        'row.setStyleSheet("QFrame { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 14px; } QFrame:hover { background: rgba(255, 170, 48, 0.04); border: 1px solid rgba(255, 170, 48, 0.3); }")'
    ),
    (
        'title.setStyleSheet(f"color: {C.WHITE};")',
        'title.setStyleSheet(f"color: {C.WHITE}; border: none;")'
    ),
    (
        'status.setStyleSheet(f"color: {C.GREEN if key else C.PRI};")',
        'status.setStyleSheet(f"color: {C.GREEN if key else C.PRI}; border: none;")'
    ),
    (
        'model_lbl.setStyleSheet(f"color: {C.TEXT_DIM};")',
        'model_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; border: none;")'
    ),
    (
        'api_lbl.setStyleSheet(f"color: {C.TEXT_MED};")',
        'api_lbl.setStyleSheet(f"color: {C.TEXT_MED}; border: none;")'
    ),
    (
        "QPushButton:hover {\n                background: rgba(255, 170, 48,0.10);\n                border: 1px solid {C.PRI};\n            }",
        "QPushButton:hover {\n                background: rgba(255, 170, 48, 0.10);\n                border: 1px solid rgba(255, 170, 48, 0.3);\n            }"
    )
]

for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        print("Replaced:", repr(old[:30]))
    else:
        print("Could not find:", repr(old[:30]))

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
