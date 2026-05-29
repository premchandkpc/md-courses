#!/usr/bin/env python3
"""
Code Syntax Validation Analysis and Script Generator
Analyzes 60K+ code examples across 437 markdown files
Identifies languages/domains needing validation, proposes structure
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ============================================================================
# PHASE 1: ANALYZE CODE DISTRIBUTION
# ============================================================================

class CodeAnalyzer:
    def __init__(self, root_dir='./data'):
        self.root_dir = root_dir
        self.lang_counts = defaultdict(int)
        self.domain_counts = defaultdict(lambda: defaultdict(int))
        self.file_examples = defaultdict(list)
        self.code_blocks = defaultdict(list)

    def extract_code_blocks(self):
        """Extract and catalog all code blocks by language"""
        patterns = {
            'python': r'```python\n(.*?)```',
            'javascript': r'```(?:javascript|js)\n(.*?)```',
            'typescript': r'```(?:typescript|ts)\n(.*?)```',
            'go': r'```(?:go|golang)\n(.*?)```',
            'java': r'```java\n(.*?)```',
            'sql': r'```(?:sql|postgresql|mysql|oracle)\n(.*?)```',
            'bash': r'```(?:bash|sh|shell)\n(.*?)```',
            'html': r'```(?:html|xml)\n(.*?)```',
            'css': r'```css\n(.*?)```',
            'json': r'```json\n(.*?)```',
            'yaml': r'```(?:yaml|yml)\n(.*?)```',
            'dockerfile': r'```(?:dockerfile|docker)\n(.*?)```',
            'graphql': r'```graphql\n(.*?)```',
            'c': r'```c\n(.*?)```',
            'cpp': r'```(?:cpp|c\+\+)\n(.*?)```',
        }

        md_files = 0
        total_blocks = 0

        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.md'):
                    md_files += 1
                    domain = root.split(os.sep)[1] if len(root.split(os.sep)) > 1 else 'root'
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.root_dir)

                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Simple block counting
                        for lang, pattern in patterns.items():
                            matches = re.findall(r'```' + lang, content)
                            count = len(matches)
                            if count > 0:
                                self.lang_counts[lang] += count
                                self.domain_counts[domain][lang] += count
                                self.file_examples[lang].append(rel_path)
                                total_blocks += count
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}", file=sys.stderr)

        return md_files, total_blocks

    def print_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("CODE SYNTAX VALIDATION ANALYSIS REPORT")
        print("60K+ Code Examples Across 437 Markdown Files")
        print("="*80 + "\n")

        md_files, total_blocks = self.extract_code_blocks()

        print(f"Total Markdown Files Analyzed: {md_files}")
        print(f"Total Code Blocks Found: {total_blocks}\n")

        # Language Distribution
        print("-" * 80)
        print("PHASE 1: LANGUAGE DISTRIBUTION")
        print("-" * 80)
        sorted_langs = sorted(self.lang_counts.items(), key=lambda x: x[1], reverse=True)

        print(f"\n{'Language':<15} {'Blocks':<10} {'%':<8} {'Risk Level':<20} {'Priority':<10}")
        print("-" * 80)

        risk_levels = {
            'python': 'LOW',
            'javascript': 'LOW',
            'typescript': 'LOW',
            'go': 'MEDIUM',
            'java': 'MEDIUM',
            'sql': 'HIGH',  # Complex dialects
            'bash': 'HIGH',  # Environment-dependent
            'html': 'LOW',
            'css': 'LOW',
            'json': 'LOW',
            'yaml': 'MEDIUM',
            'dockerfile': 'MEDIUM',
            'graphql': 'MEDIUM',
            'c': 'HIGH',
            'cpp': 'HIGH',
        }

        priority_map = {'LOW': 3, 'MEDIUM': 2, 'HIGH': 1}

        for lang, count in sorted_langs:
            if count > 0:
                pct = (count / total_blocks * 100) if total_blocks > 0 else 0
                risk = risk_levels.get(lang, 'UNKNOWN')
                priority = priority_map.get(risk, 99)
                print(f"{lang:<15} {count:<10} {pct:>6.1f}% {risk:<20} P{priority}")

        # Domain Distribution
        print("\n" + "-" * 80)
        print("PHASE 2: DOMAIN-SPECIFIC DISTRIBUTION (Top Domains)")
        print("-" * 80 + "\n")

        sorted_domains = sorted(self.domain_counts.items(),
                               key=lambda x: sum(x[1].values()),
                               reverse=True)[:8]

        for domain, langs in sorted_domains:
            total_in_domain = sum(langs.values())
            print(f"\n{domain}/ [{total_in_domain} blocks]")
            for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    print(f"  - {lang}: {count}")

        # High-Risk Findings
        print("\n" + "-" * 80)
        print("PHASE 3: HIGH-RISK DOMAINS (Incomplete Syntax Checks = Higher Priority)")
        print("-" * 80 + "\n")

        high_risk_langs = ['sql', 'bash', 'c', 'cpp', 'dockerfile']
        for lang in high_risk_langs:
            if lang in self.lang_counts and self.lang_counts[lang] > 0:
                print(f"\n[HIGH-RISK] {lang.upper()}")
                print(f"  - Blocks Found: {self.lang_counts[lang]}")
                print(f"  - Validation Challenge: {self._get_validation_challenge(lang)}")
                print(f"  - Tools Available: {self._get_available_tools(lang)}")
                print(f"  - Sample Files: {', '.join(self.file_examples[lang][:3])}")

    def _get_validation_challenge(self, lang):
        """Get specific validation challenges per language"""
        challenges = {
            'sql': 'Multiple dialects (PostgreSQL, MySQL, Oracle), vendor-specific syntax',
            'bash': 'Environment-dependent, requires shell context, complex glob patterns',
            'c': 'Complex preprocessing, platform-specific features, undefined behavior',
            'cpp': 'Template syntax, overload resolution, version-specific features (C++11→23)',
            'dockerfile': 'Order-dependent, requires base image context, COPY/ADD path validation',
            'java': 'Generics, type erasure, version-dependent features',
            'go': 'Interface satisfaction, type system, package resolution',
            'python': 'Indentation-sensitive, version-dependent (2 vs 3), type hints optional',
        }
        return challenges.get(lang, 'Unknown')

    def _get_available_tools(self, lang):
        """Get available validation tools per language"""
        tools = {
            'sql': 'sqlparse, pgvalidate, sqlglot (multi-dialect)',
            'bash': 'shellcheck, sh -n (syntax-only), shfmt',
            'c': 'gcc -fsyntax-only, clang --parse-only, cppcheck',
            'cpp': 'g++ -fsyntax-only, clang++ --parse-only, cppcheck',
            'dockerfile': 'hadolint, docker build --dry-run (requires Docker)',
            'java': 'javac -d /tmp, eclipse compiler (ecj)',
            'go': 'go build, go vet, gofmt',
            'python': 'python -m py_compile, ast.parse(), mypy (with stubs)',
            'javascript': 'node --check, esprima, acorn',
            'typescript': 'tsc --noEmit, ts-node',
            'json': 'jq, python -m json.tool',
            'yaml': 'yamllint, python -m yaml',
        }
        return tools.get(lang, 'Unknown')

    def generate_validation_script(self):
        """Generate modular validation script structure"""
        script_content = '''#!/usr/bin/env python3
"""
Comprehensive Code Syntax Validation Suite
Validates 60K+ code examples across Python, JavaScript, Go, Java, SQL, Bash
"""

import os
import re
import sys
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from enum import Enum

# ============================================================================
# LANGUAGE-SPECIFIC VALIDATORS
# ============================================================================

class ValidationResult:
    def __init__(self, language: str, filepath: str, block_num: int):
        self.language = language
        self.filepath = filepath
        self.block_num = block_num
        self.valid = False
        self.error = None
        self.warning = None
        self.code_snippet = None

class BaseSyntaxValidator:
    """Base class for all validators"""
    def __init__(self, language: str):
        self.language = language
        self.tool_available = False
        self.check_tool_availability()

    def check_tool_availability(self):
        """Check if required validation tool is installed"""
        raise NotImplementedError

    def validate(self, code_block: str) -> ValidationResult:
        """Validate a code block"""
        raise NotImplementedError

# ============================================================================
# PYTHON VALIDATOR
# ============================================================================

class PythonValidator(BaseSyntaxValidator):
    """Validates Python syntax using ast.parse()"""
    def __init__(self):
        super().__init__('python')

    def check_tool_availability(self):
        self.tool_available = True  # Built-in

    def validate(self, code_block: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(self.language, filepath, block_num)
        result.code_snippet = code_block[:100]

        try:
            import ast
            ast.parse(code_block)
            result.valid = True
        except SyntaxError as e:
            result.valid = False
            result.error = f"SyntaxError at line {e.lineno}: {e.msg}"
        except IndentationError as e:
            result.valid = False
            result.error = f"IndentationError: {e.msg}"

        return result

# ============================================================================
# JAVASCRIPT / TYPESCRIPT VALIDATOR
# ============================================================================

class JavaScriptValidator(BaseSyntaxValidator):
    """Validates JavaScript/TypeScript using node --check"""
    def __init__(self, language='javascript'):
        self.language = language
        super().__init__(language)

    def check_tool_availability(self):
        result = subprocess.run(['which', 'node'], capture_output=True)
        self.tool_available = result.returncode == 0

    def validate(self, code_block: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(self.language, filepath, block_num)
        result.code_snippet = code_block[:100]

        if not self.tool_available:
            result.warning = "Node.js not available"
            return result

        # Write to temp file
        temp_file = f"/tmp/validate_{block_num}.{self.language}"
        try:
            with open(temp_file, 'w') as f:
                f.write(code_block)

            proc = subprocess.run(
                ['node', '--check', temp_file],
                capture_output=True, text=True, timeout=5
            )

            if proc.returncode == 0:
                result.valid = True
            else:
                result.error = proc.stderr
        except subprocess.TimeoutExpired:
            result.error = "Validation timeout"
        except Exception as e:
            result.error = str(e)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return result

# ============================================================================
# SQL VALIDATOR
# ============================================================================

class SQLValidator(BaseSyntaxValidator):
    """Validates SQL syntax using sqlglot (multi-dialect)"""
    def __init__(self):
        super().__init__('sql')

    def check_tool_availability(self):
        try:
            import sqlglot
            self.tool_available = True
        except ImportError:
            self.tool_available = False

    def validate(self, code_block: str, filepath: str, block_num: int,
                dialect='postgres') -> ValidationResult:
        result = ValidationResult(self.language, filepath, block_num)
        result.code_snippet = code_block[:100]

        if not self.tool_available:
            result.warning = "sqlglot not installed (pip install sqlglot)"
            return result

        try:
            import sqlglot
            # Parse SQL (detects syntax errors)
            ast = sqlglot.parse_one(code_block, dialect=dialect)
            result.valid = ast is not None
        except Exception as e:
            result.error = str(e)

        return result

# ============================================================================
# BASH VALIDATOR
# ============================================================================

class BashValidator(BaseSyntaxValidator):
    """Validates Bash syntax using shellcheck or sh -n"""
    def __init__(self):
        super().__init__('bash')

    def check_tool_availability(self):
        # Check for shellcheck first (preferred)
        result = subprocess.run(['which', 'shellcheck'], capture_output=True)
        self.tool_available = result.returncode == 0
        self.use_shellcheck = self.tool_available

        if not self.tool_available:
            # Fall back to sh -n
            result = subprocess.run(['which', 'sh'], capture_output=True)
            self.tool_available = result.returncode == 0
            self.use_shellcheck = False

    def validate(self, code_block: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(self.language, filepath, block_num)
        result.code_snippet = code_block[:100]

        if not self.tool_available:
            result.warning = "Neither shellcheck nor sh available"
            return result

        temp_file = f"/tmp/validate_{block_num}.sh"
        try:
            with open(temp_file, 'w') as f:
                f.write(code_block)
            os.chmod(temp_file, 0o755)

            if self.use_shellcheck:
                proc = subprocess.run(
                    ['shellcheck', temp_file],
                    capture_output=True, text=True, timeout=5
                )
            else:
                proc = subprocess.run(
                    ['sh', '-n', temp_file],
                    capture_output=True, text=True, timeout=5
                )

            result.valid = proc.returncode == 0
            if proc.returncode != 0:
                result.error = proc.stderr
        except subprocess.TimeoutExpired:
            result.error = "Validation timeout"
        except Exception as e:
            result.error = str(e)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        return result

# ============================================================================
# GO VALIDATOR
# ============================================================================

class GoValidator(BaseSyntaxValidator):
    """Validates Go syntax using go build"""
    def __init__(self):
        super().__init__('go')

    def check_tool_availability(self):
        result = subprocess.run(['which', 'go'], capture_output=True)
        self.tool_available = result.returncode == 0

    def validate(self, code_block: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(self.language, filepath, block_num)
        result.code_snippet = code_block[:100]

        if not self.tool_available:
            result.warning = "Go toolchain not available"
            return result

        temp_dir = f"/tmp/go_validate_{block_num}"
        temp_file = f"{temp_dir}/main.go"

        try:
            os.makedirs(temp_dir, exist_ok=True)

            # Wrap code in main package if needed
            wrapped_code = self._wrap_code(code_block)
            with open(temp_file, 'w') as f:
                f.write(wrapped_code)

            proc = subprocess.run(
                ['go', 'build', '-o', '/dev/null', temp_file],
                capture_output=True, text=True, timeout=10, cwd=temp_dir
            )

            result.valid = proc.returncode == 0
            if proc.returncode != 0:
                result.error = proc.stderr
        except subprocess.TimeoutExpired:
            result.error = "Validation timeout"
        except Exception as e:
            result.error = str(e)
        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        return result

    def _wrap_code(self, code: str) -> str:
        """Wrap code fragment in valid Go package/main"""
        if 'package ' not in code:
            return f"package main\\n\\n{code}"
        return code

# ============================================================================
# JAVA VALIDATOR
# ============================================================================

class JavaValidator(BaseSyntaxValidator):
    """Validates Java syntax using javac"""
    def __init__(self):
        super().__init__('java')

    def check_tool_availability(self):
        result = subprocess.run(['which', 'javac'], capture_output=True)
        self.tool_available = result.returncode == 0

    def validate(self, code_block: str, filepath: str, block_num: int) -> ValidationResult:
        result = ValidationResult(self.language, filepath, block_num)
        result.code_snippet = code_block[:100]

        if not self.tool_available:
            result.warning = "Java compiler not available"
            return result

        temp_dir = f"/tmp/java_validate_{block_num}"
        temp_file = f"{temp_dir}/Validate.java"

        try:
            os.makedirs(temp_dir, exist_ok=True)

            # Extract class name or create wrapper
            wrapped_code = self._wrap_code(code_block)
            with open(temp_file, 'w') as f:
                f.write(wrapped_code)

            proc = subprocess.run(
                ['javac', '-d', '/dev/null', temp_file],
                capture_output=True, text=True, timeout=10
            )

            result.valid = proc.returncode == 0
            if proc.returncode != 0:
                result.error = proc.stderr
        except subprocess.TimeoutExpired:
            result.error = "Validation timeout"
        except Exception as e:
            result.error = str(e)
        finally:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        return result

    def _wrap_code(self, code: str) -> str:
        """Wrap code in valid Java class"""
        if 'class ' not in code:
            return f"class Validate {{ {code} }}"
        return code

# ============================================================================
# MAIN VALIDATION ENGINE
# ============================================================================

class ValidationEngine:
    def __init__(self):
        self.validators = {
            'python': PythonValidator(),
            'javascript': JavaScriptValidator('javascript'),
            'typescript': JavaScriptValidator('typescript'),
            'go': GoValidator(),
            'java': JavaValidator(),
            'sql': SQLValidator(),
            'bash': BashValidator(),
        }
        self.results = []

    def extract_and_validate(self, markdown_dir='./data'):
        """Extract code blocks from all markdown files and validate"""
        patterns = {
            'python': r'```python\\n(.*?)```',
            'javascript': r'```(?:javascript|js)\\n(.*?)```',
            'typescript': r'```(?:typescript|ts)\\n(.*?)```',
            'go': r'```(?:go|golang)\\n(.*?)```',
            'java': r'```java\\n(.*?)```',
            'sql': r'```(?:sql|postgresql|mysql|oracle)\\n(.*?)```',
            'bash': r'```(?:bash|sh|shell)\\n(.*?)```',
        }

        for root, dirs, files in os.walk(markdown_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        for lang, pattern in patterns.items():
                            blocks = re.findall(pattern, content, re.DOTALL)
                            for block_num, block in enumerate(blocks, 1):
                                if lang in self.validators:
                                    validator = self.validators[lang]
                                    result = validator.validate(block, filepath, block_num)
                                    self.results.append(result)
                    except Exception as e:
                        print(f"Error processing {filepath}: {e}", file=sys.stderr)

    def generate_report(self, output_file='validation_report.json'):
        """Generate JSON report of validation results"""
        report = {
            'summary': self._generate_summary(),
            'results_by_language': self._group_by_language(),
            'failures': self._get_failures(),
            'warnings': self._get_warnings(),
        }

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def _generate_summary(self):
        """Generate summary statistics"""
        by_lang = defaultdict(lambda: {'total': 0, 'valid': 0, 'failed': 0})

        for result in self.results:
            by_lang[result.language]['total'] += 1
            if result.valid:
                by_lang[result.language]['valid'] += 1
            else:
                by_lang[result.language]['failed'] += 1

        return dict(by_lang)

    def _group_by_language(self):
        """Group results by language"""
        grouped = defaultdict(list)
        for result in self.results:
            grouped[result.language].append({
                'filepath': result.filepath,
                'block_num': result.block_num,
                'valid': result.valid,
                'error': result.error,
                'warning': result.warning,
            })
        return dict(grouped)

    def _get_failures(self):
        """Get all failed validations"""
        return [
            {
                'language': r.language,
                'filepath': r.filepath,
                'block': r.block_num,
                'error': r.error,
            }
            for r in self.results if not r.valid and r.error
        ]

    def _get_warnings(self):
        """Get all warnings (tool not available)"""
        return [
            {
                'language': r.language,
                'filepath': r.filepath,
                'warning': r.warning,
            }
            for r in self.results if r.warning
        ]

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    engine = ValidationEngine()
    print("Starting validation suite...")
    engine.extract_and_validate('./data')
    report = engine.generate_report()
    print("Validation complete. Report saved to validation_report.json")
    print(f"Summary: {report['summary']}")
'''
        return script_content

if __name__ == '__main__':
    analyzer = CodeAnalyzer()
    analyzer.print_report()

    print("\n" + "="*80)
    print("PHASE 4: PROPOSED VALIDATION SCRIPT STRUCTURE")
    print("="*80 + "\n")

    print("""
The validation script should follow this modular architecture:

DIRECTORY STRUCTURE:
--------------------
validation/
├── validate_all.py                 # Main entry point
├── validators/
│   ├── __init__.py
│   ├── base.py                     # BaseSyntaxValidator abstract class
│   ├── python_validator.py         # Uses ast.parse()
│   ├── javascript_validator.py     # Uses node --check
│   ├── typescript_validator.py     # Uses tsc --noEmit
│   ├── go_validator.py             # Uses go build
│   ├── java_validator.py           # Uses javac
│   ├── sql_validator.py            # Uses sqlglot (multi-dialect)
│   ├── bash_validator.py           # Uses shellcheck + sh -n fallback
│   ├── html_validator.py           # Uses html5lib / W3C validator
│   ├── json_validator.py           # Uses json.tool
│   ├── yaml_validator.py           # Uses yamllint
│   └── dockerfile_validator.py     # Uses hadolint
├── extractors/
│   ├── markdown_extractor.py       # Extract code blocks from .md
│   └── code_block.py               # CodeBlock data class
├── reporters/
│   ├── json_reporter.py            # JSON output
│   ├── html_reporter.py            # HTML dashboard
│   ├── csv_reporter.py             # CSV for spreadsheet
│   └── summary_reporter.py         # Console summary
├── config/
│   ├── validators.yaml             # Validator configuration
│   ├── rules.yaml                  # Validation rules per language
│   └── ignore_patterns.txt         # Patterns to skip validation
└── requirements.txt                # Dependencies

KEY FEATURES:
-------------
1. Language-specific validators with graceful degradation
2. Configurable validation rules per language/domain
3. Batch processing with progress tracking
4. Multi-format reporting (JSON, HTML, CSV)
5. Failure summary with file:block references
6. Tool availability checks with helpful messages
7. Timeout protection (5-10s per block)
8. Error categorization (syntax vs. runtime vs. missing tools)

VALIDATION FLOW:
----------------
extract_code_blocks()
    ↓
validate_blocks()  [parallel where possible]
    ↓
generate_report()
    ↓
output_results()

HIGH-RISK DOMAINS REQUIRING PRIORITY:
--------------------------------------
""")

    print("\n1. SQL (Complex Multi-Dialect Validation)")
    print("   - Challenge: PostgreSQL/MySQL/Oracle/SQLite syntax differences")
    print("   - Priority: HIGH (financial/analytics domains)")
    print("   - Recommendation: Use sqlglot (parse + validate)")
    print("   - Examples: 08-databases/, cheat-sheets/")

    print("\n2. BASH (Environment-Dependent)")
    print("   - Challenge: Shell-specific syntax, globbing, variable expansion")
    print("   - Priority: HIGH (DevOps/SRE domains)")
    print("   - Recommendation: Use shellcheck + sh -n fallback")
    print("   - Examples: 06-devops/, 07-kubernetes/")

    print("\n3. JAVA (Complex Type System)")
    print("   - Challenge: Generics, version-specific features, lambda syntax")
    print("   - Priority: MEDIUM (backend domain)")
    print("   - Recommendation: Use javac with version flags")
    print("   - Examples: 03-backend/java/, 20-interviews/")

    print("\n4. GO (Package/Interface Validation)")
    print("   - Challenge: Package structure, interface satisfaction")
    print("   - Priority: MEDIUM (backend domain)")
    print("   - Recommendation: Use go build with sandbox")
    print("   - Examples: 03-backend/go/")

    print("\n5. JAVASCRIPT/TYPESCRIPT (Version & Async Issues)")
    print("   - Challenge: ES6+ features, async/await, type checking")
    print("   - Priority: MEDIUM (frontend/backend domain)")
    print("   - Recommendation: Use node --check + tsc for TS")
    print("   - Examples: 03-backend/typescript/, 04-frontend/react/")

    print("\n6. PYTHON (Indentation & Async)")
    print("   - Challenge: Indentation-sensitive, async/await, type hints optional")
    print("   - Priority: LOW (most portable)")
    print("   - Recommendation: Use ast.parse() + optional type checking")
    print("   - Examples: 03-backend/python/, 01-ai-ml/")
