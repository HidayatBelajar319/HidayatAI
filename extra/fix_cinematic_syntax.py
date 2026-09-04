import os

file_path = r'd:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the multi-line string errors
text = text.replace('self._s1_lbl.setText(self._s1_lbl.text() + "\n\n" + line)', 'self._s1_lbl.setText(self._s1_lbl.text() + "\\n\\n" + line)')
text = text.replace('gs = QLabel("★★★★★ Recommended\nPrimary Intelligence")', 'gs = QLabel("★★★★★ Recommended\\nPrimary Intelligence")')
text = text.replace('os_lbl = QLabel("Multiple Models\nOptional Secondary")', 'os_lbl = QLabel("Multiple Models\\nOptional Secondary")')
text = text.replace('self._s3_status.setText("✓ Identity Verified\nGemini 2.5 Pro\nLatency 87 ms\nReady")', 'self._s3_status.setText("✓ Identity Verified\\nGemini 2.5 Pro\\nLatency 87 ms\\nReady")')
text = text.replace('self._intro_lbl = QLabel("Identity confirmed.\n\nHello.\n\nI\'m Brahma Echo.\n\nReady whenever you are.")', 'self._intro_lbl = QLabel("Identity confirmed.\\n\\nHello.\\n\\nI\'m Brahma Echo.\\n\\nReady whenever you are.")')
text = text.replace('self._s4_lbl.setText(current_text + ("\n" if current_text else "") + modules[self._ignite_step])', 'self._s4_lbl.setText(current_text + ("\\n" if current_text else "") + modules[self._ignite_step])')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed syntax errors')
