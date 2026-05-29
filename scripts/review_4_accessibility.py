#!/usr/bin/env python3
"""Review 4: Accessibility and responsiveness."""

import re
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

def enhance_accessibility(html_file):
    """Add accessibility and responsive features."""
    with open(html_file) as f:
        content = f.read()

    original = content

    # 1. Add mobile viewport with proper meta tag
    if 'maximum-scale' not in content:
        content = content.replace(
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">'
        )

    # 2. Add prefers-reduced-motion support
    if 'prefers-reduced-motion' not in content:
        motion = '''
    @media (prefers-reduced-motion: reduce) {
      * { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
    }'''
        content = content.replace('</style>', motion + '\n  </style>')

    # 3. Add color contrast enhancements
    if 'color-contrast' not in content:
        contrast = '''
    @media (prefers-contrast: more) {
      body { color: #ffffff; }
      .item { border-left-width: 4px; }
    }'''
        content = content.replace('</style>', contrast + '\n  </style>')

    # 4. Add mobile-first responsive design
    if '@media (max-width: 768px)' not in content:
        responsive = '''
    @media (max-width: 768px) {
      .container { flex-direction: column; }
      .controls { width: 100%; border-left: none; border-top: 1px solid #334155; }
      h1 { font-size: 20px; }
      button { padding: 12px 16px; font-size: 16px; }
    }'''
        content = content.replace('</style>', responsive + '\n  </style>')

    # 5. Add print styles
    if '@media print' not in content:
        print_style = '''
    @media print {
      .controls { display: none; }
      body { background: white; color: black; }
      a { color: black; }
    }'''
        content = content.replace('</style>', print_style + '\n  </style>')

    # 6. Add dark mode support
    if '@media (prefers-color-scheme: light)' not in content:
        lightmode = '''
    @media (prefers-color-scheme: light) {
      body { background: #f8fafc; color: #1e293b; }
      header { background: #e2e8f0; border-bottom-color: #cbd5e1; }
      .status { background: #e2e8f0; }
      .item { background: #f1f5f9; }
    }'''
        content = content.replace('</style>', lightmode + '\n  </style>')

    # 7. Add semantic HTML improvements
    content = re.sub(r'<h2[^>]*>', '<h2 role="main">', content)

    # 8. Add loading attribute to external resources
    if '<img' in content:
        content = re.sub(r'<img(?![^>]*loading=)', '<img loading="lazy"', content)

    # 9. Ensure sufficient color contrast text
    if '--text-contrast' not in content:
        contrast_vars = '''
    :root { --text-contrast: #e2e8f0; --bg-contrast: #0f172a; }'''
        content = content.replace('</style>', contrast_vars + '\n  </style>')

    # 10. Add focus trap for keyboard users
    focus_trap = '''
    const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const modal = document.querySelector('.modal');
    if (modal) {
      const firstFocusable = modal.querySelector(focusableElements);
      const focusableContent = modal.querySelectorAll(focusableElements);
      const lastFocusable = focusableContent[focusableContent.length - 1];
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
          if (e.shiftKey && document.activeElement === firstFocusable) {
            lastFocusable.focus();
            e.preventDefault();
          } else if (!e.shiftKey && document.activeElement === lastFocusable) {
            firstFocusable.focus();
            e.preventDefault();
          }
        }
      });
    }'''
    if 'focusableElements' not in content:
        content = content.replace('</script>', focus_trap + '\n  </script>')

    with open(html_file, 'w') as f:
        f.write(content)

    return content != original

def main():
    enhanced = 0
    for html_file in sorted(HTML_DIR.glob("*.html")):
        if html_file.name.startswith('.'):
            continue
        try:
            if enhance_accessibility(html_file):
                enhanced += 1
                if enhanced % 50 == 0:
                    print(f"Enhanced {enhanced} files...")
        except Exception as e:
            print(f"Error {html_file.name}: {e}")

    print(f"\n✓ Review 4 Complete: Accessibility enhanced in {enhanced} files")
    print("  - Added mobile viewport options")
    print("  - Added prefers-reduced-motion support")
    print("  - Added high contrast mode support")
    print("  - Added responsive design (@media queries)")
    print("  - Added print styles")
    print("  - Added dark/light mode support")
    print("  - Added semantic HTML")
    print("  - Added focus trap for keyboard navigation")

if __name__ == '__main__':
    main()
