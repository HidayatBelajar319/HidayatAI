import re
import os

file_path = r'd:\TiTech Prabha Solution\Brahma Echo\Brahma Echo\Brahma Echo-AI---Lite-main\Brahma Echo-AI---Lite-main\ui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

new_show_setup = """    def _show_setup(self, defaults: dict | None = None):
        try:
            if self._overlay:
                self._overlay.hide()
                self._overlay.deleteLater()
                self._overlay = None
            
            # Maximize the main window for the cinematic experience
            self.showMaximized()
            
            ov = SetupOverlay(self.centralWidget(), defaults=defaults or self._load_api_defaults())
            cw = self.centralWidget()
            ov.setGeometry(0, 0, cw.width(), cw.height())
            ov.done.connect(self._on_setup_done)
            ov.show()
            ov.raise_()
            ov.activateWindow()
            self._overlay = ov
        except Exception as e:
            import traceback
            with open('setup_crash.log', 'w') as err_f:
                err_f.write(traceback.format_exc())
            raise
"""

# Replace the previous definition of _show_setup
text = re.sub(r'    def _show_setup\(self, defaults: dict \| None = None\):.*?self\._overlay = ov\n        except Exception as e:.*?raise\n', new_show_setup, text, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched _show_setup with showMaximized()')
