#!/usr/bin/env python3
"""Scan all domains for diagrams, generate master report"""

import re
from pathlib import Path
from collections import defaultdict

def count_ascii_diagrams(content):
    """Count ASCII diagram blocks"""
    blocks = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if any(c in line for c in '┌┐└┘├┤┬┴─│'):
            block_lines = [line]
            j = i + 1
            while j < len(lines) and (any(c in lines[j] for c in '┌┐└┘├┤┬┴─│') or lines[j].strip() == ''):
                block_lines.append(lines[j])
                j += 1
                if j - i > 20:
                    break
            block_content = '\n'.join(block_lines)
            if len(block_content.strip()) > 10:
                blocks.append((i, len(block_content.split('\n'))))
                i = j
            else:
                i += 1
        else:
            i += 1
    return blocks

repo_root = Path("/Users/ramyachowdary/Documents/prem-work/md-courses")
data_dir = repo_root / "data"

results = defaultdict(lambda: {"files": 0, "diagrams": 0, "lines": 0})

# Scan all domains
for domain_dir in sorted(data_dir.iterdir()):
    if not domain_dir.is_dir():
        continue

    domain_name = domain_dir.name
    for md_file in domain_dir.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            blocks = count_ascii_diagrams(content)
            if blocks:
                results[domain_name]["files"] += 1
                results[domain_name]["diagrams"] += len(blocks)
                results[domain_name]["lines"] += sum(lines for _, lines in blocks)

        except Exception as e:
            pass

# Generate report
report = ["# Diagram Scan — All Domains\n"]
report.append(f"**Total Domains:** {len(results)}\n")
report.append(f"**Total Files with diagrams:** {sum(r['files'] for r in results.values())}\n")
report.append(f"**Total ASCII diagrams:** {sum(r['diagrams'] for r in results.values())}\n")
report.append(f"**Total ASCII lines:** {sum(r['lines'] for r in results.values())}\n\n")

report.append("## By Domain (sorted by line count)\n\n")
report.append("| Domain | Files | Diagrams | Lines | Priority |\n")
report.append("|--------|-------|----------|-------|----------|\n")

sorted_domains = sorted(results.items(), key=lambda x: x[1]['lines'], reverse=True)
for domain, data in sorted_domains:
    priority = "🔴 High" if data['lines'] > 500 else "🟡 Medium" if data['lines'] > 200 else "🟢 Low"
    report.append(f"| {domain} | {data['files']} | {data['diagrams']} | {data['lines']} | {priority} |\n")

report.append("\n## Conversion Queue\n\n")
report.append("**Phase 2 Priority (by impact):**\n")
for i, (domain, data) in enumerate(sorted_domains[:6], 1):
    report.append(f"{i}. `{domain}` — {data['lines']} lines, {data['diagrams']} diagrams\n")

# Save report
report_path = repo_root / "SCAN_ALL_DOMAINS.md"
with open(report_path, 'w') as f:
    f.write(''.join(report))

print(f"✅ Scanned {len(results)} domains")
print(f"📊 Report saved to SCAN_ALL_DOMAINS.md")
print(f"\nTop 5 domains by line count:")
for domain, data in sorted_domains[:5]:
    print(f"  {domain}: {data['lines']} lines")

