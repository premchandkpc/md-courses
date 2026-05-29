#!/usr/bin/env python3
"""Strip placeholder content inserted by enhance_files.py across all .md files."""
import os
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

PLACEHOLDER_BLOCK = re.compile(
    r'#### Step-by-Step\n1\. Process input\n2\. Validate\n3\. Execute\n4\. Return result\n\n#### Code Example\n```python\n# Example implementation\npass\n```\n\n#### Real-World Scenario\nThis pattern is commonly used in production systems\.\n',
    re.MULTILINE
)

PLACEHOLDER_BLOCK2 = re.compile(
    r'#### Step-by-Step\n1\. Process input\n2\. Validate\n3\. Execute\n4\. Return result\n\n#### Code Example\n```python\n# Example implementation\npass\n```\n\n#### Real-World Scenario\nThis pattern is commonly used in production systems\.',
    re.MULTILINE
)

def strip_placeholders(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_content = PLACEHOLDER_BLOCK.sub('', content)
    new_content = PLACEHOLDER_BLOCK2.sub('', new_content)
    
    # Clean up multiple blank lines left behind
    new_content = re.sub(r'\n{4,}', '\n\n\n', new_content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    count = 0
    stripped = 0
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                if strip_placeholders(filepath):
                    stripped += 1
                count += 1
    
    print(f"Scanned {count} files, stripped placeholders from {stripped} files")

if __name__ == '__main__':
    main()
