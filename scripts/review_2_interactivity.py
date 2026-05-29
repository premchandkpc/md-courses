#!/usr/bin/env python3
"""Review 2: Enhance interactivity and add features."""

import re
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

def enhance_interactivity(html_file):
    """Add enhanced interactivity features."""
    with open(html_file) as f:
        content = f.read()

    original = content

    # 1. Add keyboard event handlers
    if 'window.addEventListener("keydown"' not in content:
        keyboard_handler = '''
    window.addEventListener('keydown', (e) => {
      if (e.altKey) {
        if (e.key === 'l' || e.key === 'L') app.load();
        if (e.key === 'n' || e.key === 'N') app.nextStep();
        if (e.key === 'r' || e.key === 'R') app.reset();
      }
    });'''
        content = content.replace('window.addEventListener("load"', keyboard_handler + '\n    window.addEventListener("load"')

    # 2. Add hover tooltips to buttons
    if 'title=' not in content or 'title="Load' not in content:
        content = re.sub(
            r'<button[^>]*onclick="app\.load\(\)"[^>]*>Load Content</button>',
            '<button type="button" onclick="app.load()" title="Load content (Alt+L)">Load Content</button>',
            content
        )
        content = re.sub(
            r'<button[^>]*onclick="app\.nextStep\(\)"[^>]*>Next Step</button>',
            '<button type="button" onclick="app.nextStep()" title="Next step (Alt+N)">Next Step</button>',
            content
        )
        content = re.sub(
            r'<button[^>]*onclick="app\.reset\(\)"[^>]*>Reset</button>',
            '<button type="button" onclick="app.reset()" title="Reset (Alt+R)">Reset</button>',
            content
        )

    # 3. Add local storage for state persistence
    if 'localStorage' not in content:
        storage_code = '''
      loadState() {
        const saved = localStorage.getItem(window.location.pathname);
        if (saved) this.state = JSON.parse(saved);
      },
      saveState() {
        localStorage.setItem(window.location.pathname, JSON.stringify(this.state));
      },'''
        content = re.sub(
            r'init\(\) \{ this\.render\(\); \},',
            f'init() {{ this.loadState(); this.render(); }},\n      {storage_code}',
            content
        )
        # Add saveState calls
        content = re.sub(
            r'this\.render\(\);',
            'this.render(); this.saveState();',
            content
        )

    # 4. Add animation to progress bar
    if '.progress-fill' not in content or 'transition' not in content:
        progress_style = '''
    .progress-fill { transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1); }'''
        content = content.replace('</style>', progress_style + '\n  </style>')

    # 5. Add smooth scrolling
    if 'scroll-behavior' not in content:
        scroll_style = '''html { scroll-behavior: smooth; }'''
        content = content.replace('* { margin: 0; padding: 0; box-sizing: border-box; }', scroll_style + '\n    * { margin: 0; padding: 0; box-sizing: border-box; }')

    # 6. Add focus styles for keyboard navigation
    if ':focus-visible' not in content:
        focus_style = '''
    button:focus-visible { outline: 2px solid #60a5fa; outline-offset: 2px; }
    a:focus-visible { outline: 2px solid #60a5fa; outline-offset: 2px; }'''
        content = content.replace('</style>', focus_style + '\n  </style>')

    # 7. Add click feedback
    if 'pointer-down' not in content:
        feedback_style = '''
    button:active { opacity: 0.8; }'''
        content = content.replace('</style>', feedback_style + '\n  </style>')

    with open(html_file, 'w') as f:
        f.write(content)

    return content != original

def main():
    enhanced = 0
    for html_file in sorted(HTML_DIR.glob("*.html")):
        if html_file.name.startswith('.'):
            continue
        try:
            if enhance_interactivity(html_file):
                enhanced += 1
                if enhanced % 50 == 0:
                    print(f"Enhanced {enhanced} files...")
        except Exception as e:
            print(f"Error {html_file.name}: {e}")

    print(f"\n✓ Review 2 Complete: Interactivity enhanced in {enhanced} files")
    print("  - Added keyboard shortcuts (Alt+L/N/R)")
    print("  - Added button tooltips")
    print("  - Added state persistence (localStorage)")
    print("  - Added smooth animations")
    print("  - Added keyboard focus styles")
    print("  - Added click feedback")

if __name__ == '__main__':
    main()
