#!/usr/bin/env python3
"""
Comprehensive Code Syntax Validation Suite v1.0
Validates 60K+ code examples across Python, JavaScript, Go, Java, SQL, Bash

USAGE:
    python3 validate_syntax.py              # Full validation
    python3 validate_syntax.py --lang python  # Python only
    python3 validate_syntax.py --lang sql     # SQL only
    python3 validate_syntax.py --report       # Generate HTML report
"""

import os
import re
import sys
import subprocess
import json
import tempfile
import shutil
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ValidationResult:
    language: str
    filepath: str
    block_num: int
    valid: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    snippet: Optional[str] = None
    tool_used: Optional[str] = None

class ValidationStatus(Enum):
    VALID = "valid"
    FAILED = "failed"
    WARNING = "warning"
    TIMEOUT = "timeout"

# ============================================================================
# ABSTRACT BASE VALIDATOR
# ============================================================================

class BaseSyntaxValidator:
    """Abstract base for language validators"""

    def __init__(self, language: str):
        self.language = language
        self.tool_available = False
        self.tool_name = None
        self.check_tool_availability()

    def check_tool_availability(self):
        """Override in subclass"""
        raise NotImplementedError

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        """Override in subclass"""
        raise NotImplementedError

    def _run_subprocess(self, cmd: List[str], code: str, timeout: int = 10) -> Tuple[int, str]:
        """Helper to run external tool safely"""
        try:
            proc = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return proc.returncode, proc.stderr
        except subprocess.TimeoutExpired:
            return -1, "TIMEOUT"
        except Exception as e:
            return -2, str(e)

    def _temp_file(self, suffix: str) -> str:
        """Create temporary file"""
        return f"/tmp/{self.language}_{os.getpid()}_{suffix}"

# ============================================================================
# LANGUAGE VALIDATORS
# ============================================================================

class PythonValidator(BaseSyntaxValidator):
    """Validates Python syntax using ast.parse()"""

    def check_tool_availability(self):
        self.tool_available = True
        self.tool_name = "ast.parse() [built-in]"

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(
            language='python',
            filepath=filepath,
            block_num=block_num,
            valid=False,
            snippet=code[:80]
        )

        if not self.tool_available:
            result.warning = "Python not available"
            return result

        try:
            import ast
            ast.parse(code)
            result.valid = True
            result.tool_used = self.tool_name
        except SyntaxError as e:
            result.error = f"Line {e.lineno}: {e.msg}"
        except IndentationError as e:
            result.error = f"Indentation: {e.msg}"
        except Exception as e:
            result.error = f"Parse error: {str(e)[:100]}"

        return result


class JavaScriptValidator(BaseSyntaxValidator):
    """Validates JavaScript using node --check"""

    def check_tool_availability(self):
        result = subprocess.run(['which', 'node'], capture_output=True)
        self.tool_available = result.returncode == 0
        self.tool_name = "node --check"

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(
            language='javascript',
            filepath=filepath,
            block_num=block_num,
            valid=False,
            snippet=code[:80]
        )

        if not self.tool_available:
            result.warning = "Node.js not available"
            return result

        temp_file = self._temp_file('.js')
        try:
            with open(temp_file, 'w') as f:
                f.write(code)

            returncode, stderr = self._run_subprocess(['node', '--check', temp_file])

            if returncode == 0:
                result.valid = True
                result.tool_used = self.tool_name
            elif returncode == -1:
                result.warning = "Validation timeout"
            else:
                result.error = stderr[:200]
        except Exception as e:
            result.error = str(e)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return result


class TypeScriptValidator(BaseSyntaxValidator):
    """Validates TypeScript using tsc --noEmit"""

    def check_tool_availability(self):
        result = subprocess.run(['which', 'tsc'], capture_output=True)
        self.tool_available = result.returncode == 0
        self.tool_name = "tsc --noEmit"

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(
            language='typescript',
            filepath=filepath,
            block_num=block_num,
            valid=False,
            snippet=code[:80]
        )

        if not self.tool_available:
            result.warning = "TypeScript compiler not available"
            return result

        temp_file = self._temp_file('.ts')
        try:
            with open(temp_file, 'w') as f:
                f.write(code)

            returncode, stderr = self._run_subprocess(['tsc', '--noEmit', temp_file])

            if returncode == 0:
                result.valid = True
                result.tool_used = self.tool_name
            elif returncode == -1:
                result.warning = "Validation timeout"
            else:
                result.error = stderr[:200]
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return result


class SQLValidator(BaseSyntaxValidator):
    """Validates SQL using sqlglot (multi-dialect)"""

    def check_tool_availability(self):
        try:
            import sqlglot
            self.tool_available = True
            self.tool_name = "sqlglot"
        except ImportError:
            self.tool_available = False
            self.tool_name = None

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(
            language='sql',
            filepath=filepath,
            block_num=block_num,
            valid=False,
            snippet=code[:80]
        )

        if not self.tool_available:
            result.warning = "sqlglot not installed (pip install sqlglot)"
            return result

        try:
            import sqlglot

            # Detect dialect from filepath
            dialect = self._detect_dialect(filepath)

            # Parse SQL
            ast = sqlglot.parse_one(code, dialect=dialect)

            if ast:
                result.valid = True
                result.tool_used = f"{self.tool_name} ({dialect})"
            else:
                result.error = "Parse produced empty AST"
        except Exception as e:
            result.error = str(e)[:200]

        return result

    def _detect_dialect(self, filepath: str) -> str:
        """Detect SQL dialect from filepath"""
        if 'postgres' in filepath.lower():
            return 'postgres'
        elif 'mysql' in filepath.lower():
            return 'mysql'
        elif 'oracle' in filepath.lower():
            return 'oracle'
        elif 'sqlite' in filepath.lower():
            return 'sqlite'
        return 'postgres'  # default


class BashValidator(BaseSyntaxValidator):
    """Validates Bash using shellcheck or sh -n"""

    def check_tool_availability(self):
        # Try shellcheck first
        result = subprocess.run(['which', 'shellcheck'], capture_output=True)
        if result.returncode == 0:
            self.tool_available = True
            self.tool_name = "shellcheck"
            self.use_shellcheck = True
            return

        # Fallback to sh -n
        result = subprocess.run(['which', 'sh'], capture_output=True)
        self.tool_available = result.returncode == 0
        self.tool_name = "sh -n [fallback]"
        self.use_shellcheck = False

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(
            language='bash',
            filepath=filepath,
            block_num=block_num,
            valid=False,
            snippet=code[:80]
        )

        if not self.tool_available:
            result.warning = "Neither shellcheck nor sh available"
            return result

        temp_file = self._temp_file('.sh')
        try:
            with open(temp_file, 'w') as f:
                f.write(code)
            os.chmod(temp_file, 0o755)

            if self.use_shellcheck:
                returncode, stderr = self._run_subprocess(['shellcheck', temp_file])
            else:
                returncode, stderr = self._run_subprocess(['sh', '-n', temp_file])

            if returncode == 0:
                result.valid = True
                result.tool_used = self.tool_name
            elif returncode == -1:
                result.warning = "Validation timeout"
            else:
                result.error = stderr[:200]
        except Exception as e:
            result.error = str(e)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return result


class GoValidator(BaseSyntaxValidator):
    """Validates Go using go build"""

    def check_tool_availability(self):
        result = subprocess.run(['which', 'go'], capture_output=True)
        self.tool_available = result.returncode == 0
        self.tool_name = "go build"

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(
            language='go',
            filepath=filepath,
            block_num=block_num,
            valid=False,
            snippet=code[:80]
        )

        if not self.tool_available:
            result.warning = "Go toolchain not available"
            return result

        temp_dir = self._temp_file('_dir')
        temp_file = os.path.join(temp_dir, 'main.go')

        try:
            os.makedirs(temp_dir, exist_ok=True)

            # Wrap code if needed
            wrapped = self._wrap_code(code)
            with open(temp_file, 'w') as f:
                f.write(wrapped)

            returncode, stderr = self._run_subprocess(
                ['go', 'build', '-o', '/dev/null', temp_file],
                "",
                timeout=15
            )

            if returncode == 0:
                result.valid = True
                result.tool_used = self.tool_name
            elif returncode == -1:
                result.warning = "Validation timeout"
            else:
                result.error = stderr[:200]
        except Exception as e:
            result.error = str(e)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        return result

    def _wrap_code(self, code: str) -> str:
        """Wrap code fragment in valid Go package"""
        if 'package ' not in code:
            return f"package main\n\n{code}"
        return code


class JavaValidator(BaseSyntaxValidator):
    """Validates Java using javac"""

    def check_tool_availability(self):
        result = subprocess.run(['which', 'javac'], capture_output=True)
        self.tool_available = result.returncode == 0
        self.tool_name = "javac"

    def validate(self, code: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(
            language='java',
            filepath=filepath,
            block_num=block_num,
            valid=False,
            snippet=code[:80]
        )

        if not self.tool_available:
            result.warning = "Java compiler not available"
            return result

        temp_dir = self._temp_file('_dir')
        temp_file = os.path.join(temp_dir, 'Validate.java')

        try:
            os.makedirs(temp_dir, exist_ok=True)

            wrapped = self._wrap_code(code)
            with open(temp_file, 'w') as f:
                f.write(wrapped)

            returncode, stderr = self._run_subprocess(
                ['javac', '-d', '/dev/null', temp_file],
                "",
                timeout=15
            )

            if returncode == 0:
                result.valid = True
                result.tool_used = self.tool_name
            elif returncode == -1:
                result.warning = "Validation timeout"
            else:
                result.error = stderr[:200]
        except Exception as e:
            result.error = str(e)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        return result

    def _wrap_code(self, code: str) -> str:
        """Wrap code in valid Java class"""
        if 'class ' not in code and 'interface ' not in code:
            return f"public class Validate {{ {code} }}"
        return code


# ============================================================================
# MAIN VALIDATION ENGINE
# ============================================================================

class ValidationEngine:
    def __init__(self):
        self.validators = {
            'python': PythonValidator('python'),
            'javascript': JavaScriptValidator('javascript'),
            'typescript': TypeScriptValidator('typescript'),
            'sql': SQLValidator('sql'),
            'bash': BashValidator('bash'),
            'go': GoValidator('go'),
            'java': JavaValidator('java'),
        }
        self.results: List[ValidationResult] = []
        self.start_time = None

    def extract_and_validate(self, markdown_dir='./data', languages=None):
        """Extract code blocks and validate them"""
        self.start_time = datetime.now()

        patterns = {
            'python': r'```python\n(.*?)```',
            'javascript': r'```(?:javascript|js)\n(.*?)```',
            'typescript': r'```(?:typescript|ts)\n(.*?)```',
            'sql': r'```(?:sql|postgresql|mysql|oracle)\n(.*?)```',
            'bash': r'```(?:bash|sh|shell)\n(.*?)```',
            'go': r'```(?:go|golang)\n(.*?)```',
            'java': r'```java\n(.*?)```',
        }

        # Filter languages if specified
        if languages:
            patterns = {k: v for k, v in patterns.items() if k in languages}

        file_count = 0
        block_count = 0

        for root, dirs, files in os.walk(markdown_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    file_count += 1

                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        for lang, pattern in patterns.items():
                            blocks = re.findall(pattern, content, re.DOTALL)
                            for block_num, block in enumerate(blocks, 1):
                                block_count += 1
                                if lang in self.validators:
                                    validator = self.validators[lang]
                                    rel_path = os.path.relpath(filepath, markdown_dir)
                                    result = validator.validate(block, rel_path, block_num)
                                    self.results.append(result)
                    except Exception as e:
                        print(f"Error processing {filepath}: {e}", file=sys.stderr)

        return file_count, block_count

    def generate_json_report(self, output_file='validation_report.json'):
        """Generate JSON report"""
        summary = self._summarize()

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'by_language': self._group_by_language(),
            'failures': [asdict(r) for r in self.results if not r.valid and r.error],
            'warnings': [asdict(r) for r in self.results if r.warning],
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def print_console_report(self):
        """Print human-readable console report"""
        summary = self._summarize()

        print("\n" + "="*80)
        print(f"CODE SYNTAX VALIDATION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        print(f"\nTotal Blocks Validated: {len(self.results)}")
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"Time Elapsed: {elapsed:.2f}s")

        print("\n" + "-"*80)
        print("VALIDATION RESULTS BY LANGUAGE")
        print("-"*80)

        print(f"\n{'Language':<15} {'Total':<10} {'Valid':<10} {'Failed':<10} {'Warning':<10} {'Rate':<10}")
        print("-"*80)

        for lang, stats in sorted(summary.items()):
            total = stats['total']
            valid = stats['valid']
            failed = stats['failed']
            warning = stats['warning']
            rate = f"{(valid/total*100):.1f}%" if total > 0 else "N/A"

            print(f"{lang:<15} {total:<10} {valid:<10} {failed:<10} {warning:<10} {rate:<10}")

        if any(r.error for r in self.results):
            print("\n" + "-"*80)
            print("FAILURES (first 10)")
            print("-"*80)
            failures = [r for r in self.results if r.error][:10]
            for f in failures:
                print(f"\n{f.language.upper()}: {f.filepath}:{f.block_num}")
                print(f"  Error: {f.error}")

        print("\n" + "="*80)

    def _summarize(self) -> Dict:
        """Generate summary statistics"""
        by_lang = defaultdict(lambda: {'total': 0, 'valid': 0, 'failed': 0, 'warning': 0})

        for result in self.results:
            by_lang[result.language]['total'] += 1
            if result.valid:
                by_lang[result.language]['valid'] += 1
            elif result.error:
                by_lang[result.language]['failed'] += 1
            elif result.warning:
                by_lang[result.language]['warning'] += 1

        return dict(by_lang)

    def _group_by_language(self):
        """Group results by language"""
        grouped = defaultdict(list)
        for result in self.results:
            grouped[result.language].append(asdict(result))
        return dict(grouped)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Validate code syntax in markdown files')
    parser.add_argument('--lang', help='Validate only specific language (python, javascript, sql, etc.)')
    parser.add_argument('--dir', default='./data', help='Markdown directory to scan')
    parser.add_argument('--json', help='Output JSON report to file')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')

    args = parser.parse_args()

    engine = ValidationEngine()

    print(f"Scanning {args.dir} for code blocks...")
    languages = [args.lang] if args.lang else None
    file_count, block_count = engine.extract_and_validate(args.dir, languages)

    print(f"Found {block_count} code blocks in {file_count} files")
    print("Validating...")

    if not args.quiet:
        engine.print_console_report()

    if args.json:
        report = engine.generate_json_report(args.json)
        print(f"\nJSON report saved to {args.json}")
