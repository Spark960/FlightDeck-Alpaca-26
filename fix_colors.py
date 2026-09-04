import os
import re

dir_path = 'frontend/src'

replacements = {
    # Text
    r'text-\[\#000000\]': 'text-ink',
    r'text-\[\#111111\]': 'text-slab',
    r'text-\[\#FFFFFF\]': 'text-paper',
    r'text-\[\#0A0A0A\]': 'text-void',
    r'text-\[\#333333\]': 'text-rule2',
    r'text-\[\#444444\]': 'text-muted',
    r'text-\[\#555555\]': 'text-muted',
    r'text-\[\#666666\]': 'text-muted',
    r'text-\[\#FFE500\]': 'text-y',
    r'text-\[\#00FF41\]': 'text-pos',
    r'text-\[\#FF003C\]': 'text-neg',
    r'text-\[\#FF8C00\]': 'text-warn',
    r'text-\[\#00BFFF\]': 'text-info',
    r'text-\[\#BF00FF\]': 'text-violet',
    
    # Background
    r'bg-\[\#000000\]': 'bg-ink',
    r'bg-\[\#000A10\]': 'bg-void',
    r'bg-\[\#0A0A0A\]': 'bg-void',
    r'bg-\[\#111111\]': 'bg-slab',
    r'bg-\[\#1A1A1A\]': 'bg-rule2',
    r'bg-\[\#222222\]': 'bg-rule2',
    r'bg-\[\#333333\]': 'bg-rule2',
    r'bg-\[\#FFFFFF\]': 'bg-paper',
    r'bg-\[\#FFE500\]': 'bg-y',
    r'bg-\[\#00FF41\]': 'bg-pos',
    r'bg-\[\#FF003C\]': 'bg-neg',
    r'bg-\[\#FF8C00\]': 'bg-warn',
    r'bg-\[\#00BFFF\]': 'bg-info',
    r'bg-\[\#0099CC\]': 'bg-info/80',
    r'bg-\[\#BF00FF\]': 'bg-violet',

    # Border
    r'border-\[\#000000\]': 'border-ink',
    r'border-\[\#111111\]': 'border-slab',
    r'border-\[\#1A1A1A\]': 'border-rule2',
    r'border-\[\#222222\]': 'border-rule2',
    r'border-\[\#333333\]': 'border-rule2',
    r'border-\[\#FFFFFF\]': 'border-rule',
    r'border-\[\#FFE500\]': 'border-y',
    r'border-\[\#00FF41\]': 'border-pos',
    r'border-\[\#FF003C\]': 'border-neg',
    r'border-\[\#FF8C00\]': 'border-warn',
    r'border-\[\#00BFFF\]': 'border-info',
    r'border-\[\#BF00FF\]': 'border-violet',

    # Divide
    r'divide-\[\#1A1A1A\]': 'divide-rule2',
    r'divide-\[\#222222\]': 'divide-rule2',
    r'divide-\[\#333333\]': 'divide-rule2',

    # Accent
    r'accent-\[\#00BFFF\]': 'accent-info',
    r'accent-\[\#FFE500\]': 'accent-y',
}

for root, _, files in os.walk(dir_path):
    for f in files:
        if f.endswith('.tsx'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            original_content = content
            for k, v in replacements.items():
                content = re.sub(k, v, content)
                
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Updated {path}")
