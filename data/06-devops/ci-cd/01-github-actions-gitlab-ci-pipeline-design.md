# GitHub Actions & GitLab CI Pipeline Design


```mermaid
graph LR
    CODE["Code Push<br/>(git push)"] --> BUILD["Build Stage<br/>(compile/lint)"]
    BUILD --> TEST["Test Stage<br/>(unit/integration)"]
    TEST --> PACKAGE["Package Stage<br/>(Docker image)"]
    PACKAGE --> REG["Container Registry<br/>(ECR/Docker Hub)"]
    REG --> STAGE["Deploy to<br/>Staging"]
    STAGE --> SMOKE["Smoke Tests<br/>(Canary)"]
    SMOKE --> PROD["Deploy to<br/>Production"]
    PROD --> VERIFY["Post-Deploy<br/>Verification"]
    CI["GitHub Actions /<br/>GitLab CI YAML"] --> JOB["Job<br/>(Runs on Runner)"]
    JOB --> STEP["Step<br/>(Shell/Action)"]
    STEP --> CACHE["Cache /<br/>Artifacts"]
    style CODE fill:#4a8bc2
    style BUILD fill:#2d5a7b
    style TEST fill:#3a7ca5
    style PACKAGE fill:#6f42c1
    style REG fill:#c73e1d
    style STAGE fill:#e8912e
    style SMOKE fill:#3fb950
    style PROD fill:#c73e1d
    style VERIFY fill:#3fb950
    style CI fill:#3a7ca5
    style JOB fill:#e8912e
    style STEP fill:#2d5a7b
    style CACHE fill:#3fb950
```

## Table of Contents


1. NOOB Explanation
2. Internal Architecture
3. End-to-End Execution Flows
4. Large-Scale CI/CD Systems
5. Failure Analysis & Root Causes
6. Edge Cases & Race Conditions
7. Interview Questions for FAANG
8. Performance Optimization
9. Security Deep Dive
10. Code Examples
11. Production Incidents
12. Comparison Tables

---

## Section 1: NOOB Explanation - CI/CD Pipeline Fundamentals


### The Assembly Line Analogy


Imagine a car factory:
- **Raw materials arrive** (code commit)
- **Robot workers** (GitHub Actions runners) pick them up
- **Assembly station 1** (build step) shapes the material
- **Quality control station** (tests) checks everything
- **Packaging station** (artifact creation) prepares the final product
- **Shipping station** (deployment) sends to customers

Each station is independent but connected. If any station fails, the entire line stops.

### GitHub Actions: The Robot Workers


GitHub Actions runners are:
- **Stateless machines** that spin up, execute jobs, then vanish
- **Event-triggered** (push, PR, schedule, webhook)
- **Declarative** (YAML defines exactly what they do)
- **Parallel-capable** (multiple jobs run simultaneously)

A **workflow** is a collection of **jobs**, each running on its own runner.
Each **job** contains **steps** that execute sequentially.

### GitLab CI: The Self-Hosted Alternative


GitLab CI uses:
- **Runners** (can be self-hosted or SaaS)
- **Pipelines** (equivalent to workflows)
- **Stages** (sequential groups of jobs)
- **Artifacts** (files passed between jobs)

Key difference: GitLab stages run sequentially by default; GitHub jobs run in parallel unless configured otherwise.

---

## Section 2: Internal Architecture


### GitHub Actions Execution Model


```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Event (push/PR/etc)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           Webhook Event Dispatcher (GitHub Cloud)               │
│  - Evaluates workflow YAML for matching trigger conditions      │
│  - Checks branch protections & required reviews                 │
│  - Validates syntax & referenced actions                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Queue Management Service                           │
│  - Assigns queue position based on runner availability          │
│  - Considers job dependencies & concurrency rules               │
│  - Applies resource constraints & quotas                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
        ┌────────────────┐      ┌────────────────┐
        │ GitHub Runner  │      │ Self-Hosted    │
        │ (ubuntu-latest)│      │ Runner         │
        └────────┬───────┘      └────────┬───────┘
                 │                       │
                 ▼                       ▼
        ┌──────────────────────────────────────┐
        │  Runner Agent Startup                │
        │  - Clone repository to working dir   │
        │  - Load secrets from vault           │
        │  - Setup environment variables       │
        │  - Execute pre-job setup scripts     │
        └────────────┬─────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────────┐
        │  Execute Job Steps Sequentially      │
        │  ┌──────────────────────────────────┐│
        │  │ Step 1: run: npm install         ││
        │  └──────────────────────────────────┘│
        │  ┌──────────────────────────────────┐│
        │  │ Step 2: run: npm test            ││
        │  └──────────────────────────────────┘│
        │  ┌──────────────────────────────────┐│
        │  │ Step 3: upload-artifact          ││
        │  └──────────────────────────────────┘│
        └────────────┬─────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────────┐
        │  Artifact Storage (GitHub or S3)     │
        │  - Compress & deduplicate           │
        │  - Store with retention policy      │
        │  - Index for download               │
        └────────────┬─────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────────┐
        │  Job Status & Logs Upload            │
        │  - Stream logs to GitHub/GitLab      │
        │  - Set final status (success/fail)   │
        │  - Trigger dependent jobs            │
        └──────────────────────────────────────┘
```

### Secrets Management Deep Dive


GitHub Actions secrets storage:
```
┌─────────────────────────────────────┐
│  Secret Entered via UI/API          │
│  (e.g., AWS_ACCESS_KEY)             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Encryption (AES-GCM-256)           │
│  - Server-side encryption at rest   │
│  - Keys managed by GitHub           │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Vault Storage                      │
│  - Encrypted database backup        │
│  - Access logged for audit          │
│  - Replicated across regions        │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌─────────────────────────────────────┐
│  Requested by Job                   │
│  - Job token created with limited   │
│    scope & TTL                      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Decryption via Runner              │
│  - Decrypted in-memory on runner    │
│  - Never written to disk            │
│  - Redacted from logs               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Environment Variable Injection     │
│  ${{ secrets.AWS_ACCESS_KEY }}      │
│  - Only accessible to job steps     │
│  - Auto-masked in output            │
└─────────────────────────────────────┘
```

### YAML Parsing & Validation


GitHub Actions YAML parsing:

```yaml
name: Build & Deploy
on:
  push:
    branches: [main]
    paths-ignore:
      - 'docs/**'
  pull_request:
  schedule:
    - cron: '0 2 * * *'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: myapp

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
      - uses: docker/build-push-action@v4
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "Deploying image tag: ${{ needs.build.outputs.image-tag }}"
```

Parsing flow:
1. **Lexer** tokenizes YAML into structured tokens
2. **Parser** builds AST (Abstract Syntax Tree)
3. **Validator** checks:
   - All required fields present
   - Types correct (string, number, array, object)
   - No circular dependencies in job graph
   - Valid expressions (`${{ ... }}`)
   - Secret names exist
   - Action versions are valid
4. **Evaluator** processes conditionals & context variables
5. **Scheduler** builds execution DAG (Directed Acyclic Graph)

### Runner Architecture (Self-Hosted)


```
Self-Hosted Runner Process:
┌────────────────────────────────────────┐
│  Runner Service (systemd/launchd)      │
│  - Daemonizes on system startup        │
│  - Registers with GitHub API           │
│  - Polls for available jobs             │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  Authentication                        │
│  - PAT (Personal Access Token) or      │
│  - Repository token with limited scope │
│  - OIDC federation (enterprise)        │
└────────────┬─────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  Job Polling Loop                      │
│  - Poll every 30 seconds (default)     │
│  - Exponential backoff on no jobs      │
│  - Max 3 concurrent jobs (configurable)│
└────────────┬─────────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Job Found    │  │ No Jobs      │
└──────┬───────┘  │ Sleep        │
       │          └──────────────┘
       ▼
┌────────────────────────────────────────┐
│  Download Job Definition               │
│  - YAML config with all steps          │
│  - Action references with versions     │
│  - Secret names (not values)           │
│  - Environment variables               │
└────────────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Create Working Directory              │
│  - /home/runner/work/<owner>/<repo>    │
│  - Isolate previous runs                │
│  - Set ownership & permissions          │
└────────────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Clone Repository (shallow)            │
│  - git clone --depth=1 <url>           │
│  - Checkout specific ref (commit/tag)  │
│  - Submodules if configured            │
└────────────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Load Secrets & Env Vars               │
│  - Fetch from GitHub vault             │
│  - Inject as environment variables     │
│  - Set context variables               │
└────────────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Execute Job Steps                     │
│  - Sequential execution                │
│  - Stream stdout/stderr to GitHub      │
│  - Capture exit codes & outputs        │
└────────────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Upload Artifacts & Logs               │
│  - Compress & deduplicate              │
│  - S3/blob storage upload              │
│  - Index for retrieval                 │
└────────────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  Cleanup                               │
│  - Delete working directory            │
│  - Clear secrets from memory           │
│  - Update job status                   │
└────────────────────────────────────────┘
```

---

## Section 3: End-to-End Execution Flows


### Commit → Test → Deploy Flow


```
Developer commits code to main branch
    │
    ▼
GitHub receives push event
    │
    ▼
Webhook dispatcher finds matching workflows
    │
    ├─ "build.yml" (on: [push, pull_request])  ✓ Triggered
    ├─ "release.yml" (on: [release])            ✗ Not triggered
    └─ "nightly.yml" (schedule: cron)           ✗ Not triggered
    │
    ▼
Parse & validate workflow YAML
    │
    ├─ Check syntax
    ├─ Resolve actions (actions/checkout@v4)
    ├─ Evaluate environment variables
    ├─ Build job dependency DAG
    │
    ▼
Queue jobs based on concurrency:
    │
    build (priority 0): queued
    test (needs: build): waiting
    deploy (needs: test, if: main): waiting
    │
    ▼
Assign build job to available runner
    │
    ▼
Runner Agent:
    1. Clone repo with depth=1
    2. Checkout specific commit SHA
    3. Load secrets from vault
    4. Execute step 1: actions/setup-node@v3
    5. Execute step 2: run: npm install
    6. Execute step 3: run: npm run build
    7. Execute step 4: actions/upload-artifact@v3 (dist/)
    │
    ▼
Build completes (exit code 0)
    │
    Unblock test job
    │
    ▼
Runner Agent:
    1. Restore dist/ from artifact storage
    2. Install dependencies (with cache hit)
    3. Execute: npm test -- --coverage
    4. Upload coverage reports
    5. Exit code 0
    │
    ▼
Test completes, evaluate deploy condition:
    │
    if: github.ref == 'refs/heads/main' ✓
    if: github.event_name == 'push'     ✓
    │
    ▼
Deploy job runs:
    1. Assume AWS IAM role via OIDC token
    2. Run: aws s3 cp dist/ s3://bucket/
    3. Invalidate CloudFront cache
    4. Post deployment status to GitHub
    │
    ▼
All jobs complete
    │
    ├─ Mark commit as "passing"
    ├─ Merge PR if auto-merge enabled
    ├─ Delete artifact after retention (30 days)
    ├─ Archive logs to long-term storage
    │
    ▼
Webhook notification to Slack/Teams
```

### Pull Request Workflow with Status Checks


```
Developer pushes feature branch & creates PR
    │
    ▼
GitHub triggers workflows (on: [pull_request])
    │
    ┌─────────────────────────────────────────┐
    │  Parallel Job Execution                 │
    │  ┌──────────┐  ┌──────────┐  ┌────────┐│
    │  │  Build   │  │  Lint    │  │  Type  ││
    │  │  Stage   │  │  Stage   │  │ Check  ││
    │  └────┬─────┘  └────┬─────┘  └───┬────┘│
    │       │             │            │     │
    │       └─────────────┴────────────┘     │
    │                    │                   │
    └────────────────────┼───────────────────┘
                         │
                         ▼
    Test Stage (needs: build, lint, type-check)
    │
    ├─ Unit tests
    ├─ Integration tests
    ├─ E2E tests
    │
    ▼
Post to Commit
    │
    ├─ build [PASSED]
    ├─ lint [PASSED]
    ├─ type-check [PASSED]
    ├─ test [PASSED]
    │
    ├─ Code coverage: 87% (requires: ≥85%)
    ├─ All checks passed
    │
    ▼
Branch is now mergeable (all status checks green)
    │
    Author can click "Merge" or use auto-merge
    │
    ▼
After merge:
    1. Delete feature branch (if configured)
    2. Trigger release workflow (if tags detected)
    3. Archive PR artifacts (90 days)
```

---

## Section 4: Large-Scale CI/CD Systems


### Multi-Region Runner Distribution


For a company with 1000+ repositories and 5000+ developers:

```
┌──────────────────────────────────────────────────────────────┐
│                    GitHub Organization                       │
│                    (enterprise.github.com)                    │
└──────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ US-EAST      │ │ EU-WEST      │ │ APAC         │
    │ Runner Pool  │ │ Runner Pool  │ │ Runner Pool  │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           │                │                │
    ┌──────┴─────────┬──────┴──────┬────────┴───────┐
    │                │             │                │
┌───▼──────┐ ┌──────▼────┐ ┌──────▼────┐ ┌────────▼───┐
│ CPU Pool │ │ GPU Pool  │ │ 4GB RAM   │ │ 16GB RAM   │
│ (400 VMs)│ │ (100 VMs) │ │ (200 VMs) │ │ (50 VMs)   │
└──────────┘ └───────────┘ └───────────┘ └────────────┘
```

Runner scaling strategy:
- **Static baseline** (24/7): 150 runners in US-EAST (handle off-peak)
- **Auto-scaling** (AWS): Scale to 400 during 9-5 business hours
- **Geo-routing**: Route jobs to nearest region (minimize latency)
- **Pool management**: Separate pools for build, test, deploy jobs

### High-Frequency Deployment System


```
Commit frequency: 50+ per hour across all repos

Load balancer logic:
┌─────────────┐ ┌──────────────────┐
│ Commit Rate │ │ Available Runners │ Queue Time
├─────────────┼──────────────────┤─────────────
│ < 10/hr     │ > 100 runners     │ < 30 sec
│ 10-30/hr    │ 100-200 runners   │ 30-60 sec
│ 30-50/hr    │ 200-400 runners   │ 60-120 sec
│ > 50/hr     │ > 400 runners     │ ? (scale)
└─────────────┴──────────────────┴─────────────

Concurrency policy:
- Default: 5 concurrent per repo (prevent resource starvation)
- Enterprise tier: 20 concurrent (high-activity repos)
- Requires approval: 50+ concurrent (risk of cascade failures)

Job prioritization queue:
┌─────────────────────────────────────┐
│ Priority Queues (FIFO within level) │
├─────────────────────────────────────┤
│ P0: Production hotfix deploys       │
│ P1: Main branch builds              │
│ P2: PR builds & validation          │
│ P3: Scheduled jobs (nightly tests)  │
│ P4: Development builds              │
└─────────────────────────────────────┘
```

---

## Section 5: Failure Analysis & Root Causes


### Cache Poisoning Incident


**Symptom**: Tests passing locally but failing in CI

**Root Cause**:
```
1. Developer installs package A@1.0 locally
2. Pushes code with npm install
3. GitHub runner uses cache (from previous build)
   - Cache includes A@1.2 (newer patch)
4. Tests written for A@1.0 but run against A@1.2
5. A@1.2 has breaking change → tests fail
```

**Prevention**:
```yaml
- uses: actions/setup-node@v3
  with:
    node-version: '18'
    cache: npm
    cache-dependency-path: 'package-lock.json'

# Validate lock file integrity
- run: npm ci --audit
```

**Recovery**:
```bash
# Clear cache for this job
- uses: actions/github-script@v6
  with:
    script: |
      const caches = await github.rest.actions.getActionsCacheList();
      for (const cache of caches.data.actions_caches) {
        github.rest.actions.deleteActionsCacheById({
          owner: context.repo.owner,
          repo: context.repo.repo,
          cache_id: cache.id,
        });
      }
```

### Build Timeout Race Condition


**Symptom**: Job randomly times out after 360 minutes (6 hours)

**Root Cause**:
```
1. Job creates 100 test threads
2. Test data cached in /tmp
3. /tmp fills up (no quota enforcement)
4. Threads block on disk I/O
5. Job hangs waiting for I/O
6. After 360 min hard timeout → job killed
```

**Prevention**:
```yaml
- name: Run tests with timeout
  run: timeout 300 npm test  # Explicit 5 min timeout
  
- name: Monitor disk usage
  run: |
    USAGE=$(df /tmp | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $USAGE -gt 90 ]; then
      echo "ERROR: /tmp is ${USAGE}% full"
      exit 1
    fi
```

### Artifact Loss During Cleanup


**Symptom**: Artifact exists immediately after upload but gone when trying to download

**Root Cause**:
```
1. Job uploads 2GB artifact
2. Default retention: 30 days
3. But job completes at day 31
4. Cleanup job runs before artifact indexing completes
5. Artifact removed before it's fully committed to storage
```

**Timeline**:
- 10:00: Job completes, requests artifact upload
- 10:01: Storage service begins upload (2GB takes 5 min)
- 10:02: Cleanup job runs, sees artifact not in index, deletes it
- 10:05: Upload completes, but artifact already deleted
- 10:06: PR tries to download → 404

**Prevention**:
```yaml
- uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: coverage/
    retention-days: 90
    
  # Add explicit wait
- run: |
    sleep 10  # Allow artifact indexing
```

### Secret Rotation Failure


**Symptom**: Some jobs have new secret, others still have old secret

**Root Cause**:
```
1. Admin rotates AWS_ACCESS_KEY in GitHub UI
2. GitHub begins propagating to all runners
3. Job A: Gets new key (succeeds)
4. Job B: Gets old key (fails with 403)
5. Job C: Still waiting (race condition)
```

**Prevention**:
```yaml
- name: Verify credentials
  run: |
    aws sts get-caller-identity > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "ERROR: AWS credentials invalid, aborting"
      exit 1
    fi
```

### Concurrent Deploy Race Condition


**Symptom**: Two deploys to production simultaneously, causing data corruption

**Root Cause**:
```
1. User merges PR to main
2. Deploy workflow starts (10 min duration)
3. 5 minutes in, user reverts PR
4. New deploy workflow starts
5. At 10 min mark: Deploy 1 completes, updates database schema
6. At 10 min mark: Deploy 2 completes, updates same schema with old code
7. Data corruption: conflicting schema versions
```

**Prevention**:
```yaml
deploy:
  runs-on: ubuntu-latest
  environment: production
  concurrency:
    group: production-deploy
    cancel-in-progress: false  # Queue instead of cancel
  steps:
    - uses: actions/checkout@v4
    - run: |
        # Wait for any in-progress deploy
        aws lambda invoke --function-name check-deploy-lock \
          --payload '{}' response.json
        if grep -q "locked" response.json; then
          echo "Deploy already in progress, waiting..."
          sleep 30
        fi
```

---

## Section 6: Edge Cases & Race Conditions


### Circular Dependencies in Jobs


**Problem**:
```yaml
jobs:
  job-a:
    needs: job-b
  job-b:
    needs: job-a  # CIRCULAR!
```

**GitHub's Response**: Detects and rejects at workflow validation time
```
Error: The workflow is not valid. 
.github/workflows/build.yml (Line 10): 
The jobs dependency graph is cyclic: job-a -> job-b -> job-a
```

### Conditional Expression Short Circuiting


```yaml
jobs:
  deploy:
    if: |
      github.ref == 'refs/heads/main' &&
      github.event_name == 'push' &&
      contains(github.event.head_commit.message, '[deploy]')
    runs-on: ubuntu-latest
```

**Edge Case**: What if `github.event.head_commit` is null?
- **Before**: Short circuit evaluation would prevent NPE
- **Now**: GitHub evaluates left-to-right but won't throw on missing object

**Solution**: Use safe navigation
```yaml
if: |
  github.ref == 'refs/heads/main' &&
  (github.event.head_commit == null || 
   !contains(github.event.head_commit.message, '[skip-ci]'))
```

### Matrix Job Combination Explosion


```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]  # 3
    node-version: [16, 18, 20]                         # 3
    dependency-version: [lowest, current, highest]     # 3
    # Total combinations: 3 × 3 × 3 = 27 jobs!
```

At 27 jobs × 5 minutes each = 135 minutes total runtime!

**Solution**: Use exclude/include
```yaml
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        node-version: 18  # Primary combination
      - os: windows-latest
        node-version: 20  # Secondary
      - os: macos-latest
        node-version: 18
  exclude:
    - os: macos-latest
      node-version: 16   # Don't test this combo
```

### Artifact Storage Exhaustion


**Scenario**:
- Workflow generates 500MB artifact per run
- Runs 100 times per day
- Retention: 30 days
- Total storage: 500MB × 100 × 30 = 1.5TB
- GitHub Actions artifact storage (free tier): 5GB
- **Result**: All old artifacts deleted, only latest can be accessed

**Prevention**:
```yaml
- uses: actions/upload-artifact@v3
  with:
    name: build-${{ github.run_number }}
    path: dist/
    retention-days: 7  # Keep only 7 days
    if-no-files-found: error

- name: Cleanup old artifacts
  run: |
    # Keep only 10 most recent
    ARTIFACTS=$(gh run list --limit 100 --json databaseId)
    echo "$ARTIFACTS" | jq -r '.[10:][].databaseId' | while read id; do
      gh run delete $id --repo ${{ github.repository }}
    done
```

### Self-Hosted Runner Disk Full


**Scenario**:
- Self-hosted runner on small VM (20GB disk)
- Job clones large repository (15GB)
- Disk fills up during git clone
- Runner enters zombie state

**Prevention**:
```bash
#!/bin/bash
# Runner startup script
AVAILABLE_SPACE=$(($(stat -f%a /tmp) * $(stat -f%f /tmp) / 1024 / 1024))
if [ $AVAILABLE_SPACE -lt 30000 ]; then  # < 30GB
  echo "ERROR: Not enough disk space"
  exit 1
fi

# Monitor during run
while true; do
  USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
  if [ $USAGE -gt 95 ]; then
    pkill -TERM -P $$  # Kill job
    echo "ERROR: Disk full during execution"
    exit 1
  fi
  sleep 30
done &
MONITOR_PID=$!
```

---

## Section 7: Interview Questions for FAANG


### Q1: Design a CI/CD system for 10,000 repositories


**Expected Answer Structure**:

1. **Architecture**:
   - Distributed runners across 3 regions (US, EU, APAC)
   - Auto-scaling groups (Kubernetes or cloud VMs)
   - Separate pools for build/test/deploy

2. **Scalability**:
   ```
   10,000 repos × 50 commits/day = 500,000 jobs/day
   Assuming 5 min average job: 500,000 × 5 = 2.5M minutes/day
   = 41,666 hours/day CPU usage
   = ~1,700 concurrent runners needed
   
   Strategy:
   - 400 baseline runners (always on)
   - 1,300 auto-scaling runners (peak hours)
   - 800 on-demand capacity (burst)
   ```

3. **Queue Management**:
   ```yaml
   priority_queue:
     - Production hotfixes (P0): < 1 min wait
     - Release builds (P1): < 5 min wait
     - Main branch (P2): < 15 min wait
     - PR validation (P3): < 30 min wait
     - Nightly tests (P4): no limit
   ```

4. **Artifact Storage**:
   - S3 with intelligent tiering
   - 90-day retention for build artifacts
   - 365-day retention for release artifacts
   - Deduplication via content-addressable storage (CAS)
   - Cost: ~$5K/month for 1PB storage

5. **Monitoring & Alerting**:
   - Queue wait time SLO: p95 < 30 seconds
   - Runner utilization: target 70-80%
   - Failure rate: < 2% across all jobs
   - Cost tracking per team/project

### Q2: You have a job that occasionally hangs indefinitely


**Root Cause Analysis**:
```
Given:
- Job runs every commit to main
- 99% success rate
- When it hangs: consumes 100% CPU, full memory
- Timeout after 6 hours is only way to stop it
- Logs show no errors before hang

Questions to ask:
1. Is it a test that creates threads without cleanup?
2. Is it reading from a network socket without timeout?
3. Is it lock contention (mutex deadlock)?
4. Is it OOM killer (looks like hang)?

Investigation:
- Run job in container with strace
- Monitor system calls right before hang
- Look for read() calls that never return
- Check if DNS resolution hangs

Common causes:
- Test framework spawning infinite threads
- Network call without timeout (AWS API, Docker daemon)
- Database connection not closing
- File handle exhaustion
```

**Solution**:
```yaml
- name: Run tests with explicit timeout
  run: timeout 600 npm test  # Hard 10 min limit
  
- name: Detect hung processes
  if: failure()
  run: |
    ps auxf
    netstat -an | grep ESTABLISHED | wc -l
    lsof | wc -l
```

### Q3: Artifact uploaded successfully but can't download


**Diagnosis Tree**:
```
Uploaded successfully?
├─ Yes → Upload artifacts API returned 200
│  └─ Can download immediately?
│     ├─ Yes → Intermittent (network issue?)
│     └─ No → Storage indexing lag
│           └─ Wait 5 minutes, retry
│              ├─ Success → Not a real bug
│              └─ Fail → Artifact corruption

Artifact size?
├─ < 1GB → Should download fine
├─ 1-5GB → Check S3 multipart timeout
└─ > 5GB → Need to stream, not load in memory
```

**Root causes**:
1. Storage service slow to index (< 5 min lag)
2. Network timeout during large artifact download
3. Runner disk full (can't download to scratch)
4. Artifact corruption during upload
5. Retention policy deleted it

**Prevention code**:
```yaml
- uses: actions/upload-artifact@v3
  id: upload
  with:
    name: test-results
    path: dist/
    retention-days: 90

- name: Verify artifact
  run: |
    # Wait for indexing
    for i in {1..10}; do
      if gh run download ${{ github.run_id }} \
         -n test-results -D /tmp/verify; then
        echo "✓ Artifact verified"
        exit 0
      fi
      sleep 10
    done
    echo "✗ Artifact not found"
    exit 1
```

### Q4: Design concurrent deployment safety


**Requirement**: Multiple developers can merge PRs to main simultaneously. Prevent deploy race conditions.

**Solution**:
```yaml
deploy:
  environment: production
  concurrency:
    group: production-deploy
    cancel-in-progress: false  # Important!
  steps:
    - uses: actions/checkout@v4
    
    - name: Check database lock
      run: |
        # Distributed lock via DynamoDB
        aws dynamodb put-item \
          --table-name deploy-locks \
          --item '{
            "environment": {"S": "production"},
            "run_id": {"S": "${{ github.run_id }}"},
            "timestamp": {"N": "'$(date +%s)'"},
            "ttl": {"N": "'$(($(date +%s) + 3600))'"}
          }' \
          --condition-expression 'attribute_not_exists(environment)'
    
    - name: Run migrations
      run: ./deploy.sh migrate
    
    - name: Deploy
      run: ./deploy.sh deploy
    
    - name: Release lock
      if: always()
      run: |
        aws dynamodb delete-item \
          --table-name deploy-locks \
          --key '{"environment": {"S": "production"}}'
```

### Q5: Explain how matrix jobs interact with concurrency limits


**Complex scenario**:
```yaml
strategy:
  matrix:
    os: [ubuntu, windows]
    version: [18, 20]
concurrency:
  group: test-${{ matrix.os }}
```

**Creates 4 jobs**:
- ubuntu-18 (concurrency group: test-ubuntu)
- ubuntu-20 (concurrency group: test-ubuntu)
- windows-18 (concurrency group: test-windows)
- windows-20 (concurrency group: test-windows)

**Behavior**:
```
Time  ubuntu-18  ubuntu-20  windows-18  windows-20
0     running    queued     running     queued
5     running    queued     running     queued
10    done       running    done        running
15    done       running    done        running
20    done       done       done        done

Key insight: cancel-in-progress only cancels within same group!
```

---

## Section 8: Performance Optimization


### Build Cache Strategy


**Problem**: Node modules installation takes 3 minutes every run

**Solution 1: GitHub Actions Cache**
```yaml
- uses: actions/setup-node@v3
  with:
    node-version: '18'
    cache: npm

# Caches ~/.npm or node_modules based on lock file
# Hit rate: ~95% if package.json unchanged
```

**Performance**:
- Cache miss: 3 minutes (full install)
- Cache hit: 30 seconds (restore + npm ci)
- Total savings: ~70% for typical PR

**Solution 2: Docker Layer Caching**
```dockerfile
FROM node:18
WORKDIR /app

# Layer 1: dependencies (cached until package.json changes)
COPY package*.json ./
RUN npm ci

# Layer 2: source code
COPY . .
RUN npm run build
```

In GitHub Actions:
```yaml
- uses: docker/build-push-action@v4
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Performance**:
- First build: 8 minutes
- Subsequent builds (unchanged deps): 1 minute (node_modules from cache)
- Subsequent builds (changed source only): 2 minutes

### Parallelization Strategy


```yaml
jobs:
  # Instead of sequential stages:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm install
      - run: npm run build
      
  test-unit:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: npm test -- --testPathPattern=unit
  
  test-integration:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: npm test -- --testPathPattern=integration
  
  lint:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: npm run lint
  
  type-check:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: npm run type-check

# Sequential timeline (total 15 min):
# build: 0-3 min
# ├── test-unit: 3-8 min
# ├── test-integration: 3-10 min
# ├── lint: 3-5 min
# └── type-check: 3-8 min
# Total: 10 min (not 15 min if sequential)
```

### Runner Efficiency


```
Problem: 400 runners, but average utilization only 40%
Result: $200K/month wasted

Solution: Implement priority queues with job coalescing

Priority scheduling:
┌─────────────────────────────────────┐
│ P0: Production hotfixes             │
│ Always gets available runner        │
├─────────────────────────────────────┤
│ P1: Main branch builds              │
│ Gets runner after P0 queue empty    │
├─────────────────────────────────────┤
│ P2: PR validation                   │
│ Share remaining capacity            │
├─────────────────────────────────────┤
│ P3: Scheduled/nightly jobs          │
│ Only run during off-peak            │
└─────────────────────────────────────┘

Cost impact:
- Reduce baseline runners: 400 → 200
- Increase auto-scaling max: 1200 → 1500
- Result: Better utilization, same peak capacity
- Savings: $100K/month
```

---

## Section 9: Security Deep Dive


### Secrets Management Evolution


**Phase 1: Environment Files (UNSAFE)**
```bash
# .env file committed to repo (worst case!)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
AWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE
DB_PASSWORD=super_secret_pass
```

**Risks**:
- Compromised forever in git history
- Visible to anyone with repo access
- Can't be revoked (in git forever)

**Phase 2: GitHub Secrets (Better)**
```yaml
steps:
  - run: npm install
    env:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**Security**:
- Encrypted at rest
- Only decrypted on runner
- Redacted from logs
- But: all org members can create workflows that use secrets

**Phase 3: OIDC Token Exchange (Best)**
```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: Assume AWS role
    uses: aws-actions/configure-aws-credentials@v2
    with:
      role-to-assume: arn:aws:iam::123456789:role/github-actions
      aws-region: us-east-1

  - name: Deploy
    run: aws s3 cp dist/ s3://bucket/
```

**Flow**:
```
GitHub Actions                   AWS
    │                            │
    ├─ Create OIDC token         │
    │  (signed by GitHub)        │
    │                            │
    ├─ Send to AWS STS ──────────→
    │                            │
    │                      Verify signature
    │                      Check thumbprint
    │                      Match subject claim
    │                            │
    │          ← Return temporary credentials ──┐
    │                                           │
    └─ Use in AWS CLI              (15 min TTL)
       (no static credentials!)
```

**Advantages**:
- No long-lived credentials
- Automatic rotation (15 min)
- Audit trail in AWS CloudTrail
- Scope-limited (specific repo, branch, environment)

### RBAC & Repository Secrets


```
GitHub Organization
├── Public Teams
│   ├── oncall (all repos)
│   │   └─ Write access to secrets
│   └── @backend (only backend/* repos)
│       └─ Read-only secrets
├── Secret Storage
│   ├── org-level
│   │   ├── CI_SIGNING_KEY (all repos)
│   │   └── SLACK_TOKEN (all repos)
│   └── repo-level (overrides org-level)
│       ├── production-deploy-key
│       └── aws-account-id
└── Access Control
    ├── Secret readable by: repo, team
    ├── Cannot list secrets via API
    ├── Cannot read value (only write)
    └── Audit logging (who created/accessed)
```

**Principle of Least Privilege**:
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read  # Only what we need
  
  deploy:
    runs-on: ubuntu-latest
    environment: production
    permissions:
      id-token: write  # For AWS assume-role
      contents: read
```

### Supply Chain Security


**Risk**: Compromised GitHub Action

```yaml
uses: actions/checkout@v4  # Trust GitHub's action

# vs

uses: some-user/malicious-action@v1  # Possible supply chain attack!
```

**Mitigation**:
```yaml
# Pin to specific commit hash (most secure)
uses: actions/checkout@a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

# Pin to semantic version (acceptable)
uses: actions/checkout@v4

# Never use: floating tags
uses: actions/checkout@main  # BAD!

# Verification
- name: Verify action checksum
  run: |
    EXPECTED="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    ACTUAL=$(sha256sum action.yml | cut -d' ' -f1)
    if [ "$EXPECTED" != "$ACTUAL" ]; then
      echo "Action checksum mismatch!"
      exit 1
    fi
```

### Audit Logging


```
What to audit:
┌──────────────────────────────────────┐
│ 1. Who accessed which secrets?       │
│ 2. Which jobs deployed what?         │
│ 3. Who approved environment deploy?  │
│ 4. Which runners executed this job?  │
│ 5. What artifacts were accessed?     │
└──────────────────────────────────────┘

Implementation:
1. All API calls logged to CloudTrail (AWS)
2. GitHub API audit log (org-level)
3. Workflow run logs (7-day retention)
4. Custom logging in deployment scripts

Query example:
```bash
gh api repos/{owner}/{repo}/actions/runs \
  --jq '.workflow_runs[] | 
    select(.conclusion=="failure") |
    {id, name, created_at, actor}'
```
```

---

## Section 10: Code Examples


### Complete Multi-Stage Workflow


```yaml
name: Build, Test, & Deploy

on:
  push:
    branches:
      - main
      - develop
    paths-ignore:
      - 'docs/**'
      - '*.md'
  pull_request:
    branches:
      - main
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

concurrency:
  group: ${{ github.ref }}
  cancel-in-progress: true

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  NODE_VERSION: '18'

jobs:
  metadata:
    name: Generate Build Metadata
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.value }}
      build-id: ${{ steps.version.outputs.build-id }}
      cache-key: ${{ steps.cache.outputs.key }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - id: version
        run: |
          VERSION=$(git describe --tags --always)
          BUILD_ID="${{ github.run_id }}-${{ github.run_number }}"
          echo "value=$VERSION" >> $GITHUB_OUTPUT
          echo "build-id=$BUILD_ID" >> $GITHUB_OUTPUT

      - id: cache
        run: |
          CACHE_KEY="node-cache-${{ hashFiles('**/package-lock.json') }}"
          echo "key=$CACHE_KEY" >> $GITHUB_OUTPUT

  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm

      - run: npm ci

      - name: ESLint
        run: npm run lint

      - name: Prettier check
        run: npm run format:check

      - uses: github/super-linter@v4
        env:
          DEFAULT_BRANCH: main
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  build:
    name: Build Application
    runs-on: ubuntu-latest
    needs: metadata
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm

      - run: npm ci
      - run: npm run build

      - uses: actions/upload-artifact@v3
        with:
          name: build-output-${{ needs.metadata.outputs.build-id }}
          path: dist/
          retention-days: 7

      - uses: docker/setup-buildx-action@v2

      - uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v4
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix={{branch}}-
            type=raw,value=${{ needs.metadata.outputs.version }}

      - uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  test-unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm

      - run: npm ci
      - run: npm run test:unit -- --coverage

      - uses: actions/upload-artifact@v3
        with:
          name: coverage-unit
          path: coverage/

      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
          flags: unit
          fail_ci_if_error: true

  test-integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: build
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm

      - run: npm ci

      - name: Run migrations
        run: npm run db:migrate
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/test

      - run: npm run test:integration -- --coverage
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379

      - uses: actions/upload-artifact@v3
        with:
          name: coverage-integration
          path: coverage/

  test-e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: npm

      - run: npm ci

      - name: Start application
        run: npm run start &
        env:
          PORT: 3000

      - name: Wait for application
        run: |
          for i in {1..30}; do
            if curl -f http://localhost:3000/health; then
              exit 0
            fi
            sleep 1
          done
          exit 1

      - uses: playwright/browsers-action@v1

      - run: npm run test:e2e

      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4

      - run: npm audit --production

      - uses: dependabot/fetch-metadata@v1
        id: metadata
        if: ${{ github.event_name == 'pull_request' }}

      - uses: github/super-linter/slim@v4
        env:
          DEFAULT_BRANCH: main
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, test-unit, test-integration, test-e2e, lint]
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-staging
          aws-region: us-east-1

      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster staging \
            --service myapp \
            --force-new-deployment

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "Staging deployment ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Staging Deployment* - ${{ job.status }}\n${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
                  }
                }
              ]
            }

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, test-unit, test-integration, test-e2e, lint]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: https://example.com
    concurrency:
      group: production-deploy
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-production
          aws-region: us-east-1
          duration-seconds: 900

      - name: Wait for approval
        if: ${{ github.event_name == 'workflow_dispatch' }}
        run: echo "Deployment approved via workflow_dispatch"

      - name: Blue-Green Deployment
        run: |
          # Get current active version
          CURRENT=$(aws ecs describe-services \
            --cluster production \
            --services myapp \
            --query 'services[0].taskDefinition' \
            --output text)

          # Deploy new version
          aws ecs update-service \
            --cluster production \
            --service myapp \
            --force-new-deployment

          # Wait for deployment
          aws ecs wait services-stable \
            --cluster production \
            --services myapp

          # Health check
          if ! curl -f https://example.com/health; then
            echo "Health check failed, rolling back..."
            exit 1
          fi

      - name: Update monitoring
        run: |
          aws cloudwatch put-metric-data \
            --namespace "Deployments" \
            --metric-name "DeploymentSuccess" \
            --value 1

      - name: Notify
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_PROD }}
          payload: |
            {
              "text": "🚀 Production deployment ${{ job.status }}"
            }
```

---

## Section 11: Production Incidents


### Incident 1: Cache Poisoning in Monorepo


**Timeline**:
- 14:00: Engineer A pushes to `shared-utils` package
- 14:05: Engineer B pushes to `frontend` package
- 14:07: Frontend tests fail (but pass locally!)
- 14:15: All frontend PRs failing
- 14:30: Root cause found and fixed

**Root Cause**:
```
Shared cache key: node_modules.tar.gz
Two engineers push simultaneously:
├─ shared-utils bumps lodash 4.17.20 → 4.17.21
└─ frontend uses lodash 4.17.20

Cache key based on monorepo root package-lock.json:
├─ Hash collides (same parent hash)
└─ Runner loads cached node_modules WITH newer lodash
    └─ Tests fail because frontend code expects old behavior

Timing:
1. A's job: install deps, create cache, upload
2. B's job: install deps, cache hit with A's cache!
3. B gets wrong version of lodash
```

**Fix**:
```yaml
# Separate cache per workspace
- uses: actions/setup-node@v3
  with:
    node-version: '18'
    # OLD: cache: npm (entire monorepo)
    # NEW: cache per package
    cache: npm
    cache-dependency-path: 'packages/${{ matrix.package }}/package-lock.json'

# Or use per-package key:
strategy:
  matrix:
    package: [shared-utils, frontend, backend]

- uses: actions/cache@v3
  with:
    path: packages/${{ matrix.package }}/node_modules
    key: ${{ matrix.package }}-${{ hashFiles('packages/${{ matrix.package }}/package-lock.json') }}
```

### Incident 2: State File Corruption in Terraform CI


**Timeline**:
- 10:00: Deploy job 1 starts (infrastructure changes)
- 10:01: Deploy job 2 starts (new env variables)
- 10:02: Job 1 acquires state lock
- 10:08: Job 1 applies and releases lock
- 10:09: Job 2 acquires lock, state file corrupted
- 11:00: Someone notices VMs not responsive

**Root Cause**:
```
Concurrent Terraform applies on same state file:
1. Job 1 acquires state lock (DynamoDB)
2. Job 1 reads state.json (1000 lines)
3. Job 2 acquires lock (timeout on lock)
   └─ Job 1 timed out reading (network lag)
   └─ Lock expired after 90 seconds
4. Job 2 reads stale state
5. Job 1 writes new state
6. Job 2 writes, overwriting Job 1's changes
7. State file now inconsistent (VM created but state missing)
```

**Prevention**:
```yaml
deploy:
  concurrency:
    group: terraform-state
    cancel-in-progress: false  # Queue, don't cancel

  steps:
    - uses: actions/checkout@v4

    - uses: hashicorp/setup-terraform@v2

    - name: Init with remote lock
      run: |
        terraform init \
          -backend-config="dynamodb_table=terraform-lock" \
          -backend-config="encrypt=true"

    - name: Plan with lock timeout
      run: terraform plan \
        -lock-timeout=5m \
        -out=tfplan

    # CRITICAL: Serialize applies
    - name: Apply (serialized)
      run: |
        # Acquire file lock to prevent parallel applies
        flock -e 200
        terraform apply -lock-timeout=10m tfplan
      exit_code: 200  # lock file descriptor
```

### Incident 3: Artifact Race Condition During Cleanup


**Timeline**:
- 15:30: Build job completes, uploads 2GB artifact
- 15:31: Artifact upload starts (takes 5 minutes)
- 15:31: Cleanup job runs (independent job)
- 15:32: Cleanup job deletes artifacts older than 30 days
- 15:33: Build artifact missing from index, but upload in progress
- 15:35: Upload completes, tries to register artifact
- 15:36: Download job starts, artifact 404

**Root Cause**:
```
Job dependency order:
cleanup-old-artifacts: (always runs, cleanup step)
build: depends on nothing, parallel with cleanup

Timeline:
0min:   build starts
0min:   cleanup starts (no dependency)
3min:   build completes, requests upload
3min:   cleanup queries S3 for artifacts > 30 days
4min:   cleanup deletes bucket/artifacts/run-123 (in progress upload!)
4min:   upload tries to write, path deleted
5min:   build finishes "upload", but file's gone
```

**Fix**:
```yaml
build:
  runs-on: ubuntu-latest
  steps:
    - run: npm run build
    - uses: actions/upload-artifact@v3
      with:
        name: build
        path: dist/

cleanup:
  # Add explicit dependency!
  needs: build  # Wait for build to complete
  if: always()
  runs-on: ubuntu-latest
  steps:
    - uses: actions/github-script@v6
      with:
        script: |
          // Only delete artifacts this job didn't just create
          const artifacts = await github.rest.actions.listArtifactsForRepo({
            owner: context.repo.owner,
            repo: context.repo.repo,
          });
          
          for (const artifact of artifacts.artifacts) {
            // Keep artifacts from current job
            if (artifact.workflow_run.id === context.runId) {
              continue;
            }
            
            const age = Date.now() - new Date(artifact.created_at).getTime();
            if (age > 30 * 24 * 60 * 60 * 1000) {
              await github.rest.actions.deleteArtifact({
                owner: context.repo.owner,
                repo: context.repo.repo,
                artifact_id: artifact.id,
              });
            }
          }
```

### Incident 4: Self-Hosted Runner Disk Full


**Symptom**: All jobs timeout waiting for runner availability

**Root Cause**:
```
Self-hosted runner specification:
├─ VM: 20GB disk (assumed sufficient)
├─ OS + tools: 5GB
├─ Available: 15GB
└─ Per job: clone repo + build = ~8GB

Timeline:
├─ Job 1: Clone (2GB) + Install (3GB) + Build (2GB) → 7GB
├─ Job 1: Cleanup → -7GB
├─ Job 2: Clone (2GB) + Install (3GB) + Build (2GB) → 7GB
│
│ PROBLEM: Large artifact generation
├─ Job 3: Generate test artifacts (5GB) → 5GB total
├─ Job 3: Upload artifact (5GB compressed to 3GB) → still 3GB used
├─ Job 3: Cleanup missing: no cleanup!
│
│ Now disk full with artifacts:
├─ Job 4: Clone fails (no space)
├─ Job 5: Clone fails
└─ All jobs timeout (no available runners)
```

**Prevention**:
```bash
#!/bin/bash
# /opt/runner-monitor.sh

MAX_DISK_USAGE=90
CHECK_INTERVAL=30

while true; do
  USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
  
  if [ "$USAGE" -gt "$MAX_DISK_USAGE" ]; then
    # Kill current job
    pkill -TERM -f "run.sh"
    
    # Aggressive cleanup
    rm -rf /tmp/*
    rm -rf ~/.cache/*
    docker system prune -af --volumes
    
    # Alert
    systemctl restart runner
  fi
  
  sleep $CHECK_INTERVAL
done
```

### Incident 5: Secret Exposure in Logs


**Timeline**:
- 10:00: Engineer deploys new logging
- 10:05: Logs show full request/response
- 10:10: Security team finds database password in logs
- 10:15: Password rotated

**Root Cause**:
```yaml
# Problematic logging:
steps:
  - name: Debug output
    run: |
      echo "Database URL: ${{ secrets.DB_URL }}"
      echo "All env vars:"
      env | sort  # EXPOSES ALL SECRETS!
      npm run deploy
```

**Fix**:
```yaml
steps:
  - name: Deploy
    run: npm run deploy
    # GitHub auto-redacts secrets from logs
    # But: engineer must be careful!

  # DANGEROUS - don't do this:
  # - run: echo $DB_PASSWORD

  # SAFE - GitHub redacts:
  # - run: curl -H "Authorization: Bearer ${{ secrets.TOKEN }}" ...
  #
  # Log output shows: Bearer ***

  # Safe debug output:
  - name: Debug (safe)
    run: |
      echo "Deploying to region: ${{ env.AWS_REGION }}"
      echo "Using SSL: ${{ env.USE_SSL }}"
      # No secrets!
```

---

## Section 12: GitHub Actions vs GitLab CI vs Jenkins


| Feature | GitHub Actions | GitLab CI | Jenkins |
|---------|---|---|---|
| **Hosting** | SaaS only | SaaS or self-hosted | Self-hosted only |
| **Configuration** | YAML (`.github/workflows/`) | YAML (`.gitlab-ci.yml`) | Groovy/YAML (Jenkinsfile) |
| **Runners** | GitHub-hosted + self-hosted | SaaS runners + self-hosted | Self-hosted agents |
| **Job Parallelization** | Default parallel (needs to sequence) | Default sequential (stages) | Configurable via DAG |
| **Pricing** | Free tier: 2K minutes/month | Free tier: 50K minutes/month | Free (self-hosted) |
| **Marketplace** | 10K+ public actions | 500+ extensions | 1K+ plugins |
| **Secrets Management** | Organization + repository | Organization + project | Credentials plugin |
| **RBAC** | Organization roles + CODEOWNERS | Project roles + protected refs | Jenkins users + groups |
| **Container Support** | Docker service containers | Service containers | Docker/Podman support |
| **Artifacts** | 5GB free tier, 1GB max file | 100GB free tier, 1GB max file | Configurable (S3 plugin) |
| **Caching** | GitHub cache action | Native cache directive | Cache plugin (S3) |
| **Matrix Builds** | Built-in (strategy.matrix) | Built-in (parallel keyword) | Manual (nested loops) |
| **Environments** | First-class (environment blocks) | Environments with protection | Via Groovy variables |
| **Status Checks** | Git status API | Merge request pipelines | Git webhook plugins |
| **Cost at Scale** | $0.008/minute after free tier | $0.008/minute after free tier | Infrastructure costs |
| **Learning Curve** | Easy (GitHub integration) | Medium (GitLab learning) | Steep (Groovy expertise) |
| **Enterprise Features** | SAML, IP allowlist | SAML, IP allowlist | LDAP, complex auth |
| **Deployment Approval** | Environment approval | Manual approval jobs | Manual approval plugins |

### Comparison: Build a Node.js app & deploy


**GitHub Actions**:
```yaml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: npm
      - run: npm ci && npm run build
      - run: npm test
      - run: npm run deploy
```
**Lines: 17 | Readability: High | Parallelization: Poor (sequential)**

**GitLab CI**:
```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  image: node:18
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
  cache:
    paths:
      - node_modules/

test:
  stage: test
  image: node:18
  script:
    - npm ci
    - npm test

deploy:
  stage: deploy
  image: node:18
  script:
    - npm run deploy
  only:
    - main
```
**Lines: 32 | Readability: Medium | Parallelization: Good (stages) | Artifact passing: Native**

**Jenkins**:
```groovy
pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh '''
          node --version
          npm ci
          npm run build
        '''
        archiveArtifacts artifacts: 'dist/**', allowEmptyArchive: false
      }
    }
    stage('Test') {
      steps {
        sh 'npm test'
        junit 'test-results/**/*.xml'
      }
    }
    stage('Deploy') {
      when {
        branch 'main'
      }
      steps {
        sh 'npm run deploy'
      }
    }
  }
}
```
**Lines: 30 | Readability: Low (Groovy) | Parallelization: Difficult | Flexibility: Very high**

---

## Section 13: Best Practices Checklist


- [ ] **Secrets**: Use OIDC tokens, not static credentials
- [ ] **Caching**: Cache dependencies, build outputs, Docker layers
- [ ] **Parallelization**: Run independent jobs in parallel
- [ ] **Concurrency**: Use `concurrency` groups for deploy safety
- [ ] **Artifacts**: Clean up after 7-30 days, not forever
- [ ] **Logs**: Don't print secrets; GitHub redacts but be careful
- [ ] **Permissions**: Principle of least privilege (only needed scopes)
- [ ] **Testing**: Unit + integration + E2E, parallel where possible
- [ ] **Monitoring**: Alert on failures, track queue times
- [ ] **Documentation**: Keep workflow README updated
- [ ] **Cost**: Monitor minutes usage, optimize runner utilization
- [ ] **Security**: Audit action versions, use approved actions only

---

## Conclusion


GitHub Actions and GitLab CI are powerful, but understanding their internals is critical for production systems. Master YAML parsing, runner execution, artifact storage, and security to build reliable CI/CD pipelines that scale to thousands of repositories.

Key takeaways:
1. **Workflows are declarative**, not imperative
2. **Runners are ephemeral** (isolation, cost benefit)
3. **Caching is crucial** (3 minutes → 30 seconds)
4. **Concurrency requires discipline** (race conditions everywhere)
5. **Security is hard** (secrets, supply chain, RBAC)
6. **Monitoring is essential** (queue times, failures, costs)


## Observability


```mermaid
flowchart LR
    A[Docker Host] --> B[Metrics]
    A --> C[Logs]
    B --> E[Prometheus/cAdvisor]
    C --> F[Loki/ELK]
    E --> H[Grafana]
    F --> H
    H --> I[Alerts]
```

### Key Metrics


| Metric | Unit | Threshold | Indicates |
|--------|------|-----------|-----------|
| Container CPU usage | % | < 80% of limit | CPU contention |
| Container memory usage | % | < 80% of limit | Memory pressure |
| Container restart count | count/min | 0 | CrashLoop |
| Image pull latency | s | < 30s | Registry issues |
| Docker daemon file descriptors | count | < 70% of ulimit | Daemon health |
| Layer cache hit rate | % | > 50% | Build efficiency |
| Disk usage (overlay2) | % | < 80% | Cleanup needed |

### Logs


- **ERROR**: Container exit code != 0, OOMKilled, daemon errors, storage driver errors
- **WARN**: Image pull slow, container restart, resource limit approaching, DNS resolution slow
- **INFO**: Container start/stop, image pull complete, daemon ready, network created

### Alerts


| Severity | Condition | Response |
|----------|-----------|----------|
| P0 | Container restarts > 3/min | Investigate crash |
| P1 | Disk usage > 85% | Clean up images/volumes |
| P1 | Daemon unresponsive | Restart dockerd |
| P2 | Image pull > 60s | Check registry mirror |

### Dashboards


**Docker Host Dashboard**: container count, CPU/memory/disk per container, restart rate, image size distribution, layer usage.
