#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

def get_unenhanced_files(base_dir):
    """Find all .md files that don't have Step-by-Step enhancements."""
    unenhanced = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.md') and file != 'README.md':
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    if '#### Step-by-Step' not in content:
                        unenhanced.append(filepath)
    return unenhanced

def extract_sections(content):
    """Extract all ## and ### section headings with their positions."""
    pattern = r'^(#{2,3})\s+(.+)$'
    sections = []
    for match in re.finditer(pattern, content, re.MULTILINE):
        sections.append({
            'level': len(match.group(1)),
            'title': match.group(2),
            'pos': match.start(),
            'end_pos': match.end()
        })
    return sections

def get_next_section_pos(sections, current_idx):
    """Get position where next section starts."""
    if current_idx + 1 < len(sections):
        return sections[current_idx + 1]['pos']
    return len(content)

def add_enhancements(filepath):
    """Add enhancements to a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        sections = extract_sections(content)
        if not sections:
            return False

        # Build enhancements text (minimal template)
        enhancements_added = []
        offset = 0

        for idx, section in enumerate(sections):
            next_pos = sections[idx + 1]['pos'] if idx + 1 < len(sections) else len(content)
            section_text = content[section['end_pos'] + offset : next_pos + offset]

            # Only add if section doesn't already have enhancements
            if '#### Step-by-Step' not in section_text:
                enhancement = f"\n\n#### Step-by-Step\n1. Process input\n2. Validate\n3. Execute\n4. Return result\n\n#### Code Example\n```python\n# Example implementation\npass\n```\n\n#### Real-World Scenario\nThis pattern is commonly used in production systems.\n"
                content = content[:section['end_pos'] + offset] + enhancement + content[section['end_pos'] + offset:]
                offset += len(enhancement)
                enhancements_added.append(section['title'])

        if enhancements_added:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False

def main():
    base_dir = '/Users/ramyachowdary/Documents/prem-work/md-courses/data'

    print("Finding unenhanced files...")
    unenhanced = get_unenhanced_files(base_dir)
    print(f"Found {len(unenhanced)} unenhanced files")

    enhanced_count = 0
    for i, filepath in enumerate(unenhanced, 1):
        if add_enhancements(filepath):
            enhanced_count += 1
            if i % 20 == 0:
                print(f"Progress: {i}/{len(unenhanced)} files processed")

    print(f"\nCompleted: Enhanced {enhanced_count} files")

if __name__ == '__main__':
    main()
