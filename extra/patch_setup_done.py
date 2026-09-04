import re

file_path = r'd:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

new_setup_done = """    def _on_setup_done(self, gemini_key: str, or_key: str, os_sys: str):
        self.showNormal()
        if self._overlay:
"""
text = re.sub(r'    def _on_setup_done\(self, gemini_key: str, or_key: str, os_sys: str\):\n        if self\._overlay:', new_setup_done, text, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched _on_setup_done')
