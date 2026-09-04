import os
import re

dir_path = 'frontend/src'

replacements = {
    r'style={{ boxShadow: "4px 4px 0 #333333" }}': 'shadow-hard-muted',
    r'style={{ boxShadow: "4px 4px 0 #FFFFFF" }}': 'shadow-hard',
    r'style={{ boxShadow: "4px 4px 0 #FFE500" }}': 'shadow-hard-y',
    r'style={{ boxShadow: "4px 4px 0 #00FF41" }}': 'shadow-hard-g',
    r'style={{ boxShadow: "4px 4px 0 #FF003C" }}': 'shadow-hard-r',
    r'style={{ boxShadow: "2px 2px 0 #FFFFFF" }}': 'shadow-hard-sm',
    r'style={{ boxShadow: "3px 3px 0 #FFFFFF" }}': 'shadow-hard-sm',
    r'style={{ background: "rgba(0,0,0,0.88)" }}': 'bg-black/90',
}

def process_match(match):
    # This function expects a match like `className="something" style={{...}}`
    class_name = match.group(1)
    style_str = match.group(2)
    
    if style_str in replacements:
        shadow_cls = replacements[style_str]
        return f'className="{class_name} {shadow_cls}"'
    return match.group(0)

for root, _, files in os.walk(dir_path):
    for f in files:
        if f.endswith('.tsx'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            original_content = content
            
            # match `className="..." style={{...}}`
            content = re.sub(r'className="([^"]+)"\s+(style={{[^}]+}})', process_match, content)
            
            # what if style is before className?
            def process_match_rev(match):
                style_str = match.group(1)
                class_name = match.group(2)
                if style_str in replacements:
                    shadow_cls = replacements[style_str]
                    return f'className="{class_name} {shadow_cls}"'
                return match.group(0)
                
            content = re.sub(r'(style={{[^}]+}})\s+className="([^"]+)"', process_match_rev, content)

            if content != original_content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Updated {path}")
