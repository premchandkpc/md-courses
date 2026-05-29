#!/usr/bin/env python3
"""Fix all back-links in HTML files to point to correct data directories."""

import re
from pathlib import Path

HTML_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/html")
DATA_DIR = Path("/Users/ramyachowdary/Documents/prem-work/md-courses/data")

# Get all data directories
DATA_DIRS = sorted([d.name for d in DATA_DIR.iterdir() if d.is_dir() and d.name[0].isdigit()])

# Map file number ranges to data topics
FILE_TO_TOPIC = {
    range(1, 50): "09-distributed-systems",      # System design, networking, backend patterns
    range(50, 100): "13-security",                # Security, testing, design patterns, incidents
    range(100, 105): "00-foundations",            # Paradigms, algorithms
    range(105, 125): "01-ai-ml",                  # ML concepts
    range(125, 145): "02-data-engineering",       # Data pipelines
    range(145, 165): "03-backend",                # Backend services
    range(165, 180): "04-frontend",               # Frontend frameworks
    range(180, 195): "06-devops",                 # DevOps, CI/CD
    range(195, 210): "14-sre-observability",      # Observability, monitoring
    range(210, 226): "19-testing",                # Testing, QA
}

def get_topic_for_file(file_num):
    """Get topic directory for a file number."""
    for range_obj, topic in FILE_TO_TOPIC.items():
        if file_num in range_obj:
            return topic
    return "00-foundations"  # Default

def fix_file(html_file):
    """Fix back-link in HTML file."""
    # Extract file number
    match = re.match(r'(\d+)-', html_file.name)
    if not match:
        return False

    file_num = int(match.group(1))
    topic = get_topic_for_file(file_num)

    with open(html_file) as f:
        content = f.read()

    # Find and replace back-link
    old_pattern = r'href="[^"]*Back to Notes'
    new_link = f'href="../data/{topic}/index.md" class="back-link">← Back to Notes'

    new_content = re.sub(
        r'href="[^"]*"[^>]*class="back-link">← Back to Notes',
        new_link,
        content
    )

    if new_content != content:
        with open(html_file, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    fixed = 0
    for html_file in sorted(HTML_DIR.glob("*.html")):
        if html_file.name.startswith('.'):
            continue
        if fix_file(html_file):
            fixed += 1

    print(f"✓ Fixed {fixed} back-links")

if __name__ == '__main__':
    main()
