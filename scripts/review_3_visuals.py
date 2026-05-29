#!/usr/bin/env python3
"""Review 3: Improve visual design and animations."""

import re
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

def enhance_visuals(html_file):
    """Add visual enhancements and animations."""
    with open(html_file) as f:
        content = f.read()

    original = content

    # 1. Add animation keyframes
    if '@keyframes' not in content:
        animations = '''
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    .fade-in { animation: fadeIn 0.3s ease-in; }
    .slide-up { animation: slideUp 0.3s ease-out; }'''
        content = content.replace('</style>', animations + '\n  </style>')

    # 2. Add gradient backgrounds
    if 'linear-gradient' not in content or 'to bottom' not in content:
        gradient_style = '''
    header { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); }'''
        content = content.replace('header {', 'header { background: linear-gradient(135deg, #1e293b 0%, #334155 100%);')

    # 3. Add box shadows for depth
    if 'box-shadow: none' not in content:
        shadow_style = '''
    .status { box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08); }
    .item { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
    button { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
    button:hover { box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15); }'''
        content = content.replace('</style>', shadow_style + '\n  </style>')

    # 4. Add hover scale effect
    if 'transform: scale' not in content:
        scale_style = '''
    button:hover { transform: translateY(-2px); }
    .item:hover { transform: translateX(4px); }'''
        content = content.replace('</style>', scale_style + '\n  </style>')

    # 5. Add backdrop blur to modals (if any)
    backdrop = '''
    .modal-backdrop { backdrop-filter: blur(4px); }'''
    if 'backdrop-filter' not in content:
        content = content.replace('</style>', backdrop + '\n  </style>')

    # 6. Enhance item styling with gradient on active
    if 'background: rgba(16, 185, 129, 0.1)' in content:
        content = content.replace(
            'background: rgba(16, 185, 129, 0.1);',
            'background: linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0) 100%);'
        )

    # 7. Add color transition
    if 'transition: color' not in content:
        transition = '''
    .item, button { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }'''
        content = content.replace('</style>', transition + '\n  </style>')

    # 8. Add glow effect to active elements
    glow = '''
    .item.active { box-shadow: 0 0 10px rgba(16, 185, 129, 0.3), inset 0 0 10px rgba(16, 185, 129, 0.1); }'''
    if 'box-shadow: 0 0 10px' not in content:
        content = content.replace('</style>', glow + '\n  </style>')

    with open(html_file, 'w') as f:
        f.write(content)

    return content != original

def main():
    enhanced = 0
    for html_file in sorted(HTML_DIR.glob("*.html")):
        if html_file.name.startswith('.'):
            continue
        try:
            if enhance_visuals(html_file):
                enhanced += 1
                if enhanced % 50 == 0:
                    print(f"Enhanced {enhanced} files...")
        except Exception as e:
            print(f"Error {html_file.name}: {e}")

    print(f"\n✓ Review 3 Complete: Visual design improved in {enhanced} files")
    print("  - Added CSS animations (fadeIn, slideUp, pulse)")
    print("  - Added gradient backgrounds")
    print("  - Added box shadows for depth")
    print("  - Added hover scale effects")
    print("  - Added smooth transitions")
    print("  - Added glow effects on active elements")

if __name__ == '__main__':
    main()
