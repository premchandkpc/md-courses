# Code Syntax Validation Implementation Guide

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Python: sqlglot for SQL validation
pip install sqlglot

# System: shellcheck for Bash validation
# macOS
brew install shellcheck

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install shellcheck

# Windows (via chocolatey)
choco install shellcheck

# Node.js and TypeScript (if not already installed)
npm install -g typescript
```

### 2. Run Baseline Validation

```bash
# Simple run - validates all languages
python3 validate_syntax.py

# Validate only SQL (highest risk)
python3 validate_syntax.py --lang sql

# Generate JSON report for analysis
python3 validate_syntax.py --json validation_results.json

# Quiet mode (no console output)
python3 validate_syntax.py --quiet --json results.json
```

### 3. Review Results

```bash
# Check summary
python3 validate_syntax.py | grep -A 15 "VALIDATION RESULTS"

# View failures (if any)
cat validation_results.json | jq '.failures | .[0:5]'
```

---

## Phase 1: Initial Setup (1-2 hours)

### Step 1: Place Script Files

Copy these files to your repository root:

```
md-courses/
├── validate_syntax.py            # Main validation engine
├── validation_config.yaml         # Configuration file
├── SYNTAX_VALIDATION_ANALYSIS.md  # This analysis
└── validate_all.sh               # Optional wrapper script
```

### Step 2: Create Wrapper Script (Optional but Recommended)

**File:** `validate_all.sh`

```bash
#!/bin/bash
# Comprehensive validation wrapper

set -e

echo "=========================================="
echo "Code Syntax Validation Suite"
echo "=========================================="
echo ""

# Install dependencies if missing
echo "Checking dependencies..."

if ! python3 -c "import sqlglot" 2>/dev/null; then
    echo "Installing sqlglot..."
    pip install -q sqlglot
fi

if ! command -v shellcheck &> /dev/null; then
    echo "Warning: shellcheck not found"
    echo "Install with: brew install shellcheck (macOS) or apt-get install shellcheck (Linux)"
fi

echo "Dependencies OK"
echo ""

# Run validation
echo "Starting validation..."
python3 validate_syntax.py --json validation_results.json

# Display summary
echo ""
echo "=========================================="
echo "Validation Complete"
echo "=========================================="
python3 validate_syntax.py | tail -20

echo ""
echo "Full report saved to: validation_results.json"
echo ""
```

Make it executable:

```bash
chmod +x validate_all.sh
./validate_all.sh
```

### Step 3: Test with Single Language

Start with Python (lowest risk, built-in validation):

```bash
python3 validate_syntax.py --lang python
```

Expected output:

```
Total Blocks Validated: ~8,500
Time Elapsed: 45.23s

VALIDATION RESULTS BY LANGUAGE
────────────────────────────────────────────────────────────────────────────────
Language        Total      Valid      Failed     Warning    Rate
────────────────────────────────────────────────────────────────────────────────
python          8500       8350       150        50         98.2%
────────────────────────────────────────────────────────────────────────────────
```

### Step 4: Add SQL Validation

SQL has highest risk, so validate second:

```bash
python3 validate_syntax.py --lang sql
```

This tests `sqlglot` installation and multi-dialect support.

---

## Phase 2: Expand to All Languages (2-3 hours)

### Step 1: Install Remaining Tools

```bash
# Java: Already standard (javac)
javac -version

# Go: Already standard (go)
go version

# Node.js: For JavaScript/TypeScript
node --version

# TypeScript (if not already installed)
npm install -g typescript
tsc --version
```

### Step 2: Run Full Validation

```bash
# All languages
python3 validate_syntax.py

# With JSON output for analysis
python3 validate_syntax.py --json full_results.json

# Check pass rates
python3 validate_syntax.py | grep "Rate"
```

### Step 3: Analyze Results by Domain

```python
import json

with open('full_results.json') as f:
    report = json.load(f)

# Failures by language
for lang, stats in report['summary'].items():
    if stats['failed'] > 0:
        print(f"\n{lang}: {stats['failed']} failures out of {stats['total']}")
        
# Sample failures
failures = report['failures'][:5]
for f in failures:
    print(f"\n{f['language']}: {f['filepath']}:{f['block_num']}")
    print(f"  Error: {f['error']}")
```

---

## Phase 3: Fix High-Priority Failures (1-2 days)

### High-Risk Domains (Address First)

#### 1. SQL Failures

SQL failures are often multi-dialect issues. Check:

```bash
# Extract SQL failures only
python3 << 'EOF'
import json
with open('full_results.json') as f:
    report = json.load(f)
    
sql_failures = [f for f in report['failures'] if f['language'] == 'sql']
print(f"Total SQL failures: {len(sql_failures)}")
for f in sql_failures[:5]:
    print(f"\n{f['filepath']}:{f['block_num']}")
    print(f"Error: {f['error'][:100]}")
EOF
```

**Common SQL Issues:**

1. **Dialect incompatibility**
   - Fix: Add SQL dialect hint in markdown
   ```markdown
   ```sql -- postgres
   SELECT ... LIMIT 10 OFFSET 5;
   ```
   ```

2. **Missing schema context**
   - Fix: Use fully qualified names or schema comments
   ```sql
   -- Schema: users(id INT, email VARCHAR)
   SELECT * FROM users WHERE email = 'test@example.com';
   ```

#### 2. Bash Failures

Check shellcheck output:

```bash
# Get bash failure details
python3 << 'EOF'
import json
with open('full_results.json') as f:
    report = json.load(f)
    
bash_failures = [f for f in report['failures'] if f['language'] == 'bash']
for f in bash_failures[:3]:
    print(f"{f['filepath']}:{f['block_num']}")
    print(f"Error: {f['error']}")
    print()
EOF
```

**Common Bash Issues:**

1. **Unquoted variables** (SC2086)
   ```bash
   # Bad
   echo $var
   
   # Good
   echo "$var"
   ```

2. **Unescaped glob patterns**
   ```bash
   # Bad
   rm *.log  # Fails if no .log files exist
   
   # Good
   shopt -s nullglob  # Allow empty glob
   rm *.log
   ```

3. **Using [[ instead of [**
   ```bash
   # Portable
   if [ -f "$file" ]; then
   
   # bash-specific
   if [[ -f "$file" ]]; then
   ```

#### 3. Java Failures

Java often fails on version-specific features:

```bash
python3 << 'EOF'
import json
with open('full_results.json') as f:
    report = json.load(f)
    
java_failures = [f for f in report['failures'] if f['language'] == 'java']
print(f"Java failures: {len(java_failures)}")
for f in java_failures[:3]:
    print(f"\n{f['filepath']}:{f['block_num']}")
    print(f"Error: {f['error'][:150]}")
EOF
```

**Common Java Issues:**

1. **Version-specific syntax**
   ```java
   // Java 8+ (lambdas)
   list.stream().filter(x -> x > 5)
   
   // Java 14+ (records)
   record Point(int x, int y) {}
   
   // Java 17+ (sealed classes)
   sealed class Shape permits Circle, Square {}
   ```

   Fix: Add version comment or update to Java 17
   ```java
   // Java 17+ required
   record Point(int x, int y) {}
   ```

2. **Incomplete class definition**
   ```java
   // Incomplete - needs class wrapper
   void process(List<String> items) {
       items.forEach(System.out::println);
   }
   ```

### Step-by-Step Fix Process

1. **Identify top failure category**
   ```bash
   python3 validate_syntax.py --json results.json
   python3 << 'EOF'
   import json
   from collections import Counter
   with open('results.json') as f:
       report = json.load(f)
   errors = [f['error'].split(':')[0] for f in report['failures']]
   for error, count in Counter(errors).most_common(5):
       print(f"{count:3d} {error}")
   EOF
   ```

2. **Fix by domain**
   - Edit `/data/03-backend/java/...` for Java issues
   - Edit `/data/08-databases/...` for SQL issues
   - Edit `/data/06-devops/...` for Bash issues

3. **Validate fix**
   ```bash
   python3 validate_syntax.py --lang java --json results.json
   ```

4. **Commit fix**
   ```bash
   git add data/
   git commit -m "Fix Java syntax: [description of fix]"
   ```

---

## Phase 4: CI/CD Integration (1-2 hours)

### Option A: GitHub Actions (Recommended)

**File:** `.github/workflows/validate-code.yml`

```yaml
name: Code Validation

on:
  push:
    branches: [main, develop]
    paths: ['data/**/*.md']
  pull_request:
    branches: [main]
    paths: ['data/**/*.md']

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install sqlglot
          sudo apt-get update
          sudo apt-get install -y shellcheck
      
      - name: Run validation
        run: python3 validate_syntax.py --json validation_results.json
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: validation-results
          path: validation_results.json
      
      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('validation_results.json', 'utf8'));
            const failures = results.failures.slice(0, 10);
            
            let comment = '### Code Validation Results\n\n';
            comment += `Failed: ${failures.length} blocks\n\n`;
            comment += '```\n';
            for (const f of failures) {
              comment += `${f.language}: ${f.filepath}:${f.block_num}\n`;
              comment += `  ${f.error.substring(0, 100)}\n`;
            }
            comment += '```\n';
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

### Option B: Pre-commit Hook

**File:** `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Run validation on changed .md files before commit

set -e

echo "Running code validation..."

# Check if any .md files changed
if ! git diff --cached --name-only | grep -q "\.md$"; then
    exit 0
fi

# Run validation
if ! python3 validate_syntax.py --quiet; then
    echo "Validation failed. Fix errors and try again."
    echo "Run: python3 validate_syntax.py --lang <language>"
    exit 1
fi

echo "Validation passed!"
```

Install:
```bash
cp .pre-commit-hook .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Option C: Local Validation

Run before pushing:

```bash
# Validate before push
./validate_all.sh

# If failures, fix and re-run
python3 validate_syntax.py --lang sql  # Fix SQL
python3 validate_syntax.py --lang bash # Fix Bash
```

---

## Phase 5: Monitoring & Maintenance (Ongoing)

### Weekly Checks

```bash
# Run validation
python3 validate_syntax.py --json weekly_report.json

# Extract stats
python3 << 'EOF'
import json
with open('weekly_report.json') as f:
    report = json.load(f)
    
print("Weekly Validation Summary:")
print("=" * 50)
for lang, stats in sorted(report['summary'].items()):
    total = stats['total']
    valid = stats['valid']
    rate = f"{(valid/total*100):.1f}%" if total else "0%"
    print(f"{lang:12} {valid:5}/{total:5} ({rate})")
EOF
```

### Fix Patterns

Create a monthly fix schedule:

1. **Monday:** Review and triage failures
2. **Tuesday-Thursday:** Fix high-impact failures
3. **Friday:** Verify all fixes, commit

### Tracking Issues

Create GitHub Issues for high-impact failures:

```bash
# Generate issue template for top failures
python3 << 'EOF'
import json
with open('validation_results.json') as f:
    report = json.load(f)

failures = sorted(
    report['failures'],
    key=lambda x: x.get('block_num', 0)
)[:5]

for f in failures:
    print(f"""
### Fix validation error: {f['language']} in {f['filepath']}

**File:** {f['filepath']}  
**Block:** {f['block_num']}  
**Error:** {f['error']}

**Steps to fix:**
1. Open the file and find the code block
2. Verify syntax with: python3 validate_syntax.py --lang {f['language']}
3. Fix the error
4. Commit and push

**Priority:** Medium
""")
EOF
```

---

## Troubleshooting

### Issue: "sqlglot not found"

```bash
pip install sqlglot
python3 -c "import sqlglot; print(sqlglot.__version__)"
```

### Issue: "shellcheck not found"

```bash
# macOS
brew install shellcheck

# Linux
sudo apt-get install shellcheck

# Verify
shellcheck --version
```

### Issue: "No code blocks found"

Check that markdown files have proper code fence format:

```markdown
# Good
```python
code here
```

# Bad
```
code here (no language specified)
```

# Bad
    code here (indented code, not fenced)
```

### Issue: "Validation timeout"

Some code blocks take too long. Options:

1. Increase timeout in `validation_config.yaml`
2. Simplify the code block
3. Add comment to skip: `<!-- skip-validation -->`

### Issue: "Tool not available"

See Installation section above for each tool.

---

## Performance Tips

### Run Validation in Parallel

The script uses single-threaded validation by default. For large batches:

```bash
# Split by language (parallel runs)
python3 validate_syntax.py --lang python &
python3 validate_syntax.py --lang sql &
python3 validate_syntax.py --lang bash &
wait

# Merge results (future enhancement)
```

### Validate Only Changed Files

```bash
# Git hook to validate only changed .md files
git diff --name-only HEAD | grep "\.md$" | \
    xargs python3 validate_syntax.py --files
```

---

## Summary Checklist

- [ ] Install `sqlglot`, `shellcheck`, `typescript` (tsc)
- [ ] Run `python3 validate_syntax.py` to get baseline
- [ ] Review failures by language (SQL, Bash, Java first)
- [ ] Fix high-impact failures (~50 blocks)
- [ ] Set up GitHub Actions workflow
- [ ] Run validation on every PR
- [ ] Monitor weekly and fix new failures
- [ ] Document special cases (SQL dialects, Java versions)

---

## Next Steps

1. **Today:** Install tools and run baseline validation
2. **This week:** Fix top 20 failures
3. **This month:** Achieve >90% pass rate
4. **Ongoing:** Monitor and maintain

---

## Support

For issues with:
- **Python validation:** See `validate_syntax.py` PythonValidator
- **SQL validation:** Check `sqlglot` docs: https://sqlglot.com
- **Bash validation:** Check `shellcheck` docs: https://shellcheck.net
- **Java validation:** Java compiler documentation
- **Go/JS/TS:** Built-in tools documentation

Questions? Create an issue or review the analysis document:
`SYNTAX_VALIDATION_ANALYSIS.md`
