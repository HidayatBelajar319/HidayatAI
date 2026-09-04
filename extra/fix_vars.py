import sys

def fix_file(f, replacements):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    for o, n in replacements:
        content = content.replace(o, n)
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

fix_file('main.py', [
    ('brahma echo = BrahmaLive(', 'brahma_echo = BrahmaLive('),
    ('brahma echo.plugin_manager', 'brahma_echo.plugin_manager'),
    ('plugin_manager.register_brahma(brahma echo)', 'plugin_manager.register_brahma(brahma_echo)'),
    ('plugin_manager.dispatch("on_startup", brahma echo)', 'plugin_manager.dispatch("on_startup", brahma_echo)'),
    ('asyncio.run(brahma echo.run())', 'asyncio.run(brahma_echo.run())')
])

fix_file('plugin_manager.py', [
    ('self.brahma echo', 'self.brahma_echo'),
    ('brahma echo=self.brahma_echo', 'brahma_echo=self.brahma_echo')
])

print('Fixes applied!')
