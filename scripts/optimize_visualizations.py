#!/usr/bin/env python3
"""Optimize HTML files: minify, reduce size, improve performance."""

import re
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")

def minify_css(css):
    """Minify CSS."""
    # Remove comments
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    # Remove excess whitespace
    css = re.sub(r'\s+', ' ', css)
    # Remove spaces around special characters
    css = re.sub(r'\s*([{}:;,])\s*', r'\1', css)
    return css.strip()

def minify_js(js):
    """Minify JavaScript."""
    # Remove comments
    js = re.sub(r'//.*?\n', '\n', js)
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
    # Remove excess whitespace
    js = re.sub(r'\s+', ' ', js)
    # Keep necessary spaces around keywords
    js = re.sub(r'\s*(const|let|var|function|return|if|else)\s+', r' \1 ', js)
    js = re.sub(r'\s*([{}();,])\s*', r'\1', js)
    return js.strip()

def optimize_html(html_file):
    """Optimize HTML file."""
    with open(html_file) as f:
        content = f.read()

    original_size = len(content)

    # Extract and minify style
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    if style_match:
        style = style_match.group(1)
        minified_style = minify_css(style)
        content = content.replace(f'<style>{style}</style>', f'<style>{minified_style}</style>')

    # Extract and minify script
    script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
    if script_match:
        script = script_match.group(1)
        minified_script = minify_js(script)
        content = content.replace(f'<script>{script}</script>', f'<script>{minified_script}</script>')

    # Remove extra whitespace between tags
    content = re.sub(r'>\s+<', '><', content)
    # Remove multiple spaces
    content = re.sub(r'  +', ' ', content)

    # Add loading="lazy" to images if any
    content = re.sub(r'<img ', '<img loading="lazy" ', content)

    new_size = len(content)
    reduction = original_size - new_size

    with open(html_file, 'w') as f:
        f.write(content)

    return reduction

def main():
    total_reduction = 0
    count = 0

    for html_file in sorted(HTML_DIR.glob("*.html")):
        if html_file.name.startswith('.'):
            continue
        reduction = optimize_html(html_file)
        total_reduction += reduction
        count += 1
        if count % 50 == 0:
            print(f"Optimized {count} files, {total_reduction} bytes saved...")

    print(f"\n✓ Optimized {count} files")
    print(f"✓ Total size reduction: {total_reduction:,} bytes ({total_reduction/1024:.1f} KB)")

if __name__ == '__main__':
    main()
