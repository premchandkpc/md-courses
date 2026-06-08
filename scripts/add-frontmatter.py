#!/usr/bin/env python3
"""
Batch-add YAML frontmatter to all .md files in content/.
Extracts title from # heading, infers difficulty/path from directory,
preserves existing Level/Time markers.

Usage:
    python3 scripts/add-frontmatter.py              # dry run — show what would change
    python3 scripts/add-frontmatter.py --apply      # apply changes
    python3 scripts/add-frontmatter.py --file content/08-databases/01-postgresql-internals.md  # single file
"""

import os
import re
import sys
import pathlib

CONTENT_DIR = pathlib.Path(__file__).resolve().parent.parent / 'content'

# Difficulty mapping by domain heuristics
DOMAIN_DIFFICULTY = {
    '00-foundations': 'beginner',
    '01-ai-ml': 'intermediate',
    '02-data-engineering': 'intermediate',
    '03-backend': 'intermediate',
    '04-frontend': 'intermediate',
    '05-cloud': 'intermediate',
    '06-devops': 'intermediate',
    '07-kubernetes': 'advanced',
    '08-databases': 'intermediate',
    '09-distributed-systems': 'advanced',
    '10-messaging': 'advanced',
    '11-networking': 'intermediate',
    '12-operating-systems': 'intermediate',
    '13-security': 'intermediate',
    '14-sre-observability': 'advanced',
    '15-system-design': 'advanced',
    '16-microservices': 'advanced',
    '17-software-architecture': 'advanced',
    '18-performance-engineering': 'advanced',
    '19-testing': 'intermediate',
    '20-interviews': 'advanced',
    '21-roadmaps': 'beginner',
    '22-production-stories': 'advanced',
    '23-projects': 'advanced',
    '24-low-level-design': 'intermediate',
    '25-software-engineering': 'intermediate',
}

# Path mapping
DOMAIN_PATHS = {
    '00-foundations': ['backend-junior'],
    '01-ai-ml': ['ai-ml'],
    '02-data-engineering': ['data', 'ai-ml'],
    '03-backend': ['backend-junior', 'backend-senior'],
    '04-frontend': ['frontend'],
    '05-cloud': ['sre', 'backend-senior'],
    '06-devops': ['sre', 'backend-junior'],
    '07-kubernetes': ['sre', 'backend-senior'],
    '08-databases': ['backend-junior', 'data', 'backend-senior'],
    '09-distributed-systems': ['backend-senior', 'system-design', 'staff'],
    '10-messaging': ['backend-senior', 'data', 'staff'],
    '11-networking': ['backend-junior', 'sre'],
    '12-operating-systems': ['backend-junior', 'sre'],
    '13-security': ['sre', 'backend-senior'],
    '14-sre-observability': ['sre', 'backend-senior'],
    '15-system-design': ['system-design', 'staff'],
    '16-microservices': ['backend-senior', 'staff'],
    '17-software-architecture': ['staff'],
    '18-performance-engineering': ['backend-senior', 'sre'],
    '19-testing': ['backend-junior', 'frontend'],
    '20-interviews': ['system-design', 'backend-senior'],
    '21-roadmaps': ['backend-junior'],
    '22-production-stories': ['staff', 'sre'],
    '23-projects': ['staff'],
    '24-low-level-design': ['backend-junior'],
    '25-software-engineering': ['backend-junior'],
}


def guess_domain(filepath):
    """Extract domain name from file path (first numeric prefix segment)."""
    parts = filepath.relative_to(CONTENT_DIR).parts
    for p in parts:
        if re.match(r'^\d{2}-', p):
            return p
    if 'arch' in parts:
        return 'arch'
    if 'cheat-sheets' in parts:
        return 'cheat-sheets'
    if 'components' in parts:
        return 'components'
    if 'paths' in parts:
        return 'paths'
    if 'html-visualizations' in parts:
        return 'html-visualizations'
    return None


def extract_title(content):
    """Extract title from first # heading, stripping emoji and suffix."""
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if not m:
        return None
    title = m.group(1).strip()
    # Strip emoji
    title = re.sub(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', '', title).strip()
    # Remove common suffixes: "— Complete ... Deep Dive", "— Complete Guide", "— Deep Dive", etc.
    title = re.sub(r'\s*[—–-]{1,2}\s*Complete\s+.*?(Deep\s+Dive|Guide|Overview)\s*$', '', title)
    title = re.sub(r'\s*[—–-]{1,2}\s*(Deep\s+Dive|Complete\s+(Guide|Overview)|Comprehensive\s+Guide)\s*$', '', title)
    # Remove trailing dash/hyphen artifacts
    title = re.sub(r'\s*[—–-]\s*$', '', title).strip()
    return title


def extract_level(content):
    """Extract Level: marker from content."""
    m = re.search(r'\*\*Level:\*\*\s*(\S+)', content)
    if m:
        return m.group(1).lower()
    return None


def extract_time(content):
    """Extract Time: marker from content."""
    m = re.search(r'\*\*Time:\*\*\s*(\S+)', content)
    if m:
        return m.group(1).lower()
    return None


def has_frontmatter(content):
    """Check if content already has YAML frontmatter."""
    return content.startswith('---')


def build_frontmatter(title, domain, level, time_est):
    """Build YAML frontmatter string."""
    lines = ['---']
    if title:
        lines.append(f'title: {title}')
    if domain:
        lines.append(f'topic: {domain}')
        diff = DOMAIN_DIFFICULTY.get(domain, 'intermediate')
        # Level marker overrides domain heuristic
        level_map = {'beginner': 'beginner', 'intermediate': 'intermediate', 'advanced': 'advanced', 'staff': 'staff'}
        if level and level.lower() in level_map:
            diff = level_map[level.lower()]
        lines.append(f'difficulty: {diff}')
    if time_est:
        lines.append(f'time: {time_est}')
    else:
        lines.append('time: 30m')
    if domain and domain in DOMAIN_PATHS:
        paths = DOMAIN_PATHS[domain]
        lines.append(f'paths:')
        for p in paths:
            lines.append(f'  - {p}')
    lines.append('---')
    return '\n'.join(lines)


def process_file(filepath, apply=False):
    """Process a single .md file, adding frontmatter if missing."""
    content = filepath.read_text(encoding='utf-8')

    if has_frontmatter(content):
        return None  # already has frontmatter

    title = extract_title(content)
    domain = guess_domain(filepath)
    level = extract_level(content)
    time_est = extract_time(content)

    fm = build_frontmatter(title, domain, level, time_est)

    # Remove old Level/Time markers if they exist (they're now in frontmatter)
    cleaned = content
    if level:
        cleaned = re.sub(r'\*\*Level:\*\*\s*\S+\s*\|\s*', '', cleaned)
        cleaned = re.sub(r'\*\*Level:\*\*\s*\S+\s*', '', cleaned)
    if time_est:
        cleaned = re.sub(r'\*\*Time:\*\*\s*\S+\s*', '', cleaned)
    # Clean up empty lines at start
    cleaned = re.sub(r'^\s*\n', '', cleaned, count=1)

    new_content = fm + '\n\n' + cleaned

    rel = filepath.relative_to(CONTENT_DIR)
    if apply:
        filepath.write_text(new_content, encoding='utf-8')
        return f'  UPDATED {rel}'
    else:
        return f'  WOULD UPDATE {rel} (title={title}, domain={domain})'


def main():
    apply = '--apply' in sys.argv
    single = None
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            single = pathlib.Path(sys.argv[idx + 1]).resolve()

    if single:
        result = process_file(single, apply=apply)
        if result:
            print(result)
        else:
            rel = single.relative_to(CONTENT_DIR) if CONTENT_DIR in single.parents else single
            print(f'  SKIPPED {rel} (already has frontmatter)')
        return

    # Walk all .md files
    md_files = sorted(CONTENT_DIR.rglob('*.md'))
    # Skip files in paths/ and archived dirs
    skip_dirs = {'node_modules', '__pycache__', '.git'}
    md_files = [f for f in md_files if not any(d in f.parts for d in skip_dirs)]

    print(f'Scanning {len(md_files)} .md files in {CONTENT_DIR}...')
    if not apply:
        print('DRY RUN — use --apply to write changes')
    print()

    updated = 0
    skipped = 0
    for f in md_files:
        result = process_file(f, apply=apply)
        if result:
            if apply:
                print(result)
            updated += 1
        else:
            skipped += 1

    print()
    print(f'Done: {updated} updated, {skipped} already have frontmatter')
    if not apply:
        print(f'Re-run with --apply to write changes to {updated} files')


if __name__ == '__main__':
    main()
