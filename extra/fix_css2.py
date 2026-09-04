import os
import re

file_path = r"d:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Make SettingsCard background transparent
text = re.sub(
    r"QFrame#SettingsCard \{\s*background: [^;]+;\s*border: [^;]+;\s*border-radius: [^;]+;\s*\}",
    "QFrame#SettingsCard {\n                background: transparent;\n                border: 1px solid rgba(255, 255, 255, 0.06);\n                border-radius: 18px;\n            }",
    text,
    flags=re.MULTILINE
)

# Update QPushButton hover
text = re.sub(
    r"QPushButton:hover \{\s*background: rgba\(255,\s*170,\s*48,0\.10\);\s*border: 1px solid \{C\.PRI\};\s*\}",
    "QPushButton:hover {\n                background: rgba(255, 170, 48, 0.10);\n                border: 1px solid rgba(255, 170, 48, 0.3);\n            }",
    text,
    flags=re.MULTILINE
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print('Done styling with regex!')
