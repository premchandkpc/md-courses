# Airflow and Dagster

## Airflow Overview


Apache Airflow is a platform to programmatically author, schedule, and monitor workflows. It uses Directed Acyclic Graphs (DAGs) to represent workflows, where nodes are tasks and edges are dependencies. Airflow was created at Airbnb in 2014 and became an Apache top-level project in 2019.

## Airflow Architecture


```mermaid
graph TB
    subgraph UI["🖥️ Web Layer"]
        WEB["Webserver<br/>Flask UI + REST API"]
    end
    
    subgraph SCHED["⚙️ Control Layer"]
        PARSER["DAG Processor<br/>Parse DAG files"]
        SCHEDULER["Scheduler<br/>Create DagRuns<br/>Queue tasks"]
    end
    
    subgraph EXEC["🚀 Execution Layer"]
        WORKER1["Worker 1<br/>Execute tasks"]
        WORKER2["Worker 2<br/>Execute tasks"]
        WORKERN["Worker N<br/>Execute tasks"]
    end
    
    subgraph STORE["💾 Storage & Coordination"]
        DB["Metadata DB<br/>PostgreSQL/MySQL<br/>DAGs, Runs, Tasks, Variables"]
        BROKER["Message Broker<br/>Redis/RabbitMQ<br/>Task Queue"]
    end
    
    WEB --> DB
    PARSER --> DB
    SCHEDULER --> DB
    SCHEDULER --> BROKER
    BROKER --> WORKER1
    BROKER --> WORKER2
    BROKER --> WORKERN
    WORKER1 --> DB
    WORKER2 --> DB
    WORKERN --> DB
    
    style WEB fill:#4a8bc2
    style PARSER fill:#2d5a7b
    style SCHEDULER fill:#c73e1d
    style WORKER1 fill:#1a5d3a
    style WORKER2 fill:#1a5d3a
    style WORKERN fill:#1a5d3a
    style DB fill:#1a3a52
    style BROKER fill:#2d5a7b
```

### Components


#### Webserver
- Flask web application serving the Airflow UI
- Reads DAGs from the database (serialized DAGs)
- Provides REST API for external integration
- Must be stateless for HA deployments

#### Scheduler
The scheduler is a multi-threaded process that:

1. **DAG parsing loop**: Reads DAG files, creates DagBag, serializes DAGs
2. **DAG processing**: Determines which DAG runs to create based on schedule
3. **Task scheduling**: Creates task instances and queues them for execution
4. **Task monitoring**: Tracks task state transitions (queued → running → success/fail)

```
Scheduler Loop (every ~5 seconds):
  1. Parse DAG files (DagFileProcessorManager)
  2. Create DagRuns for scheduled DAGs
  3. Calculate task dependencies in each DagRun
  4. Queue ready tasks to executor (set to "scheduled" state)
  5. Send tasks to executor for execution
  6. Process executor events (task success/fail)
  7. Handle cleanup/timeouts
  8. Sleep until next loop
```

**Scheduler HA** (Airflow 2.0+):
- Run multiple scheduler processes with `airflow scheduler`
- Uses database-level locking to prevent duplicate task scheduling
- HA database connection pooling required (PgBouncer for Postgres)

#### Executor

The executor defines how tasks are run:

| Executor | How Tasks Run | Scaling | Best For |
|----------|--------------|---------|----------|
| **SequentialExecutor** | 1 task at a time in scheduler process | None | Testing, SQLite |
| **LocalExecutor** | Multiple processes on one machine | Vertical | Single node, dev |
| **CeleryExecutor** | Distributed via Celery workers | Horizontal (add workers) | Production |
| **KubernetesExecutor** | Each task in its own K8s Pod | Autoscaling (K8s) | Cloud-native |
| **CeleryKubernetesExecutor** | Mix: queue + K8s Pod per task | Hybrid | Mixed workloads |

```python
# airflow.cfg setting
executor = CeleryExecutor
```

#### DAG Processor

Introduced in Airflow 2.0 to separate DAG parsing from scheduling:

```
DagFileProcessorManager:
  - Manages file processing in parallel (configurable threads)
  - Parses DAG files in child processes
  - Serializes parsed DAGs to database (DagModel.serialized_dag)
  - Detects file changes (timestamp-based)
```

```python
# How many DAG files to parse in parallel
core.parsing_processes = 4
core.dagbag_import_timeout = 30
core.max_active_parsing_processes = 8
```

## DAG Design


### Basic DAG


```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "data_team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["alerts@company.com"],
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
    "sla": timedelta(hours=1),
}

with DAG(
    dag_id="etl_pipeline",
    default_args=default_args,
    description="Main ETL pipeline",
    schedule_interval="0 */6 * * *",       # Every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "production"],
    max_active_runs=1,
    concurrency=16,
) as dag:

    start = BashOperator(
        task_id="start_pipeline",
        bash_command="echo 'Starting ETL'",
    )

    def extract(**context):
        execution_date = context["execution_date"]
        data = read_from_api(execution_date)
        return data

    extract_task = PythonOperator(
        task_id="extract_data",
        python_callable=extract,
        provide_context=True,
    )

    start >> extract_task
```

### Task Lifecycle


```
       +---> Scheduled ---> Queued ---> Running ---> Success
       |                                              |
None --+                                              +---> Failed ---> Upstream Failed
       |                                              |
       +---> Skipped (Branch)                         +---> Removed
                                                     |
                                                     +---> Shutdown
```

### Dependencies and Branching


```python
from airflow.models.baseoperator import chain
from airflow.operators.python import BranchPythonOperator

def choose_branch(**context):
    """Route based on a condition."""
    if context["params"].get("mode") == "full_refresh":
        return ["delete_all", "full_load"]
    return ["incremental_load"]

branch = BranchPythonOperator(
    task_id="choose_strategy",
    python_callable=choose_branch,
)

def should_retry(**context):
    return "retry_load"

retry_lookup = BranchPythonOperator(
    task_id="should_retry",
    python_callable=should_retry,
)

# Define tasks
ingest = PythonOperator(task_id="ingest", python_callable=lambda: ...)
delete_all = PostgresOperator(task_id="delete_all", sql="TRUNCATE target_table")
full_load = PythonOperator(task_id="full_load", python_callable=lambda: ...)
incremental_load = PythonOperator(task_id="incremental_load", python_callable=lambda: ...)
retry_load = PythonOperator(task_id="retry", python_callable=lambda: ...)

# Dependencies
start >> branch
branch >> delete_all >> full_load
branch >> incremental_load
full_load >> ingest
incremental_load >> ingest_hook

# Trigger rules
ingest.trigger_rule = "none_failed"  # Run if any upstream succeeded
retry_load.trigger_rule = "one_failed"  # Run if at least one failed

chain(start, branch, [delete_all >> full_load, incremental_load], finish)
```

**Trigger rules**:
```
ALL_SUCCESS    (default)    All upstream succeeded
ALL_FAILED                  All upstream failed
ALL_DONE                    All upstream done (regardless of state)
ONE_SUCCESS                 At least one upstream succeeded
ONE_FAILED                  At least one upstream failed
NONE_FAILED                 No upstream failed (some may be skipped)
NONE_SKIPPED                No upstream skipped
NONE_FAILED_OR_SKIPPED      No upstream failed or skipped
DUMMY                       Always, no dependencies
```

### Task Groups


```python
from airflow.utils.task_group import TaskGroup

with DAG("data_pipeline", ...) as dag:

    with TaskGroup("data_quality_checks") as dq:
        check_null_rates = PythonOperator(task_id="null_rates", ...)
        check_uniqueness = PythonOperator(task_id="uniqueness", ...)
        check_freshness = PythonOperator(task_id="freshness", ...)

        [check_null_rates, check_uniqueness, check_freshness]

    with TaskGroup("load_layer") as load:
        load_bronze = PythonOperator(task_id="bronze", ...)
        load_silver = PythonOperator(task_id="silver", ...)
        load_gold = PythonOperator(task_id="gold", ...)

        load_bronze >> load_silver >> load_gold

    # Task groups behave as a single unit for dependency
    start >> dq >> load >> finish

# In the UI, task groups are collapsible:
# data_pipeline/
#   start
#   data_quality_checks/     ← Collapsed
#   load_layer/             ← Collapsible
#     bronze
#     silver
#     gold
#   finish
```

### SubDAGs (Legacy)


SubDAGs were replaced by Task Groups in Airflow 2.0:

```python
from airflow.models import DAG
from airflow.operators.subdag import SubDagOperator

def subdag_factory(parent_dag_name, child_dag_name, args):
    with DAG(
        dag_id=f"{parent_dag_name}.{child_dag_name}",
        default_args=args,
    ) as dag:
        task1 = DummyOperator(task_id="task1")
        task2 = DummyOperator(task_id="task2")
        task3 = DummyOperator(task_id="task3")
        task1 >> task2 >> task3
    return dag

# In parent DAG
subdag = SubDagOperator(
    task_id="process_chunk",
    subdag=subdag_factory("main_dag", "process_chunk", default_args),
)
```

## Executors in Detail


### Celery Executor


```
+-------------+     +-------------+     +-------------+
|  Scheduler  |     |  Scheduler  |     |  Scheduler  |
|    Node 1   |     |    Node 2   |     |    Node 3   |
+------+------+     +------+------+     +------+------+
       |                   |                   |
       +-------------------+-------------------+
                           |
                   +-------v--------+
                   |   Message      |
                   |   Broker       |
                   | (Redis/RMQ)    |
                   +-------+--------+
                           |
           +---------------+---------------+
           |               |               |
    +------v------+ +------v------+ +------v------+
    |   Worker 1  | |   Worker 2  | |   Worker N  |
    |  (pool=16)  | |  (pool=16)  | |  (pool=16)  |
    +------+------+ +------+------+ +------+------+
           |               |               |
           +-------+-------+--------+------+
                   |                |
           +-------v--------+  +----v--------+
           |  Flower Monitor|  | Database    |
           |  (Celery UI)   |  | (results)   |
           +----------------+  +-------------+
```

```python
# airflow.cfg for CeleryExecutor
executor = CeleryExecutor

# Broker configuration
broker_url = redis://:password@redis-host:6379/0
result_backend = db+postgresql://user:pass@db-host/airflow

# Worker configuration
worker_concurrency = 16
worker_prefetch_mode = last_task_only
worker_umask = 0007
worker_terminate_on_deprocessing = True

# Celery-specific
celery_app_name = airflow.providers.celery.executors.celery_executor
celeryd_concurrency = 16
celery_flower_url = http://flower:5555

# Queue routing
default_queue = default
# Priority queues:
#   high_priority, default, low_priority
```

**Queue routing**:
```python
task1 = PythonOperator(task_id="critical", queue="high_priority", ...)
task2 = PythonOperator(task_id="batch", queue="low_priority", ...)

# Start workers for specific queues:
# airflow celery worker -q high_priority
# airflow celery worker -q default
# airflow celery worker -q low_priority
```

### Kubernetes Executor


```
+-------------+     +-------------+
|  Scheduler  |     |  Webserver  |
+------+------+     +------+------+
       |                   |
       +-------------------+
       |
+------v------+
| K8s API     |
| Server      |
+------+------+
       |
       | watch for Pod events
       v
+------+------+  +------+------+  +------+------+
| Pod (Task 1)|  | Pod (Task 2)|  | Pod (Task N)|
| +----------+|  | +----------+|  | +----------+|
| | Worker   ||  | | Worker   ||  | | Worker   ||
| | Container||  | | Container||  | | Container||
| +----------+|  | +----------+|  | +----------+|
| +----------+|  | +----------+|  | +----------+|
| | Git-sync  ||  | | Airflow  ||  | | Airflow  ||
| | Sidecar  ||  | | Init     ||  | | Init     ||
| +----------+|  | +----------+|  | +----------+|
+-------------+  +-------------+  +-------------+
```

```python
from airflow.kubernetes.secret import Secret
from airflow.kubernetes.pod import PodDefaults

# airflow.cfg for Kubernetes Executor
executor = KubernetesExecutor

[kubernetes_executor]
pod_template_file = /opt/airflow/pod_template.yaml
worker_container_repository = myregistry/airflow-worker
worker_container_tag = latest
namespace = airflow
delete_worker_pods = True
delete_worker_pods_on_failure = False
worker_pods_creation_batch_size = 1
max_pods_per_pending = 100  # Prevent overwhelming K8s API
```

```yaml
# pod_template.yaml
apiVersion: v1
kind: Pod
metadata:
  name: airflow-worker
  labels:
    app: airflow-worker
spec:
  containers:
    - name: base
      image: myregistry/airflow-worker:latest
      command: ["airflow", "tasks", "run"]
      args: ["{{ dag_id }}", "{{ task_id }}", "{{ execution_date }}"]
      env:
        - name: AIRFLOW__CORE__EXECUTOR
          value: "LocalExecutor"
      resources:
        requests:
          cpu: 1
          memory: 2Gi
        limits:
          cpu: 2
          memory: 4Gi
```

### CeleryKubernetes Executor (Hybrid)


```python
executor = CeleryKubernetesExecutor

# Routes tasks:
#   queue="kubernetes" → runs in K8s pod
#   queue="celery" → runs in Celery worker
#   default (no queue) → Celery

heavy_task = BashOperator(
    task_id="heavy_computation",
    queue="kubernetes",        # Will launch K8s pod
)

quick_task = PythonOperator(
    task_id="quick_transform",
    queue="celery",            # Will use Celery worker pool
)
```

## Operators


### Built-in Operators


```python
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonVirtualenvOperator
from airflow.operators.email import EmailOperator
from airflow.operators.http import SimpleHttpOperator

# PythonOperator: run any Python function
PythonOperator(
    task_id="process_data",
    python_callable=my_function,
    op_kwargs={"param1": "value1"},
    provide_context=True,  # Pass task_instance, dag_run, etc.
)

# PythonVirtualenvOperator: run in isolated venv
PythonVirtualenvOperator(
    task_id="isolated_task",
    python_callable=train_model,
    requirements=["scikit-learn==1.0", "pandas"],
    system_site_packages=False,
)

# BashOperator: execute bash command
BashOperator(
    task_id="run_script",
    bash_command="/opt/scripts/etl.sh {{ ds }}",
    env={"AWS_DEFAULT_REGION": "us-east-1"},
)
```

### Provider Operators


```python
# AWS
from airflow.providers.amazon.aws.operators.s3 import S3ListOperator
from airflow.providers.amazon.aws.operators.emr import EmrAddStepsOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.operators.redshift import RedshiftSQLOperator

# GCP
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from airflow.providers.google.cloud.operators.gcs import GCSListObjectsOperator

# Snowflake
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

# Docker
from airflow.providers.docker.operators.docker import DockerOperator
DockerOperator(
    task_id="run_in_container",
    image="my-etl-image:latest",
    command="python run.py",
    network_mode="bridge",
    auto_remove=True,
    docker_url="unix://var/run/docker.sock",
    environment={"VAR": "value"},
    force_pull=False,
)

# KubernetesPodOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

k8s_task = KubernetesPodOperator(
    task_id="kubernetes_task",
    name="spark-job",
    namespace="data",
    image="gcr.io/my-project/spark-runner:latest",
    cmds=["spark-submit"],
    arguments=["--class", "com.example.Main", "local:///app/job.jar"],
    labels={"app": "spark", "team": "data"},
    startup_timeout_seconds=300,
    container_resources=Resources(
        request_memory="4G",
        request_cpu="2",
        limit_memory="8G",
        limit_cpu="4",
    ),
    is_delete_operator_pod=True,
    in_cluster=True,
    config_file=None,
)
```

### Sensors


Sensors are operators that wait for a condition to be true:

```python
from airflow.sensors.filesystem import FileSensor
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.apache.hive.sensors.named_hive_partition import NamedHivePartitionSensor

# Wait for file
wait_for_file = FileSensor(
    task_id="wait_for_data",
    filepath="/data/landing/{{ ds }}/_SUCCESS",
    fs_conn_id="fs_default",
    poke_interval=60,        # Check every 60s
    timeout=3600,            # Timeout after 1 hour
    soft_fail=False,         # Fail if timeout
)

# S3 key sensor
wait_for_s3 = S3KeySensor(
    task_id="wait_for_s3_file",
    bucket_key="s3://data-raw/{{ ds }}/events/*.json",
    bucket_name=None,
    wildcard_match=True,
    aws_conn_id="aws_default",
    poke_interval=30,
    timeout=7200,
)

# Deferrable sensor (Airflow 2.2+, async)
from airflow.sensors.filesystem import FileSensor
from airflow.triggers.file import FileTrigger

deferrable_sensor = FileSensor(
    task_id="async_wait",
    filepath="/data/landing/ready.txt",
    deferrable=True,  # Uses async trigger, frees worker slot
    poke_interval=10,
)
```

### Deferrable Operators


Airflow 2.2+ supports deferrable operators that release worker slots while waiting:

```python
from airflow.providers.amazon.aws.sensors.emr import EmrJobFlowSensor

# Traditional (uses a worker slot while poking)
emr_sensor_old = EmrJobFlowSensor(
    task_id="wait_emr",
    job_flow_id="j-XXXXX",
    poke_interval=60,
)

# Deferrable (releases worker, uses trigger)
emr_sensor_new = EmrJobFlowSensor(
    task_id="wait_emr_async",
    job_flow_id="j-XXXXX",
    poke_interval=60,
    deferrable=True,
)
```

**Deferrable vs blocking**:
```
Blocking:
  [Worker: Waits 5 minutes polling S3 → continues]

Deferrable:
  [Worker: Sets up trigger → returns to pool]
  [Trigger: Polls asynchronously → signals completion]
  [Worker (same or different): Resumes from trigger]
```

## Production Airflow


### CI/CD for DAGs


```yaml
# .github/workflows/dag-ci.yml
name: DAG CI
on:
  pull_request:
    paths:
      - "dags/**"
      - "plugins/**"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          pip install apache-airflow[all]==2.6.0
          pip install pytest

      - name: Validate DAGs
        run: |
          airflow dags list
          python -c "
import sys
from airflow.models import DagBag
dagbag = DagBag(dag_folder='dags/', include_examples=False)
if dagbag.import_errors:
    for file, err in dagbag.import_errors.items():
        print(f'ERROR in {file}: {err}')
    sys.exit(1)
print(f'{len(dagbag.dags)} DAGs validated successfully')
          "

      - name: Run DAG tests
        run: pytest tests/
```

### Testing DAGs


```python
# tests/test_etl_dag.py
from datetime import datetime
import pytest
from airflow.models import DagBag

@pytest.fixture
def dagbag():
    return DagBag(dag_folder="dags/", include_examples=False)

class TestETL:
    def test_dag_loaded(self, dagbag):
        dag = dagbag.get_dag("etl_pipeline")
        assert dag is not None
        assert len(dag.tasks) == 10

    def test_dag_structure(self, dagbag):
        dag = dagbag.get_dag("etl_pipeline")
        # Verify expected task count
        assert len(dag.tasks) >= 5

    def test_no_cycles(self, dagbag):
        for dag_id in dagbag.dags:
            dag = dagbag.get_dag(dag_id)
            dag.validate()  # Raises AirflowException if cycle

    def test_task_dependencies(self, dagbag):
        dag = dagbag.get_dag("etl_pipeline")
        extract = dag.get_task("extract_data")
        assert "validate_data" in extract.downstream_task_ids

    def test_schedule_interval(self, dagbag):
        dag = dagbag.get_dag("etl_pipeline")
        assert dag.schedule_interval == "0 */6 * * *"

    def test_default_args_override(self, dagbag):
        dag = dagbag.get_dag("etl_pipeline")
        for task in dag.tasks:
            if task.task_id == "critical_task":
                assert task.retries == 3  # Overrides default

    def test_task_sla_set(self, dagbag):
        dag = dagbag.get_dag("etl_pipeline")
        for task in dag.tasks:
            if task.task_id == "long_running":
                assert task.sla is not None
```

### Backfilling


```python
# CLI backfill
airflow dags backfill \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --reset-dagruns \
    etl_pipeline

# Run specific tasks
airflow tasks run etl_pipeline extract_data 2024-01-15

# Clear task instances for re-run
airflow tasks clear etl_pipeline \
    --downstream \
    --recursive \
    --task-regex "load_*" \
    --start-date 2024-01-01 \
    --end-date 2024-01-10
```

### SLAs


```python
with DAG(
    default_args={
        "sla": timedelta(hours=2),         # Notify if task runs > 2h
        "execution_timeout": timedelta(hours=4),  # Force kill at 4h
        "sla_miss_callback": sla_callback_function,
    },
    # Per-task SLA (overrides default)
) as dag:
    task1 = PythonOperator(
        task_id="slow_task",
        sla=timedelta(hours=1),
        ...
    )
```

**SLA notifications**:
```
Database: sla_miss table
Email:    sent to task.sla_miss_callback or default email_on_failure
Channel:  Slack/PagerDuty via callbacks
```

### Pool Management


```python
# airflow.cfg
# Define pools in the UI or CLI:
# airflow pools set heavy_pool 5 "For heavy ETL tasks"
# airflow pools set light_pool 20 "For light tasks"

with DAG("pipeline") as dag:
    heavy = PythonOperator(
        task_id="heavy_task",
        pool="heavy_pool",      # Limits to 5 concurrent runs
        pool_slots=2,           # Each instance takes 2 slots
        priority_weight=10,     # Higher = scheduled first
    )

    light = PythonOperator(
        task_id="light_task",
        pool="light_pool",
        pool_slots=1,
    )

    # Default pool: uses default_pool with max 16 slots
```

### Task Isolation


```python
# 1. PythonVirtualenvOperator
PythonVirtualenvOperator(
    task_id="isolated_task",
    python_callable=train_model,
    requirements=["numpy==1.24", "pandas==2.0"],
)

# 2. DockerOperator
DockerOperator(
    task_id="docker_isolated",
    image="python:3.10-slim",
    command="python /scripts/run.py",
    mounts=[Mount(source="/data", target="/data", type="bind")],
)

# 3. KubernetesPodOperator
KubernetesPodOperator(
    task_id="k8s_isolated",
    image="my-project/custom-image:latest",
    container_resources=k8s.V1ResourceRequirements(
        requests={"cpu": "2", "memory": "4Gi"},
    ),
)

# 4. ExternalTaskSensor (cross-DAG dependencies)
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_upstream = ExternalTaskSensor(
    task_id="wait_for_etl_dag",
    external_dag_id="upstream_etl",
    external_task_id="final_load",
    allowed_states=["success"],
    execution_delta=timedelta(hours=1),  # Wait for previous DAG run
)
```

## Dagster Overview


Dagster is a data orchestrator designed for building, testing, and monitoring data pipelines. It introduces the concept of **software-defined assets** (SDAs) — assets that are defined in code with their dependencies explicit.

## Dagster vs Airflow


| Feature | Airflow | Dagster |
|---------|---------|---------|
| **Core abstraction** | Tasks + DAGs | Software-defined assets |
| **Data awareness** | Limited (XComs) | First-class (I/O managers) |
| **Testing** | Complex mocking | Simple (pure ops/graphs) |
| **Asset lineage** | Manual tracking | Automatic |
| **Type system** | None | Dagster Types |
| **Partitioning** | Manual (params) | First-class partitions |
| **Backfill** | CLI command | Built-in, UI-driven |
| **Scaling** | Celery/K8s executors | Multiprocess/K8s executors |
| **Config** | Jinja templates | Pydantic-like config schemas |
| **Monitoring** | SLAs, alerts | Asset health, sensors |
| **CI/CD** | DAG validation tests | `dagster dev` testing |

### Software-Defined Assets


```python
from dagster import asset, Output, Out, AssetIn
import pandas as pd

@asset
def raw_events() -> pd.DataFrame:
    """Raw events ingested from API."""
    return pd.read_csv("s3://data-landing/events.csv")

@asset
def cleaned_events(raw_events: pd.DataFrame) -> pd.DataFrame:
    """Cleaned events with nulls removed and types cast."""
    df = raw_events.dropna(subset=["user_id", "event_type"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

@asset
def daily_metrics(cleaned_events: pd.DataFrame) -> pd.DataFrame:
    """Daily aggregated metrics per event type."""
    return cleaned_events.groupby(
        [cleaned_events["timestamp"].dt.date, "event_type"]
    ).size().reset_index(name="count")

# Dependencies are automatically derived from function signatures
# Running daily_assets will automatically run cleaned_events and raw_events

# Materialize in the UI or via:
# dagster asset materialize --select daily_metrics
```

### Asset Dependencies


```python
@asset(
    key_prefix=["s3", "bronze"],      # dbt-style key prefix
    group_name="ingestion",
    io_manager_key="s3_io",           # Custom I/O manager
    partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"),
    kinds={"python", "pandas"},       # Asset kind tags
)
def raw_events() -> pd.DataFrame:
    ...

@asset(
    ins={
        "events": AssetIn(
            key_prefix=["s3", "bronze"],
            partition_mapping=TimeWindowPartitionMapping(),  # Same partition
        )
    },
    group_name="cleaning",
    required_resource_keys={"database"},
)
def cleaned_events(events: pd.DataFrame) -> pd.DataFrame:
    ...


# Partitioned asset
@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"),
)
def daily_sales(context) -> pd.DataFrame:
    """Sales data partitioned by day."""
    partition_date = context.partition_key
    df = read_from_db(partition_date)
    return df
```

### Ops and Graphs


Dagster offers a lower-level API for composing steps:

```python
from dagster import op, graph, Out, In, job
from dagster import DagsterType

# Define a custom type
DataFrameType = DagsterType(
    name="DataFrame",
    type_check_fn=lambda _, value: isinstance(value, pd.DataFrame),
)

@op(out=Out(DataFrameType))
def extract() -> pd.DataFrame:
    return pd.read_csv("data.csv")

@op(ins={"raw_data": In(DataFrameType)})
def clean(raw_data: pd.DataFrame) -> pd.DataFrame:
    return raw_data.dropna()

@op(ins={"clean_data": In(DataFrameType)})
def analyze(clean_data: pd.DataFrame) -> dict:
    return {"row_count": len(clean_data), "columns": list(clean_data.columns)}

@graph
def etl():
    result = analyze(clean(extract()))
    return result

# Create job from graph
etl_job = etl.to_job(
    resource_defs={"io_manager": fs_io_manager}
)
```

### Schedules and Sensors


```python
from dagster import schedule, sensor, RunRequest, SkipReason
from dagster import DefaultScheduleStatus

# Schedule
@schedule(
    job=etl_job,
    cron_schedule="0 6 * * *",
    default_status=DefaultScheduleStatus.RUNNING,
    execution_timezone="US/Eastern",
)
def daily_etl_schedule():
    return {}

# Sensor (event-driven)
@sensor(job=etl_job)
def s3_sensor(context):
    """Check S3 for new files and trigger runs."""
    new_files = check_s3_for_new_files()
    if new_files:
        context.log.info(f"Found {len(new_files)} new files")
        for f in new_files:
            yield RunRequest(
                run_key=f,
                run_config={
                    "ops": {
                        "extract": {"config": {"file_path": f}}
                    }
                },
            )
    else:
        yield SkipReason("No new files found")

# Multi-asset sensor
@sensor(asset_selection=["raw_events", "cleaned_events"])
def upstream_sensor(context):
    if upstream_pipeline_completed():
        return RunRequest()
```

### I/O Managers


```python
from dagster import IOManager, io_manager, InputContext, OutputContext
import pandas as pd

class ParquetIOManager(IOManager):
    def __init__(self, base_path: str):
        self.base_path = base_path

    def handle_output(self, context: OutputContext, obj: pd.DataFrame):
        """Write DataFrame to Parquet."""
        asset_key = context.asset_key.path
        path = self.base_path + "/" + "/".join(asset_key) + ".parquet"
        obj.to_parquet(path)
        context.log.info(f"Written to {path}")

    def load_input(self, context: InputContext) -> pd.DataFrame:
        """Read DataFrame from Parquet."""
        asset_key = context.asset_key.path
        path = self.base_path + "/" + "/".join(asset_key) + ".parquet"
        return pd.read_parquet(path)

@io_manager(required_resource_keys={"database"})
def db_io_manager(init_context):
    """I/O manager that reads/writes from database."""
    return DatabaseIOManager(init_context.resources.database)

# Use in assets
@asset(io_manager_key="parquet_io")
def my_asset() -> pd.DataFrame:
    ...
```

### Dagster Configuration


```yaml
# workspace.yaml
load_from:
  - python_module:
      module_name: my_project.definitions
      location_name: prod

# dagster.yaml
scheduler:
  module: dagster.core.scheduler
  class: DagsterDaemonScheduler

run_coordinator:
  module: dagster.core.run_coordinator
  class: QueuedRunCoordinator
  config:
    max_concurrent_runs: 10

run_launcher:
  module: dagster.core.launcher
  class: DefaultRunLauncher

storage:
  postgres:
    postgres_db:
      username: dagster
      password: password
      hostname: postgres
      db_name: dagster
      port: 5432
```

### Dagster Partitioning


```python
from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    WeeklyPartitionsDefinition,
    MonthlyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    DynamicPartitionsDefinition,
    TimeWindowPartitionMapping,
)

# Time-based partitions
daily = DailyPartitionsDefinition(start_date="2024-01-01")
hourly = HourlyPartitionsDefinition(start_date="2024-01-01")
weekly = WeeklyPartitionsDefinition(start_date="2024-01-01")

# Static partitions (e.g., countries)
countries = StaticPartitionsDefinition(["US", "UK", "DE", "JP", "AU"])

# Multi-dimensional partitions
@asset(
    partitions_def=MultiPartitionsDefinition(
        partitions_defs={
            "date": DailyPartitionsDefinition(start_date="2024-01-01"),
            "country": StaticPartitionsDefinition(["US", "UK", "DE"]),
        }
    )
)
def sales_by_region(context):
    partition = context.partition_key.keys_by_dimension
    date = partition["date"]
    country = partition["country"]
    df = query_sales(date, country)
    return df

# Dynamic partitions (created at runtime)
@asset(
    partitions_def=DynamicPartitionsDefinition(name="customers"),
)
def customer_report(context):
    customer_id = context.partition_key
    return generate_report(customer_id)
```

## Airflow at Scale


### HA Scheduler


```yaml
# docker-compose for HA Airflow
version: "3.8"
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: airflow

  scheduler:
    image: apache/airflow:2.6.0
    command: airflow scheduler
    depends_on: [postgres]
    replicas: 3  # Multiple scheduler instances
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__SCHEDULER__PARSING_PROCESSES: 4
      AIRFLOW__SCHEDULER__MAX_DAGRUNS_PER_LOOP: 50
      AIRFLOW__SCHEDULER__SCHEDULER_HEARTBEAT_SEC: 10

  triggerer:
    image: apache/airflow:2.6.0
    command: airflow triggerer
    replicas: 2
```

### DAG Serialization


Airflow 2.0+ serializes DAGs to the database, decoupling parsing from scheduling:

```python
# airflow.cfg
core.store_serialized_dags = True
core.min_serialized_dag_update_interval = 30
core.min_serialized_dag_fetch_interval = 10

# Benefits:
# - Webserver reads serialized DAGs (no parsing)
# - Scheduler parses in parallel, stores to DB
# - Reduced webserver memory
# - Consistent DAG representation
```

### Airflow Performance Tuning


```python
# Scheduler tuning
scheduler.parsing_processes = 4             # DAG parsing parallelism
scheduler.max_dagruns_per_loop = 50          # Maximum DAG runs per loop
scheduler.max_tis_per_query = 512            # Task instances per query
scheduler.scheduler_heartbeat_sec = 10       # HA heartbeat interval
scheduler.scheduler_idle_sleep_time = 0.5    # Sleep between loops

# DAG processing
core.dagbag_import_timeout = 60               # Max import time
core.max_active_parsing_processes = 8         # Max concurrent parsers
core.max_active_runs_per_dag = 16             # Max concurrent DAG runs

# Task scheduling
core.task_runner = StandardTaskRunner         # or LocalTaskJob
core.parallelism = 128                        # Max total tasks
core.dag_concurrency = 16                     # Max tasks per DAG

# Database
sql_alchemy_pool_enabled = True
sql_alchemy_pool_size = 8
sql_alchemy_max_overflow = 16
sql_alchemy_pool_use_lifo = True
sql_alchemy_engine_args = {
    "pool_pre_ping": True,
    "pool_recycle": 1800,
}

# Metrics
statsd_on = True
statsd_host = statsd-exporter
statsd_port = 9125
```

### Airflow Database Optimization


```sql
-- Postgres optimizations for Airflow
-- Run on metadata database

-- Index cleanup: drop unused indexes
DROP INDEX IF EXISTS idx_task_instance_dag_run;
DROP INDEX IF EXISTS idx_task_instance_dag;

-- Partial index for active task instances
CREATE INDEX CONCURRENTLY idx_ti_active ON task_instance
    (dag_id, task_id, execution_date)
    WHERE state IN ('queued', 'running', 'scheduled');

-- Optimize dag_run queries
CREATE INDEX CONCURRENTLY idx_dag_run_state ON dag_run
    (dag_id, state, execution_date DESC);

-- Vacuum regularly
VACUUM ANALYZE task_instance;
VACUUM ANALYZE dag_run;

-- Table partitioning (Airflow 2.5+)
ALTER TABLE task_instance PARTITION BY RANGE (start_date);
```

---

## Related


- [Databases](../../08-databases/) — Data storage and querying
- [Messaging](../../10-messaging/) — Event streaming (Kafka)
- [Cloud Platforms](../../05-cloud/) — Data warehousing (Redshift, BigQuery)
- [Backend](../../03-backend/) — Data service APIs
- [Distributed Systems](../../09-distributed-systems/) — Scale and consistency
