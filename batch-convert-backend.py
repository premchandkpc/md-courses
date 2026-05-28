#!/usr/bin/env python3
"""Batch convert Backend domain ASCII diagrams to Mermaid"""

import re
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Conversion:
    file: str
    line: int
    ascii_snippet: str
    mermaid_type: str
    converted: bool

def extract_ascii_blocks(content):
    """Find and extract ASCII diagram blocks with line numbers"""
    blocks = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if any(c in line for c in '┌┐└┘├┤┬┴─│'):
            block_start = i
            block_lines = [line]
            j = i + 1
            while j < len(lines):
                if any(c in lines[j] for c in '┌┐└┘├┤┬┴─│'):
                    block_lines.append(lines[j])
                    j += 1
                elif lines[j].strip() == '' and j < len(lines) - 1:
                    # Allow empty line if next has ASCII
                    if j + 1 < len(lines) and any(c in lines[j+1] for c in '┌┐└┘├┤┬┴─│'):
                        block_lines.append(lines[j])
                        j += 1
                        continue
                    break
                else:
                    break
                if j - i > 20:
                    break

            block_content = '\n'.join(block_lines)
            if len(block_content.strip()) > 10:
                blocks.append((block_start, '\n'.join(block_lines)))
                i = j
            else:
                i += 1
        else:
            i += 1
    return blocks

def classify_and_suggest(content):
    """Classify diagram and suggest Mermaid conversion"""
    # Hierarchy patterns (most common in Backend)
    if ('├' in content or '┬' in content) and content.count('\n') < 15:
        return 'hierarchy', '''```mermaid
graph TD
    A["Parent"] --> B["Child 1"]
    A --> C["Child 2"]
    A --> D["Child 3"]
```'''

    # Sequential flow
    if content.count('→') >= 2 and content.count('\n') < 8:
        return 'flowchart', '''```mermaid
graph LR
    A["Step 1"] --> B["Step 2"] --> C["Step 3"]
```'''

    # State machine
    if ('CLOSED' in content or 'OPEN' in content or 'STATE' in content):
        return 'state', '''```mermaid
stateDiagram-v2
    [*] --> STATE_A
    STATE_A --> STATE_B: trigger
    STATE_B --> STATE_C: condition
```'''

    return 'unknown', None

def should_convert(diagram_type, confidence=0.7):
    """Decide if diagram should be auto-converted"""
    if diagram_type in ['hierarchy', 'flowchart', 'state']:
        return True
    return False

# Scan Backend domain
repo_root = Path("/Users/ramyachowdary/Documents/prem-work/md-courses")
backend_dir = repo_root / "data" / "03-backend"

conversions = []
total_lines = 0
converted_count = 0

for md_file in sorted(backend_dir.rglob("*.md")):
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        blocks = extract_ascii_blocks(original_content)
        if not blocks:
            continue

        for block_start, block_content in blocks:
            diagram_type, suggestion = classify_and_suggest(block_content)

            if should_convert(diagram_type) and suggestion:
                converted_count += 1
                total_lines += len(block_content.split('\n'))
                conversions.append(Conversion(
                    file=str(md_file.relative_to(repo_root)),
                    line=block_start,
                    ascii_snippet=block_content[:50].replace('\n', '\\n'),
                    mermaid_type=diagram_type,
                    converted=True
                ))

    except Exception as e:
        pass

# Generate report
report = ["# Backend Batch Conversion Report\n\n"]
report.append(f"**Status:** Analyzed for conversion\n")
report.append(f"**Files scanned:** {len(list(backend_dir.rglob('*.md')))}\n")
report.append(f"**ASCII diagrams found:** {sum(len(extract_ascii_blocks(open(f).read())) for f in backend_dir.rglob('*.md'))}\n")
report.append(f"**Ready to convert:** {converted_count}\n")
report.append(f"**Total ASCII lines:** {total_lines}\n\n")

report.append("## Conversion Queue\n\n")
for i, conv in enumerate(conversions[:20], 1):
    report.append(f"{i}. `{conv.file}:{conv.line}` — {conv.mermaid_type.upper()}\n")

report.append(f"\n... and {converted_count - 20} more\n" if converted_count > 20 else "")

# Save report
report_path = repo_root / "BACKEND_CONVERSION_QUEUE.md"
with open(report_path, 'w') as f:
    f.write(''.join(report))

print(f"✅ Analyzed Backend domain")
print(f"📊 {converted_count} diagrams ready to convert")
print(f"📈 {total_lines} ASCII lines affected")
print(f"📄 Report: BACKEND_CONVERSION_QUEUE.md")

