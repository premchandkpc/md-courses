#!/usr/bin/env python3
"""Review 1: Check structure, add missing elements."""

import re
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

def review_and_enhance(html_file):
    """Review file structure and enhance."""
    with open(html_file) as f:
        content = f.read()

    original = content

    # 1. Ensure proper meta tags
    if 'meta name="description"' not in content:
        meta_desc = '<meta name="description" content="Interactive learning visualization">'
        content = content.replace('<meta name="viewport"', meta_desc + '\n  <meta name="viewport"')

    # 2. Add lang attribute if missing
    if '<html lang=' not in content:
        content = content.replace('<html', '<html lang="en"')

    # 3. Ensure title tag has proper format
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match:
        title = title_match.group(1)
        if ' | ' not in title:
            new_title = f'{title} | Engineering Knowledge'
            content = content.replace(f'<title>{title}</title>', f'<title>{new_title}</title>')

    # 4. Add footer with metadata
    if '<footer' not in content:
        footer = '''
  <footer style="background:#0f172a;border-top:1px solid #334155;padding:15px 20px;text-align:center;font-size:11px;color:#64748b;">
    <div>Interactive Learning Visualization</div>
    <div style="margin-top:5px;"><a href="https://github.com" style="color:#60a5fa;text-decoration:none;">View Source</a></div>
  </footer>'''
        content = content.replace('</body>', footer + '\n</body>')

    # 5. Add skip-to-content link for accessibility
    if 'Skip to content' not in content:
        skip_link = '<a href="#content" style="position:absolute;top:-40px;left:0;background:#000;color:#fff;padding:8px;text-decoration:none;z-index:100;">Skip to content</a>'
        content = content.replace('<body>', f'<body>{skip_link}')

    # 6. Add aria-labels to main sections
    content = re.sub(r'<div id="canvas">', '<div id="canvas" aria-label="Content area">', content)
    content = re.sub(r'<div class="controls">', '<div class="controls" aria-label="Control panel">', content)

    # 7. Add role to status div
    if 'role="status"' not in content:
        content = re.sub(
            r'<div class="status">',
            '<div class="status" role="status" aria-live="polite">',
            content
        )

    # 8. Ensure buttons have proper types
    content = re.sub(r'<button onclick=', '<button type="button" onclick=', content)

    # 9. Add keyboard shortcut hints in comments
    if '<!-- Keyboard shortcuts -->' not in content:
        shortcuts = '''
  <!-- Keyboard shortcuts: Alt+L = Load, Alt+N = Next, Alt+R = Reset -->'''
        content = content.replace('</head>', shortcuts + '\n</head>')

    with open(html_file, 'w') as f:
        f.write(content)

    return content != original

def main():
    enhanced = 0
    for html_file in sorted(HTML_DIR.glob("*.html")):
        if html_file.name.startswith('.'):
            continue
        try:
            if review_and_enhance(html_file):
                enhanced += 1
                if enhanced % 50 == 0:
                    print(f"Enhanced {enhanced} files...")
        except Exception as e:
            print(f"Error {html_file.name}: {e}")

    print(f"\n✓ Review 1 Complete: Structure improved in {enhanced} files")
    print("  - Added meta descriptions")
    print("  - Fixed title formatting")
    print("  - Added accessibility features (ARIA, skip links)")
    print("  - Added footer metadata")
    print("  - Proper button types")

if __name__ == '__main__':
    main()
