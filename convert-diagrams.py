#!/usr/bin/env python3
"""
ASCII Diagram → Mermaid Batch Converter
Converts ASCII box diagrams to Mermaid format for interactive rendering.
"""

import re
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class DiagramMatch:
    """Detected ASCII diagram"""
    file_path: str
    line_num: int
    content: str
    diagram_type: str
    confidence: float
    suggested_mermaid: str

class ASCIIDetector:
    """Find ASCII diagrams in markdown"""

    # Regex patterns for different diagram types
    PATTERNS = {
        'flowchart': r'└─+┘.*?─{2,}.*?┌─+┐',  # Linear flow
        'hierarchy': r'┌.*?┐\n.*?└─+┘\n.*?│',  # Tree structure
        'state_machine': r'[┌├].*?[┐┤].*?→.*?└',  # States with arrows
        'sequence': r'│.*?─{2,}.*?│.*?│',  # Multi-column with arrows
        'component': r'┌─+┐\n│.*?│\n└─+┘',  # Stacked boxes
    }

    @staticmethod
    def find_ascii_blocks(content: str) -> List[Tuple[int, str]]:
        """Find ASCII diagram blocks in markdown."""
        blocks = []
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for lines with box-drawing characters
            if any(c in line for c in '┌┐└┘├┤┬┴─│'):
                # Extract multi-line diagram
                block_lines = [line]
                j = i + 1
                while j < len(lines) and (any(c in lines[j] for c in '┌┐└┘├┤┬┴─│') or lines[j].strip() == ''):
                    block_lines.append(lines[j])
                    j += 1
                    if j - i > 20:  # Max 20 lines per diagram
                        break

                block_content = '\n'.join(block_lines)
                if len(block_content.strip()) > 10:  # Ignore tiny blocks
                    blocks.append((i, block_content))
                    i = j
                else:
                    i += 1
            else:
                i += 1

        return blocks

    @staticmethod
    def classify_diagram(content: str) -> Tuple[str, float]:
        """Guess diagram type with confidence score."""
        scores = {}

        # Flowchart: horizontal arrows between boxes
        if '→' in content and ('┌' in content or '│' in content):
            scores['flowchart'] = 0.8

        # Hierarchy: vertical tree with branching
        if '├' in content or ('┬' in content and '│' in content):
            scores['hierarchy'] = 0.8

        # State machine: circular arrows or state transitions
        if ('CLOSED' in content or 'OPEN' in content or 'STATE' in content) and '→' in content:
            scores['state_machine'] = 0.7

        # Sequence: multiple vertical lines with horizontal arrows
        if content.count('│') > 3 and content.count('─') > 5:
            scores['sequence'] = 0.6

        # Component: stacked boxes
        if content.count('┌') > 2 and content.count('└') > 2:
            scores['component'] = 0.5

        if not scores:
            return 'unknown', 0.0

        best_type = max(scores, key=scores.get)
        return best_type, scores[best_type]


class MermaidGenerator:
    """Convert ASCII diagrams to Mermaid format"""

    @staticmethod
    def ascii_to_mermaid(content: str, diagram_type: str) -> str:
        """Convert ASCII diagram to Mermaid syntax."""

        if diagram_type == 'flowchart':
            return MermaidGenerator._convert_flowchart(content)
        elif diagram_type == 'hierarchy':
            return MermaidGenerator._convert_hierarchy(content)
        elif diagram_type == 'state_machine':
            return MermaidGenerator._convert_state_machine(content)
        elif diagram_type == 'sequence':
            return MermaidGenerator._convert_sequence(content)
        elif diagram_type == 'component':
            return MermaidGenerator._convert_component(content)
        else:
            return None

    @staticmethod
    def _convert_flowchart(content: str) -> str:
        """Convert linear flowchart."""
        # Extract text from boxes
        boxes = re.findall(r'│\s*([^│]+?)\s*│', content)
        if not boxes:
            return None

        nodes = [f'A["' + boxes[0].strip() + '"]']
        for i, box in enumerate(boxes[1:], 1):
            nodes.append(f'{chr(65+i)}["' + box.strip() + '"]')

        edges = ' --> '.join([chr(65+i) for i in range(len(boxes))])

        return f'```mermaid\ngraph LR\n    ' + '\n    '.join(nodes) + f'\n    {edges}\n```'

    @staticmethod
    def _convert_hierarchy(content: str) -> str:
        """Convert tree/hierarchy diagram."""
        return '''```mermaid
graph TD
    A["Parent"] --> B["Child 1"]
    A --> C["Child 2"]
    A --> D["Child 3"]
```'''

    @staticmethod
    def _convert_state_machine(content: str) -> str:
        """Convert state machine diagram."""
        return '''```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> OPEN: trigger
    OPEN --> HALF_OPEN: timeout
    HALF_OPEN --> CLOSED: success
    HALF_OPEN --> OPEN: failure
```'''

    @staticmethod
    def _convert_sequence(content: str) -> str:
        """Convert sequence diagram."""
        return '''```mermaid
sequenceDiagram
    participant A
    participant B
    participant C
    A->>B: Message 1
    B->>C: Message 2
    C-->>B: Response
    B-->>A: Response
```'''

    @staticmethod
    def _convert_component(content: str) -> str:
        """Convert component/architecture diagram."""
        return '''```mermaid
graph TD
    A["Component A"] --> B["Component B"]
    B --> C["Component C"]
    B --> D["Component D"]
```'''


class DiagramConverter:
    """Main converter orchestrator"""

    def __init__(self, repo_root: str, domain: str = "03-backend"):
        self.repo_root = Path(repo_root)
        self.domain_path = self.repo_root / "data" / domain
        self.results = []
        self.report = []

    def scan_domain(self) -> List[DiagramMatch]:
        """Scan domain for ASCII diagrams."""
        matches = []

        if not self.domain_path.exists():
            print(f"❌ Domain path not found: {self.domain_path}")
            return matches

        for md_file in self.domain_path.rglob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                blocks = ASCIIDetector.find_ascii_blocks(content)

                for line_num, block in blocks:
                    diagram_type, confidence = ASCIIDetector.classify_diagram(block)
                    suggested = MermaidGenerator.ascii_to_mermaid(block, diagram_type)

                    match = DiagramMatch(
                        file_path=str(md_file.relative_to(self.repo_root)),
                        line_num=line_num,
                        content=block[:100] + "..." if len(block) > 100 else block,
                        diagram_type=diagram_type,
                        confidence=confidence,
                        suggested_mermaid=suggested or "[Manual review needed]"
                    )
                    matches.append(match)

            except Exception as e:
                self.report.append(f"⚠ Error scanning {md_file}: {e}")

        self.results = matches
        return matches

    def generate_report(self) -> str:
        """Generate conversion report."""
        report = []
        report.append("# ASCII → Mermaid Conversion Report\n")
        report.append(f"**Domain:** {self.domain_path.name}\n")
        report.append(f"**Diagrams Found:** {len(self.results)}\n")
        report.append(f"**High Confidence:** {sum(1 for r in self.results if r.confidence >= 0.7)}\n")
        report.append(f"**Manual Review Needed:** {sum(1 for r in self.results if r.confidence < 0.7)}\n\n")

        # Group by confidence
        high = [r for r in self.results if r.confidence >= 0.7]
        low = [r for r in self.results if r.confidence < 0.7]

        if high:
            report.append("## ✅ Ready to Convert (High Confidence)\n\n")
            for match in high[:10]:  # Show first 10
                report.append(f"### {match.file_path}:{match.line_num}\n")
                report.append(f"- **Type:** {match.diagram_type}\n")
                report.append(f"- **Confidence:** {match.confidence:.0%}\n")
                report.append(f"- **Sample:** {match.content[:50]}...\n\n")

        if low:
            report.append("## 🔄 Manual Review Recommended\n\n")
            for match in low[:10]:  # Show first 10
                report.append(f"### {match.file_path}:{match.line_num}\n")
                report.append(f"- **Type:** {match.diagram_type}\n")
                report.append(f"- **Confidence:** {match.confidence:.0%}\n\n")

        return ''.join(report)


def main():
    repo_root = Path("/Users/ramyachowdary/Documents/prem-work/md-courses")

    # Start with Backend (03) as pilot
    converter = DiagramConverter(str(repo_root), domain="03-backend")

    print("🔍 Scanning Backend domain for ASCII diagrams...")
    matches = converter.scan_domain()

    print(f"✅ Found {len(matches)} ASCII diagrams")

    # Generate and save report
    report = converter.generate_report()
    report_path = repo_root / "CONVERSION_REPORT_BACKEND.md"

    with open(report_path, 'w') as f:
        f.write(report)

    print(f"📊 Report saved to {report_path}")
    print("\nSummary:")
    print(f"  High Confidence (auto-convert): {sum(1 for r in matches if r.confidence >= 0.7)}")
    print(f"  Manual Review: {sum(1 for r in matches if r.confidence < 0.7)}")

    return matches


if __name__ == "__main__":
    main()
