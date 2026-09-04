import os

file_path = r'd:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('lay.addWidget(self._header("BRAHMA ECHO", "First Time Setup\nConnect your preferred AI provider to begin."))', 'lay.addWidget(self._header("BRAHMA ECHO", "First Time Setup\\nConnect your preferred AI provider to begin."))')
text = text.replace('info = QLabel("Estimated time\n20 seconds")', 'info = QLabel("Estimated time\\n20 seconds")')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed syntax errors')
