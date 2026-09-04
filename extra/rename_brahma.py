import os
import glob
import re

files_to_update = glob.glob('*.py') + glob.glob('**/*.html', recursive=True)

pattern = re.compile(r'\bBrahma(?:\s*AI(?:\s*-\s*Lite|\s*Lite)?)?\b(?!\s*Echo)', re.IGNORECASE)

def replacer(match):
    text = match.group(0)
    if text.isupper():
        return "BRAHMA ECHO"
    elif text.islower():
        return "brahma echo"
    else:
        return "Brahma Echo"

for file_path in files_to_update:
    if file_path == 'rename_brahma.py':
        continue
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = pattern.sub(replacer, content)
        
        # Handle Hindi occurrences
        new_content = new_content.replace('ब्रह्मा', 'ब्रह्मा इको')
        # Clean up any potential accidental doubling
        new_content = new_content.replace('ब्रह्मा इको इको', 'ब्रह्मा इको')
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_path}")
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
