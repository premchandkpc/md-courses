#!/usr/bin/env python3
"""Code Syntax Validator for md-courses library"""

import subprocess, re, json, sys, tempfile
from pathlib import Path
from typing import Dict, List, Tuple

class PythonValidator:
    def validate(self, code: str) -> Tuple[bool, str]:
        try:
            import ast
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)

class JavaScriptValidator:
    def validate(self, code: str) -> Tuple[bool, str]:
        try:
            result = subprocess.run(["node", "--check"], input=code, capture_output=True, text=True, timeout=5)
            return result.returncode == 0, result.stderr.strip()
        except:
            return False, "Node validator unavailable"

class SQLValidator:
    def validate(self, code: str) -> Tuple[bool, str]:
        try:
            import sqlglot
            sqlglot.parse_one(code)
            return True, ""
        except:
            return False, "SQL parse failed"

class BashValidator:
    def validate(self, code: str) -> Tuple[bool, str]:
        try:
            result = subprocess.run(["sh", "-n"], input=code, capture_output=True, text=True, timeout=5)
            return result.returncode == 0, result.stderr.strip()
        except:
            return False, "Bash validator unavailable"

class ValidationEngine:
    VALIDATORS = {
        'python': PythonValidator(),
        'javascript': JavaScriptValidator(),
        'sql': SQLValidator(),
        'bash': BashValidator(),
    }

    PATTERNS = {
        'python': r'```python\n(.*?)\n```',
        'javascript': r'```(?:javascript|js)\n(.*?)\n```',
        'sql': r'```(?:sql|postgres|mysql)\n(.*?)\n```',
        'bash': r'```(?:bash|sh)\n(.*?)\n```',
    }

    def validate_file(self, file_path: str) -> Dict:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        results = {'file': file_path, 'blocks': {}}
        for lang, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                results['blocks'][lang] = []
                validator = self.VALIDATORS.get(lang)
                for i, code in enumerate(matches):
                    passed, error = validator.validate(code) if validator else (True, "")
                    results['blocks'][lang].append({'num': i, 'passed': passed, 'error': error})
        return results

    def validate_directory(self, directory: str):
        all_results = []
        for md_file in Path(directory).rglob('*.md'):
            all_results.append(self.validate_file(str(md_file)))

        # Summarize
        total_blocks = sum(sum(len(v) for v in r['blocks'].values()) for r in all_results)
        passed_blocks = sum(sum(1 for b in v if b['passed']) for r in all_results for v in r['blocks'].values())

        print(f"Total blocks: {total_blocks}")
        print(f"Passed: {passed_blocks}")
        print(f"Pass rate: {(passed_blocks/total_blocks*100):.1f}%" if total_blocks > 0 else "0%")

        # Show failures
        failures = [r for r in all_results if any(not b['passed'] for v in r['blocks'].values() for b in v)]
        if failures:
            print(f"\nFailed files ({len(failures)}):")
            for r in failures[:10]:
                print(f"  {r['file']}")

if __name__ == '__main__':
    directory = sys.argv[1] if len(sys.argv) > 1 else '/Users/ramyachowdary/Documents/prem-work/md-courses/data'
    ValidationEngine().validate_directory(directory)
