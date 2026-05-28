#!/usr/bin/env python3
"""
Fix ALL broken markdown links in data/ by converting relative internal links
to absolute paths (starting with /) so they always resolve from server root.
"""

import os
import re
import sys
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

MISSING_FILE_MAP = {
    "k8s.md": "07-kubernetes/README.md",
    "loadbalancer.md": "11-networking/load-balancing/loadbalancer.md",
    "designpatterns.md": "17-software-architecture/design-patterns/designpatterns.md",
    "cheatsheet-jvm-tuning.md": "cheat-sheets/jvm-tuning.md",
    "cheatsheet-linux-debugging.md": "cheat-sheets/linux-debugging.md",
    "cheatsheet-git-commands.md": "cheat-sheets/git-commands.md",
    "cheatsheet-docker-commands.md": "cheat-sheets/docker-commands.md",
    "01-db-internals.md": "08-databases/01-relational-database-internals.md",
    "07-cqrs-event-sourcing.md": "16-microservices/07-observability-monitoring.md",
    "08-observability.md": "16-microservices/08-security-identity.md",
    "protocols.md": "11-networking/01-tcpip-protocol-stack.md",
    "MICROSERVICES_SYSTEM_DESIGN.md": "16-microservices/README.md",
    "13-design-patterns-in-java.md": "03-backend/java/14-design-patterns-in-java.md",
    "10-java-8-features.md": "03-backend/java/11-java-8-features.md",
    "04-redis-caching.md": "08-databases/04-redis-deep-dive.md",
    "01-jsx-vdom.md": "04-frontend/react/01-core-fundamentals/01-components-jsx.md",
    "02-hooks-state.md": "04-frontend/react/04-hooks-deep-dive/01-hooks-state.md",
    "03-rendering-performance.md": "04-frontend/react/03-rendering-pipeline/01-rendering-performance.md",
    "04-state-management.md": "04-frontend/react/05-state-management/01-state-management.md",
    "05-routing-data-fetching.md": "04-frontend/react/07-routing/01-routing-data-fetching.md",
    "07-performance-optimization.md": "04-frontend/react/09-performance/01-performance-optimization.md",
    "07-production-issues.md": "04-frontend/react/36-production-failures/01-production-issues.md",
    "02-state-management.md": "04-frontend/react/05-state-management/01-state-management.md",
    "03-component-patterns.md": "04-frontend/react/06-component-architecture/01-component-patterns.md",
    "01-distributed-systems.md": "09-distributed-systems/README.md",
    "linux.md": "12-operating-systems/README.md",
    "observability.md": "14-sre-observability/README.md",
}

LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]*)\)')
INLINE_CODE_PATTERN = re.compile(r'`[^`]*`')


def build_file_index(data_dir):
    index = defaultdict(list)
    for root, _dirs, files in os.walk(data_dir):
        for f in files:
            if f.endswith(".md"):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, data_dir)
                index[f].append(rel_path)
    return index


def resolve_link(source_rel_path, link_target, file_index):
    source_dir = os.path.dirname(source_rel_path)
    resolved = os.path.normpath(os.path.join(source_dir, link_target))

    abs_path = os.path.join(DATA_DIR, resolved)
    if os.path.exists(abs_path):
        return resolved, False

    if os.path.isdir(abs_path):
        readme = os.path.join(abs_path, "README.md")
        if os.path.exists(readme):
            resolved_readme = os.path.join(resolved, "README.md")
            return resolved_readme, True

    basename = os.path.basename(link_target)
    if basename in MISSING_FILE_MAP:
        mapped = MISSING_FILE_MAP[basename]
        mapped_abs = os.path.join(DATA_DIR, mapped)
        if os.path.exists(mapped_abs):
            return mapped, True

    if basename in file_index:
        candidates = file_index[basename]
        if len(candidates) == 1:
            return candidates[0], True
        elif len(candidates) > 1:
            exact_match = [c for c in candidates if c.endswith(link_target)]
            if exact_match:
                return exact_match[0], True
            shortest = min(candidates, key=lambda c: len(c))
            return shortest, True

    return None, False


def is_url_external(target):
    return bool(re.match(r'^(https?://|//|mailto:|ftp://|tel:)', target))


def is_anchor_only(target):
    return target.startswith("#")


def is_absolute_path(target):
    return target.startswith("/")


def is_relative_internal_link(target):
    if is_url_external(target) or is_anchor_only(target) or is_absolute_path(target):
        return False
    if not target.strip():
        return False
    if " " in target.strip():
        return False
    target_clean = target.split("#")[0].split("?")[0]
    if not target_clean:
        return False
    is_md = target_clean.endswith(".md")
    is_dir = target_clean.endswith("/")
    is_no_ext = "." not in os.path.basename(target_clean)
    return is_md or is_dir or is_no_ext


def strip_fragment_and_query(target):
    if "#" in target:
        idx = target.index("#")
        return target[:idx], target[idx:]
    return target, ""


def find_inline_code_spans(line):
    spans = []
    for m in INLINE_CODE_PATTERN.finditer(line):
        spans.append((m.start(), m.end()))
    return spans


def is_match_in_code_span(match_start, match_end, code_spans):
    for span_start, span_end in code_spans:
        if match_start >= span_start and match_end <= span_end:
            return True
    return False


def get_code_block_ranges(lines):
    """Pair up ``` fences: (open_line_idx, close_line_idx). Odd fence is dropped."""
    fences = [i for i, line in enumerate(lines) if line.strip().startswith("```")]
    if len(fences) % 2 == 1:
        fences = fences[:-1]  # drop stray/unmatched fence
    return [(fences[i], fences[i+1]) for i in range(0, len(fences), 2)]


def is_in_code_block(line_idx, code_block_ranges):
    for start, end in code_block_ranges:
        if start < line_idx < end:
            return True
    return False


def fix_markdown_file(filepath, file_index, dry_run=False):
    rel_path = os.path.relpath(filepath, DATA_DIR)
    changes = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_lines = content.split("\n")
    new_lines = list(original_lines)
    code_block_ranges = get_code_block_ranges(original_lines)

    for line_idx, line in enumerate(original_lines):
        if is_in_code_block(line_idx, code_block_ranges):
            continue

        stripped = line.strip()
        if stripped.startswith("```"):
            continue

        code_spans = find_inline_code_spans(line)

        for m in LINK_PATTERN.finditer(line):
            full_match = m.group(0)
            link_text = m.group(1)
            link_target = m.group(2)

            if is_match_in_code_span(m.start(), m.end(), code_spans):
                continue

            target_clean = link_target.split('"')[0].strip()
            target_clean = target_clean.split("'")[0].strip()

            if not is_relative_internal_link(target_clean):
                continue

            target_path, fragment = strip_fragment_and_query(target_clean)

            if not target_path:
                continue

            is_dir_link = target_path.endswith("/")

            resolved_rel, was_mapped = resolve_link(rel_path, target_path, file_index)

            if resolved_rel:
                if is_dir_link and not resolved_rel.endswith(".md"):
                    new_target = "/" + resolved_rel.rstrip("/") + "/" + fragment
                else:
                    new_target = "/" + resolved_rel + fragment
            else:
                basename = os.path.basename(target_path)
                if basename in MISSING_FILE_MAP:
                    resolved_rel = MISSING_FILE_MAP[basename]
                else:
                    simple = os.path.normpath(target_path)
                    parts = [p for p in simple.split("/") if p and p != ".."]
                    resolved_rel = "/".join(parts)

                if is_dir_link:
                    new_target = "/" + resolved_rel.rstrip("/") + "/" + fragment
                else:
                    new_target = "/" + resolved_rel + fragment

                sys.stderr.write(
                    f"  ⚠ WARNING: Could not resolve '{target_clean}' from {rel_path}\n"
                    f"    → Using fallback: {new_target}\n"
                )

            old_full = f"[{link_text}]({link_target})"
            new_full = f"[{link_text}]({new_target})"

            if old_full != new_full:
                changes.append((line_idx + 1, old_full, new_full))

    changes_by_line = defaultdict(list)
    for line_num, old, new in changes:
        changes_by_line[line_num].append((old, new))

    total_replacements = 0
    for line_num, line_changes in sorted(changes_by_line.items()):
        line_idx = line_num - 1
        modified_line = new_lines[line_idx]
        for old, new in line_changes:
            if old in modified_line:
                modified_line = modified_line.replace(old, new, 1)
                total_replacements += 1
        new_lines[line_idx] = modified_line

    if total_replacements > 0:
        new_content = "\n".join(new_lines)
        if not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  ✓ Fixed {total_replacements} links in {rel_path}")
        else:
            print(f"  ✓ Would fix {total_replacements} links in {rel_path} (dry-run)")

    return changes


def main():
    dry_run = "--dry-run" in sys.argv
    rerun_only = False
    passed_files = set()

    if "--rerun" in sys.argv:
        rerun_only = True

    print("Building file index...")
    file_index = build_file_index(DATA_DIR)
    print(f"  Indexed {sum(len(v) for v in file_index.values())} .md files\n")

    total_changed = 0
    total_files_changed = 0

    for root, _dirs, files in os.walk(DATA_DIR):
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(root, fname)
            changes = fix_markdown_file(filepath, file_index, dry_run=dry_run)
            if changes:
                total_files_changed += 1
                total_changed += len(changes)

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Files modified: {total_files_changed}")
    print(f"  Total links fixed: {total_changed}")
    if dry_run:
        print(f"  (dry-run, no files written)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
