# MLOps: Machine Learning Operations


## Architecture Overview


```mermaid
graph TB
    A["Data"] --> B["Preprocessing"]
    B --> C["Feature Engineering"]
    C --> D["Training"]
    D --> E["Validation"]
    E -->|Failed| C
    E -->|Success| F["Deployment"]
    style F fill:#3fb950
```

## 1. ML Lifecycle


### 1.1 The Complete ML Lifecycle


```
Data Collection -> Data Validation -> Training -> Evaluation -> Deployment -> Monitoring -> Retrain
     |                |                 |           |             |            |           |
     v                v                 v           v             v            v           v
  Data Lake      Schema Checks      ML Framework  Metrics       A/B Test    Drift Det.  Feedback
  Feature Store  Quality Checks     Hyperparam    Validation    Canary      Alerts      Loop
```

```python
class MLLifecycle:
    def __init__(self):
        self.stages = {}

    def log_stage(self, name: str, status: str, artifacts: dict = None):
        self.stages[name] = {
            "status": status,
            "timestamp": __import__('time').time(),
            "artifacts": artifacts or {}
        }

    def get_pipeline_status(self) -> dict:
        return {
            stage: info["status"]
            for stage, info in self.stages.items()
        }

    def is_ready_for_deployment(self) -> bool:
        required = ["data_validation", "training", "evaluation"]
        return all(
            self.stages.get(s, {}).get("status") == "passed"
            for s in required
        )


# Pipeline implementation
def data_pipeline(raw_data_path: str) -> str:
    processed_path = raw_data_path.replace("raw", "processed")
    return processed_path

def training_pipeline(data_path: str, params: dict) -> str:
    model_path = f"models/model_v{params['version']}.pkl"
    return model_path

def evaluation_pipeline(model_path: str, test_data: str) -> dict:
    metrics = {"accuracy": 0.95, "f1": 0.93, "latency_ms": 45}
    return metrics

def deployment_pipeline(model_path: str, version: str) -> str:
    endpoint = f"https://api.example.com/v1/models/{version}"
    return endpoint
```

### 1.2 Data Pipeline


```python
class DataPipeline:
    def __init__(self):
        self.steps = []

    def add_step(self, name: str, fn: callable):
        self.steps.append({"name": name, "fn": fn})

    def run(self, data):
        for step in self.steps:
            print(f"Running: {step['name']}")
            data = step['fn'](data)
        return data


# Example: feature engineering pipeline
def validate_schema(df):
    required_columns = ['user_id', 'timestamp', 'features', 'label']
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df

def clean_outliers(df, threshold=3):
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
        df = df[z_scores < threshold]
    return df

def create_features(df):
    df['hour_of_day'] = pd.to_datetime(df['timestamp']).dt.hour
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
    df['rolling_avg_7d'] = df.groupby('user_id')['feature'].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )
    return df
```

## 2. Experiment Tracking


### 2.1 Custom Experiment Tracker


```python
class ExperimentTracker:
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.params = {}
        self.metrics = {}
        self.artifacts = []
        self.start_time = None
        self.end_time = None

    def log_params(self, params: dict):
        self.params.update(params)

    def log_metric(self, name: str, value: float, step: int = None):
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({"value": value, "step": step or len(self.metrics[name])})

    def log_artifact(self, path: str, description: str = ""):
        self.artifacts.append({"path": path, "description": description})

    def start_run(self):
        self.start_time = __import__('time').time()
        self.run_id = f"{self.experiment_name}_{int(self.start_time)}"
        return self.run_id

    def end_run(self):
        self.end_time = __import__('time').time()

    def get_summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "experiment": self.experiment_name,
            "params": self.params,
            "metrics": {k: [m["value"] for m in v] for k, v in self.metrics.items()},
            "duration": (self.end_time or __import__('time').time()) - self.start_time,
            "artifacts": self.artifacts
        }


# MLflow-style wrapper
class MLflowTracker:
    def __init__(self, tracking_uri: str = "./mlruns"):
        self.tracking_uri = tracking_uri
        self.active_run = None
        import os
        os.makedirs(tracking_uri, exist_ok=True)

    def start_run(self, experiment_name: str = "default"):
        import uuid
        run_id = str(uuid.uuid4())
        self.active_run = {
            "id": run_id,
            "experiment": experiment_name,
            "params": {},
            "metrics": {},
            "artifacts": []
        }
        return run_id

    def log_param(self, key: str, value):
        if self.active_run:
            self.active_run["params"][key] = value

    def log_metric(self, key: str, value: float):
        if self.active_run:
            if key not in self.active_run["metrics"]:
                self.active_run["metrics"][key] = []
            self.active_run["metrics"][key].append(value)

    def log_artifact(self, local_path: str):
        if self.active_run:
            import shutil
            artifact_path = f"{self.tracking_uri}/{self.active_run['id']}/artifacts"
            __import__('os').makedirs(artifact_path, exist_ok=True)
            shutil.copy(local_path, artifact_path)
            self.active_run["artifacts"].append(local_path)

    def end_run(self):
        import json
        if self.active_run:
            run_path = f"{self.tracking_uri}/{self.active_run['id']}"
            __import__('os').makedirs(run_path, exist_ok=True)
            with open(f"{run_path}/run.json", "w") as f:
                json.dump(self.active_run, f, indent=2)
            self.active_run = None
```

### 2.2 Hyperparameter Tracking


```python
class HyperparameterTracker:
    def __init__(self):
        self.trials = []

    def log_trial(self, params: dict, metrics: dict):
        self.trials.append({
            "params": params,
            "metrics": metrics,
            "trial_id": len(self.trials)
        })

    def best_trial(self, metric: str = "accuracy", mode: str = "max") -> dict:
        if mode == "max":
            return max(self.trials, key=lambda t: t["metrics"].get(metric, 0))
        return min(self.trials, key=lambda t: t["metrics"].get(metric, float('inf')))

    def get_param_importance(self) -> dict:
        importances = {}
        if len(self.trials) < 2:
            return {}
        for param in self.trials[0]["params"]:
            values = [t["params"][param] for t in self.trials]
            if len(set(values)) > 1:
                importances[param] = len(set(values)) / len(values)
        return importances


# Grid search with tracking
def grid_search(model_class, param_grid, X_train, y_train, X_val, y_val):
    tracker = HyperparameterTracker()
    from itertools import product
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    for combo in product(*values):
        params = dict(zip(keys, combo))
        model = model_class(**params)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        accuracy = np.mean(y_pred == y_val)
        tracker.log_trial(params, {"accuracy": accuracy})
    return tracker.best_trial("accuracy"), tracker
```

## 3. Model Registry


### 3.1 Model Versioning


```python
class ModelRegistry:
    def __init__(self, registry_path: str = "./model_registry"):
        self.registry_path = registry_path
        import os
        os.makedirs(registry_path, exist_ok=True)

    def register_model(self, model, name: str, version: str, metrics: dict, tags: dict = None):
        model_path = f"{self.registry_path}/{name}/{version}"
        import os, json, pickle
        os.makedirs(model_path, exist_ok=True)
        with open(f"{model_path}/model.pkl", "wb") as f:
            pickle.dump(model, f)
        metadata = {
            "name": name,
            "version": version,
            "metrics": metrics,
            "tags": tags or {},
            "stage": "none",
            "registered_at": __import__('time').time()
        }
        with open(f"{model_path}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        return model_path

    def promote_model(self, name: str, version: str, stage: str):
        metadata_path = f"{self.registry_path}/{name}/{version}/metadata.json"
        if __import__('os').exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            metadata["stage"] = stage
            metadata["promoted_at"] = __import__('time').time()
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

    def get_model(self, name: str, stage: str = "production"):
        import os, json, pickle
        models_path = f"{self.registry_path}/{name}"
        if not os.path.exists(models_path):
            return None
        versions = os.listdir(models_path)
        for version in sorted(versions, reverse=True):
            metadata_path = f"{models_path}/{version}/metadata.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                if metadata["stage"] == stage:
                    with open(f"{models_path}/{version}/model.pkl", "rb") as f:
                        return pickle.load(f)
        return None

    def list_models(self, stage: str = None) -> list:
        import os, json
        models = []
        if not os.path.exists(self.registry_path):
            return models
        for model_name in os.listdir(self.registry_path):
            model_path = f"{self.registry_path}/{model_name}"
            for version in os.listdir(model_path):
                metadata_path = f"{model_path}/{version}/metadata.json"
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    if stage is None or metadata.get("stage") == stage:
                        models.append(metadata)
        return models


# Staging workflow
class ModelStaging:
    STAGES = ["development", "staging", "production", "archived"]

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def stage_transition(self, name: str, version: str, from_stage: str, to_stage: str):
        if to_stage not in self.STAGES:
            raise ValueError(f"Invalid stage: {to_stage}")
        if self.STAGES.index(to_stage) < self.STAGES.index(from_stage):
            confirm = input(f"Downgrade {name}:{version} from {from_stage} to {to_stage}? (y/n): ")
            if confirm.lower() != 'y':
                return False
        self.registry.promote_model(name, version, to_stage)
        return True
```

### 3.2 Model Comparison


```python
class ModelComparator:
    def compare(self, models: dict, test_data, test_labels) -> dict:
        results = {}
        for name, model in models.items():
            y_pred = model.predict(test_data)
            results[name] = {
                "accuracy": np.mean(y_pred == test_labels),
                "f1": self.f1_score(test_labels, y_pred),
                "precision": self.precision_score(test_labels, y_pred),
                "recall": self.recall_score(test_labels, y_pred)
            }
        return results

    def f1_score(self, y_true, y_pred):
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    def precision_score(self, y_true, y_pred):
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        return tp / (tp + fp) if (tp + fp) > 0 else 0

    def recall_score(self, y_true, y_pred):
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        return tp / (tp + fn) if (tp + fn) > 0 else 0
```

## 4. Feature Store Architecture


### 4.1 Architecture Overview


```mermaid
graph TB
    subgraph "Data Sources"
        A["Kafka Streams"]
        B["OLTP DBs<br/>(Postgres, MySQL)"]
        C["Data Lake<br/>(S3 Parquet)"]
    end

    subgraph "Feature Pipeline"
        D["Stream Processor<br/>(Flink)"]
        E["Batch Processor<br/>(Spark)"]
        F["Feature<br/>Computation"]
    end

    subgraph "Feature Store"
        G["Offline Store<br/>(Parquet/Delta)"]
        H["Online Store<br/>(Redis/DynamoDB)"]
        I["Feature Registry<br/>(Catalog + Metadata)"]
    end

    subgraph "Consumers"
        J["Training Jobs"]
        K["Serving<br/>Inference"]
        L["Feature<br/>Discovery"]
    end

    A --> D
    B --> E
    C --> E
    D --> F
    E --> F
    F --> G
    F --> H
    F --> I
    G --> J
    H --> K
    I --> L
    J -->|Historical features| G
    K -->|Real-time features| H
```

### 4.2 Feature Store Components


```python
class FeatureStore:
    """Production feature store with offline + online serving."""

    def __init__(self, online_store: str = "redis", offline_store: str = "s3",
                 registry_path: str = "./feature_registry"):
        self.online = self._init_online(online_store)
        self.offline = self._init_offline(offline_store)
        self.registry = FeatureRegistry(registry_path)
        self.producers: dict[str, FeatureProducer] = {}

    def _init_online(self, store_type: str):
        stores = {
            "redis": RedisOnlineStore(),
            "dynamodb": DynamoDBOnlineStore(),
            "memory": InMemoryOnlineStore()
        }
        return stores.get(store_type, InMemoryOnlineStore())

    def _init_offline(self, store_type: str):
        stores = {
            "s3": S3OfflineStore(),
            "delta": DeltaOfflineStore(),
            "local": LocalOfflineStore()
        }
        return stores.get(store_type, LocalOfflineStore())

    def register_feature_view(self, name: str, entities: list[str],
                                features: list[dict], ttl: int = 3600):
        self.registry.register(name, {
            "entities": entities,
            "features": features,
            "ttl": ttl,
            "created_at": time.time()
        })

    def get_training_data(self, feature_view: str, entities: list[str],
                           start_date: str, end_date: str) -> pd.DataFrame:
        return self.offline.get_features(
            feature_view, entities, start_date, end_date
        )

    def get_online_features(self, feature_view: str, entity_keys: dict) -> dict:
        return self.online.get(feature_view, entity_keys)

    def materialize(self, feature_view: str, start_date: str, end_date: str):
        """Push offline features to online store."""
        df = self.offline.get_features(
            feature_view, [], start_date, end_date
        )
        for _, row in df.iterrows():
            self.online.set(feature_view, row.to_dict())


class FeatureRegistry:
    def __init__(self, path: str):
        self.path = path
        self.views: dict = {}
        self._load()

    def register(self, name: str, metadata: dict):
        self.views[name] = metadata
        self._save()

    def get(self, name: str) -> dict:
        return self.views.get(name)

    def list_views(self) -> list[dict]:
        return [{"name": k, **v} for k, v in self.views.items()]

    def search(self, query: str) -> list[dict]:
        results = []
        for name, meta in self.views.items():
            if query.lower() in name.lower():
                results.append({"name": name, **meta})
            else:
                for f in meta.get("features", []):
                    if query.lower() in f.get("name", "").lower():
                        results.append({"name": name, **meta})
                        break
        return results

    def _save(self):
        os.makedirs(self.path, exist_ok=True)
        with open(f"{self.path}/registry.json", "w") as f:
            json.dump(self.views, f, indent=2)

    def _load(self):
        path = f"{self.path}/registry.json"
        if os.path.exists(path):
            with open(path) as f:
                self.views = json.load(f)


# Point-in-time correct feature retrieval
class PointInTimeJoin:
    """Ensures training data doesn't leak future information."""

    def __init__(self, feature_store: FeatureStore):
        self.store = feature_store

    def create_training_set(self, labels: pd.DataFrame, feature_view: str,
                              entity_col: str, timestamp_col: str) -> pd.DataFrame:
        """For each label row, fetch features as of that timestamp."""
        training_rows = []
        for _, row in labels.iterrows():
            entity_id = row[entity_col]
            event_time = row[timestamp_col]
            features = self.store.offline.get_features_as_of(
                feature_view, entity_id, event_time
            )
            training_rows.append({**row.to_dict(), **features})
        return pd.DataFrame(training_rows)
```

### 4.3 Feast-Style Feature Definitions


```python
# Feast-inspired feature definition pattern
class FeatureView:
    def __init__(self, name: str, entities: list[str], source: str,
                 ttl: timedelta = timedelta(days=1)):
        self.name = name
        self.entities = entities
        self.source = source
        self.ttl = ttl
        self.features: list[Feature] = []

    def add_feature(self, name: str, dtype: str, description: str = ""):
        self.features.append(Feature(name, dtype, description))
        return self

    def to_proto(self) -> dict:
        return {
            "spec": {
                "name": self.name,
                "entities": self.entities,
                "features": [f.to_dict() for f in self.features],
                "ttl": str(self.ttl),
                "source": self.source
            }
        }


@dataclass
class Feature:
    name: str
    dtype: str
    description: str

    def to_dict(self):
        return {"name": self.name, "valueType": self.dtype.upper(),
                "description": self.description}


class Entity:
    def __init__(self, name: str, join_key: str, description: str = ""):
        self.name = name
        self.join_key = join_key
        self.description = description


# Example: User features for recommendation system
user_entity = Entity("user", "user_id", "User identifier")

user_features = FeatureView("user_features", entities=["user"], source="user_events") \
    .add_feature("avg_session_duration", "float", "Average session time in seconds") \
    .add_feature("purchase_count_7d", "int32", "Purchases in last 7 days") \
    .add_feature("category_diversity", "float", "Unique categories / total interactions") \
    .add_feature("recency_hours", "float", "Hours since last activity") \
    .add_feature("ltv_segment", "string", "Customer lifetime value segment")

# Online serving
# features = store.get_online_features(
#     feature_view="user_features",
#     entity_keys={"user": "user_123"}
# )
```

### 4.4 Online and Offline Feature Serving


```python
class FeatureStore:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.online_store = {}  # Redis-like dict
        self.offline_store = {}  # Parquet-like dict

    def register_feature(self, name: str, dtype: str, description: str, source: str):
        self.offline_store[name] = {
            "dtype": dtype,
            "description": description,
            "source": source,
            "created_at": __import__('time').time()
        }

    def ingest_batch(self, feature_name: str, df: 'pd.DataFrame'):
        for _, row in df.iterrows():
            entity_key = f"{feature_name}:{row['entity_id']}"
            self.online_store[entity_key] = row['value']

    def get_online_features(self, entity_id: str, features: list) -> dict:
        result = {}
        for feature in features:
            key = f"{feature}:{entity_id}"
            result[feature] = self.online_store.get(key)
        return result

    def get_training_data(self, feature_names: list, entity_ids: list) -> 'pd.DataFrame':
        import pandas as pd
        rows = []
        for entity_id in entity_ids:
            row = {"entity_id": entity_id}
            for feature in feature_names:
                key = f"{feature}:{entity_id}"
                row[feature] = self.online_store.get(key)
            rows.append(row)
        return pd.DataFrame(rows)


# Feast-like feature definition
class FeatureDefinition:
    def __init__(self, name: str, dtype: str, source: str, ttl_seconds: int = 3600):
        self.name = name
        self.dtype = dtype
        self.source = source
        self.ttl = ttl_seconds
        self.entities = []

    def add_entity(self, entity_name: str):
        self.entities.append(entity_name)

    def to_dict(self):
        return {
            "name": self.name, "dtype": self.dtype,
            "source": self.source, "entities": self.entities,
            "ttl": self.ttl
        }


# Feature engineering pipeline
class FeatureEngineering:
    def __init__(self, feature_store: FeatureStore):
        self.feature_store = feature_store

    def create_user_features(self, user_data: 'pd.DataFrame') -> 'pd.DataFrame':
        features = user_data.copy()
        features['recency_days'] = (pd.Timestamp.now() - features['last_active']).dt.days
        features['frequency_per_week'] = features['login_count'] / features['account_age_days'] * 7
        features['avg_session_duration'] = features['total_session_time'] / features['session_count']
        features['categories_diversity'] = features['unique_categories'] / features['total_interactions']
        return features

    def create_item_features(self, item_data: 'pd.DataFrame') -> 'pd.DataFrame':
        features = item_data.copy()
        features['popularity_score'] = features['views'] / features['age_days']
        features['engagement_rate'] = features['interactions'] / features['views']
        features['freshness'] = 1 / (features['age_days'] + 1)
        return features
```

## 5. Pipeline Orchestration


### 5.1 Orchestrator Comparison


| Feature | Airflow | Kubeflow | MLflow | Prefect | Dagster |
|---------|---------|----------|--------|---------|---------|
| ML-native | No | Yes | Yes | No | Yes |
| DAG type | Static | Static | Static | Dynamic | Asset-based |
| GPU support | Manual | Native (K8s) | Native (K8s) | Manual | Manual |
| Experiment tracking | No | Yes (MLMD) | Yes | No | No |
| Model registry | No | Yes | Yes | No | No |
| Pipeline reuse | DAGs | Components | Projects | Flows | Assets |
| Best for | General ETL | Full MLOps | ML experiments | Data pipelines | Data platforms |

### 5.2 Kubeflow Pipeline


```python
# Kubeflow Pipelines SDK v2
from kfp import dsl, compiler

@dsl.component
def validate_data(data_path: str) -> str:
    import pandas as pd
    df = pd.read_parquet(data_path)
    assert df.shape[0] > 0, "Empty dataset"
    assert not df.isnull().any().any(), "Missing values found"
    return data_path

@dsl.component
def train_model(data_path: str, hyperparams: dict) -> str:
    import mlflow
    with mlflow.start_run():
        # Training logic
        accuracy = 0.95
        mlflow.log_params(hyperparams)
        mlflow.log_metric("accuracy", accuracy)
    return f"model_v1"

@dsl.component
def evaluate_model(model_uri: str, test_data: str) -> float:
    accuracy = 0.95
    if accuracy < 0.90:
        raise ValueError("Accuracy below threshold")
    return accuracy

@dsl.component
def deploy_model(model_uri: str, accuracy: float):
    print(f"Deploying {model_uri} with accuracy {accuracy}")

@dsl.pipeline(name="ml-training-pipeline")
def ml_pipeline(data_path: str = "s3://data/training"):
    validate_task = validate_data(data_path=data_path)
    train_task = train_model(
        data_path=validate_task.output,
        hyperparams={"lr": 0.01, "epochs": 10}
    )
    evaluate_task = evaluate_model(
        model_uri=train_task.output,
        test_data=data_path
    )
    evaluate_task.after(train_task)
    deploy_task = deploy_model(
        model_uri=train_task.output,
        accuracy=evaluate_task.output
    )
    deploy_task.after(evaluate_task)

# Compile
compiler.Compiler().compile(ml_pipeline, "pipeline.yaml")
```

### 5.3 MLflow Pipelines


```python
# MLflow as orchestration + tracking
import mlflow
from mlflow.models import infer_signature

class MLflowPipeline:
    def __init__(self, experiment_name: str):
        self.experiment = experiment_name
        mlflow.set_experiment(experiment_name)

    def run_training(self, data_path: str, params: dict) -> str:
        with mlflow.start_run() as run:
            mlflow.log_params(params)
            # Training
            model = self._train(data_path, params)
            # Log model
            signature = infer_signature(
                pd.DataFrame({"feature": [1, 2, 3]}),
                pd.Series([0, 1, 0])
            )
            mlflow.sklearn.log_model(model, "model", signature=signature)
            # Log metrics
            metrics = self._evaluate(model, data_path)
            mlflow.log_metrics(metrics)
            # Register
            mlflow.register_model(
                f"runs:/{run.info.run_id}/model",
                "recommendation_model"
            )
        return run.info.run_id

    def _train(self, data_path: str, params: dict):
        return {"model_type": "xgboost", "params": params}

    def _evaluate(self, model, data_path: str) -> dict:
        return {"accuracy": 0.94, "f1": 0.93, "auc": 0.97}

    def promote_to_staging(self, run_id: str):
        client = mlflow.MlflowClient()
        client.transition_model_version_stage(
            name="recommendation_model",
            version=run_id,
            stage="Staging"
        )

    def promote_to_production(self, run_id: str):
        client = mlflow.MlflowClient()
        client.transition_model_version_stage(
            name="recommendation_model",
            version=run_id,
            stage="Production"
        )
```

### 5.4 Airflow for ML


```python
# Airflow DAG for ML pipeline
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "ml-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=4)
}

with DAG(
    dag_id="ml_retraining_pipeline",
    default_args=default_args,
    schedule_interval="0 3 * * 0",  # Weekly at 3am Sunday
    catchup=False,
    tags=["ml", "training"],
) as dag:

    def validate_data(**context):
        import pandas as pd
        df = pd.read_parquet("s3://data/training/latest")
        assert len(df) > 10000, "Dataset too small"
        assert df["label"].nunique() >= 2, "Need at least 2 classes"
        context["ti"].xcom_push(key="data_path", value="s3://data/training/latest")

    def train_model(**context):
        data_path = context["ti"].xcom_pull(key="data_path")
        import mlflow
        with mlflow.start_run():
            mlflow.log_param("data_path", data_path)
            # Training logic
            accuracy = 0.95
            mlflow.log_metric("accuracy", accuracy)
        context["ti"].xcom_push(key="run_id", value=mlflow.active_run().info.run_id)

    def evaluate_model(**context):
        run_id = context["ti"].xcom_pull(key="run_id")
        accuracy = 0.95
        if accuracy < 0.85:
            raise ValueError("Model quality below threshold")
        context["ti"].xcom_push(key="accuracy", value=accuracy)

    def deploy(**context):
        accuracy = context["ti"].xcom_pull(key="accuracy")
        print(f"Deploying with accuracy: {accuracy}")

    validate = PythonOperator(task_id="validate_data", python_callable=validate_data)
    train = PythonOperator(task_id="train_model", python_callable=train_model)
    evaluate = PythonOperator(task_id="evaluate_model", python_callable=evaluate_model)
    deploy = PythonOperator(task_id="deploy_model", python_callable=deploy)

    validate >> train >> evaluate >> deploy
```

## 6. Model Serving


### 6.1 Serving Infrastructure


```python
class ModelServer:
    def __init__(self, model_registry: ModelRegistry):
        self.registry = model_registry
        self.loaded_models = {}
        self.config = {
            "max_batch_size": 32,
            "max_latency_ms": 100,
            "timeout_seconds": 30
        }

    def load_model(self, name: str, version: str = None):
        if version:
            model = self.registry.get_model(name, "production")
        else:
            model = self.registry.get_model(name, "production")
        if model:
            self.loaded_models[f"{name}:{version or 'latest'}"] = model
            return True
        return False

    def predict(self, name: str, data):
        model_key = f"{name}:latest"
        if model_key not in self.loaded_models:
            self.load_model(name)
        model = self.loaded_models.get(model_key)
        if model:
            return model.predict(data)
        raise ValueError(f"Model {name} not loaded")


class BatchInference:
    def __init__(self, model_server: ModelServer):
        self.server = model_server

    def predict_batch(self, model_name: str, data_chunks: list) -> list:
        results = []
        for chunk in data_chunks:
            batch_results = self.server.predict(model_name, chunk)
            results.extend(batch_results)
        return results


class ModelEnsemble:
    def __init__(self, models: list, weights: list = None):
        self.models = models
        self.weights = weights if weights else [1/len(models)] * len(models)

    def predict(self, data):
        predictions = []
        for model in self.models:
            pred = model.predict(data)
            if hasattr(pred, 'shape') and len(pred.shape) > 1 and pred.shape[1] > 1:
                predictions.append(pred)
            else:
                predictions.append(pred)
        return np.average(predictions, axis=0, weights=self.weights)
```

### 6.2 Serving Configuration


```python
# Triton-like configuration
class InferenceConfig:
    def __init__(self):
        self.config = {
            "backend": "tensorrt",
            "max_batch_size": 32,
            "instance_group": [{"count": 2, "kind": "KIND_GPU"}],
            "dynamic_batching": {"preferred_batch_size": [8, 16, 32]}
        }

    def to_dict(self) -> dict:
        return self.config


# vLLM-like continuous batching
class ContinuousBatchingServer:
    def __init__(self, model, max_batch_size=64):
        self.model = model
        self.max_batch_size = max_batch_size
        self.running_requests = []
        self.waiting_queue = []

    def enqueue(self, request):
        self.waiting_queue.append(request)
        self.try_batch()

    def try_batch(self):
        while len(self.waiting_queue) > 0 or len(self.running_requests) > 0:
            available = self.max_batch_size - len(self.running_requests)
            if available > 0 and self.waiting_queue:
                new_batch = self.waiting_queue[:available]
                self.waiting_queue = self.waiting_queue[available:]
                self.running_requests.extend(new_batch)
            self.step()

    def step(self):
        batch = self.running_requests[:self.max_batch_size]
        if batch:
            texts = [r["prompt"] for r in batch]
            outputs = self.model.generate(texts)
            for req, output in zip(batch, outputs):
                req["output"] = output
            self.running_requests = []

    def get_stats(self) -> dict:
        return {
            "running": len(self.running_requests),
            "waiting": len(self.waiting_queue),
            "throughput": 0  # Calculate dynamically
        }
```

## 7. A/B Testing and Deployment Strategies


### 7.1 Deployment Strategies


```python
class DeploymentStrategy:
    def __init__(self):
        self.strategies = {}

    def register_strategy(self, name: str, config: dict):
        self.strategies[name] = config

    def deploy(self, strategy: str, model_name: str, version: str):
        if strategy == "rolling":
            return self.rolling_update(model_name, version)
        elif strategy == "canary":
            return self.canary_deploy(model_name, version, traffic_percent=5)
        elif strategy == "blue_green":
            return self.blue_green_deploy(model_name, version)
        elif strategy == "shadow":
            return self.shadow_deploy(model_name, version)
        raise ValueError(f"Unknown strategy: {strategy}")

    def rolling_update(self, model_name: str, version: str):
        return {
            "strategy": "rolling",
            "model": model_name,
            "version": version,
            "instances_per_batch": 2,
            "health_check_interval_s": 30,
            "rollback_on_failure": True
        }

    def canary_deploy(self, model_name: str, version: str, traffic_percent: float = 5):
        return {
            "strategy": "canary",
            "model": model_name,
            "version": version,
            "initial_traffic_percent": traffic_percent,
            "increment_per_check": 5,
            "check_interval_m": 10,
            "metrics_watch": ["error_rate", "latency_p99", "accuracy"],
            "auto_rollback_threshold": 0.05
        }

    def blue_green_deploy(self, model_name: str, version: str):
        return {
            "strategy": "blue_green",
            "model": model_name,
            "version": version,
            "blue": "current",
            "green": "new",
            "switch_traffic": "immediate",
            "keep_blue_running_minutes": 30
        }

    def shadow_deploy(self, model_name: str, version: str):
        return {
            "strategy": "shadow",
            "model": model_name,
            "version": version,
            "shadow_traffic_percent": 100,
            "compare_metrics": ["accuracy", "confidence", "latency"],
            "promotion_condition": "accuracy >= baseline * 0.95"
        }


class A_B_TestManager:
    def __init__(self):
        self.experiments = {}

    def start_experiment(self, name: str, control_model: str, treatment_model: str, traffic_split: float = 0.5):
        self.experiments[name] = {
            "control": control_model,
            "treatment": treatment_model,
            "split": traffic_split,
            "results": {"control": [], "treatment": []},
            "start_time": __import__('time').time()
        }

    def assign_variant(self, experiment_name: str, user_id: str) -> str:
        experiment = self.experiments[experiment_name]
        if hash(user_id) % 100 < experiment["split"] * 100:
            return "control"
        return "treatment"

    def record_result(self, experiment_name: str, variant: str, metric: str, value: float):
        self.experiments[experiment_name]["results"][variant].append({
            "metric": metric,
            "value": value,
            "timestamp": __import__('time').time()
        })

    def get_significance(self, experiment_name: str, metric: str) -> dict:
        from scipy import stats
        experiment = self.experiments[experiment_name]
        control_vals = [r["value"] for r in experiment["results"]["control"] if r["metric"] == metric]
        treatment_vals = [r["value"] for r in experiment["results"]["treatment"] if r["metric"] == metric]
        if len(control_vals) < 2 or len(treatment_vals) < 2:
            return {"significant": False, "reason": "Insufficient data"}
        t_stat, p_value = stats.ttest_ind(control_vals, treatment_vals)
        return {
            "control_mean": np.mean(control_vals),
            "treatment_mean": np.mean(treatment_vals),
            "lift": (np.mean(treatment_vals) - np.mean(control_vals)) / np.mean(control_vals),
            "p_value": p_value,
            "significant": p_value < 0.05
        }
```

## 8. Model Monitoring


### 8.1 Data Drift Detection


```python
class DriftDetector:
    def __init__(self, baseline_data, threshold: float = 0.05):
        self.baseline = baseline_data
        self.threshold = threshold

    def detect_data_drift(self, new_data, method: str = "ks_test"):
        if method == "ks_test":
            from scipy import stats
            drifted_features = []
            for col in self.baseline.columns:
                if col in new_data.columns:
                    statistic, p_value = stats.ks_2samp(self.baseline[col], new_data[col])
                    if p_value < self.threshold:
                        drifted_features.append({"feature": col, "p_value": p_value, "statistic": statistic})
            return {
                "drift_detected": len(drifted_features) > 0,
                "drifted_features": drifted_features,
                "drift_ratio": len(drifted_features) / len(self.baseline.columns)
            }
        return None

    def detect_prediction_drift(self, baseline_preds, new_preds, method: str = "psi"):
        if method == "psi":
            psi = self.calculate_psi(baseline_preds, new_preds)
            return {"psi": psi, "drift_detected": psi > self.threshold}
        return None

    def calculate_psi(self, expected, actual, bins: int = 10):
        expected_hist, _ = np.histogram(expected, bins=bins, range=(0, 1))
        actual_hist, _ = np.histogram(actual, bins=bins, range=(0, 1))
        expected_pct = expected_hist / len(expected)
        actual_pct = actual_hist / len(actual)
        psi = 0
        for e, a in zip(expected_pct, actual_pct):
            if e > 0 and a > 0:
                psi += (a - e) * np.log(a / e)
        return psi


class ConceptDriftDetector:
    def __init__(self, window_size: int = 1000, warning_level: float = 0.05):
        self.window_size = window_size
        self.warning_level = warning_level
        self.accuracy_window = []

    def update(self, accuracy: float):
        self.accuracy_window.append(accuracy)
        if len(self.accuracy_window) > self.window_size:
            self.accuracy_window.pop(0)

    def detect_drift(self) -> dict:
        if len(self.accuracy_window) < 100:
            return {"drift_detected": False, "reason": "Insufficient data"}
        recent = self.accuracy_window[-100:]
        old = self.accuracy_window[:100]
        from scipy import stats
        _, p_value = stats.ttest_ind(old, recent)
        return {
            "drift_detected": p_value < self.warning_level,
            "old_accuracy": np.mean(old),
            "recent_accuracy": np.mean(recent),
            "decline": np.mean(old) - np.mean(recent),
            "p_value": p_value
        }
```

### 8.2 Monitoring Dashboard


```python
class MonitoringDashboard:
    def __init__(self):
        self.alerts = []
        self.metrics_history = {}

    def record_metric(self, name: str, value: float, tags: dict = None):
        if name not in self.metrics_history:
            self.metrics_history[name] = []
        self.metrics_history[name].append({
            "value": value,
            "tags": tags or {},
            "timestamp": __import__('time').time()
        })
        self.check_alerts(name, value)

    def add_alert_rule(self, name: str, metric: str, condition: str, threshold: float):
        self.alerts.append({
            "name": name,
            "metric": metric,
            "condition": condition,
            "threshold": threshold
        })

    def check_alerts(self, metric: str, value: float):
        for alert in self.alerts:
            if alert["metric"] == metric:
                if alert["condition"] == ">" and value > alert["threshold"]:
                    self.trigger_alert(alert["name"], value)
                elif alert["condition"] == "<" and value < alert["threshold"]:
                    self.trigger_alert(alert["name"], value)

    def trigger_alert(self, alert_name: str, value: float):
        print(f"ALERT: {alert_name} triggered with value {value:.4f}")

    def get_recent_metrics(self, name: str, minutes: int = 60) -> list:
        cutoff = __import__('time').time() - minutes * 60
        return [m for m in self.metrics_history.get(name, []) if m["timestamp"] > cutoff]
```

## 9. LLM Observability


### 9.1 Token Usage and Cost Tracking


```python
class LLMObservability:
    def __init__(self):
        self.usage_log = []

    def log_request(self, model: str, prompt_tokens: int, completion_tokens: int, latency_ms: float):
        pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03}
        }
        cost_per_1k = pricing.get(model, {"prompt": 0.01, "completion": 0.02})
        cost = (prompt_tokens / 1000 * cost_per_1k["prompt"] +
                completion_tokens / 1000 * cost_per_1k["completion"])
        self.usage_log.append({
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": cost,
            "latency_ms": latency_ms,
            "timestamp": __import__('time').time()
        })
        return cost

    def get_daily_summary(self) -> dict:
        import datetime
        today = datetime.date.today()
        today_logs = [l for l in self.usage_log
                     if datetime.datetime.fromtimestamp(l["timestamp"]).date() == today]
        total_cost = sum(l["cost"] for l in today_logs)
        total_tokens = sum(l["total_tokens"] for l in today_logs)
        avg_latency = np.mean([l["latency_ms"] for l in today_logs]) if today_logs else 0
        return {
            "date": str(today),
            "total_requests": len(today_logs),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_latency_ms": avg_latency,
            "models_used": list(set(l["model"] for l in today_logs))
        }

    def get_cost_breakdown(self, days: int = 30) -> dict:
        cutoff = __import__('time').time() - days * 86400
        recent = [l for l in self.usage_log if l["timestamp"] > cutoff]
        breakdown = {}
        for log in recent:
            if log["model"] not in breakdown:
                breakdown[log["model"]] = {"requests": 0, "tokens": 0, "cost": 0}
            breakdown[log["model"]]["requests"] += 1
            breakdown[log["model"]]["tokens"] += log["total_tokens"]
            breakdown[log["model"]]["cost"] += log["cost"]
        return breakdown
```

### 9.2 Safety Monitoring


```python
class SafetyMonitor:
    def __init__(self):
        self.flagged_outputs = []
        self.categories = {
            "hate": ["hate", "discrimination", "violence"],
            "harmful": ["harm", "danger", "weapon"],
            "pii": ["email", "ssn", "credit card", "phone"]
        }

    def check_output(self, text: str, metadata: dict = None) -> dict:
        flags = []
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    flags.append({"category": category, "keyword": keyword, "position": text.lower().index(keyword.lower())})
        if flags:
            self.flagged_outputs.append({
                "text": text[:200],
                "flags": flags,
                "metadata": metadata or {},
                "timestamp": __import__('time').time()
            })
        return {"safe": len(flags) == 0, "flags": flags}

    def get_safety_metrics(self) -> dict:
        total = len(self.flagged_outputs) + 1  # Avoid division by zero
        return {
            "total_flagged": len(self.flagged_outputs),
            "categories": {c: sum(1 for f in self.flagged_outputs for fl in f["flags"] if fl["category"] == c) for c in self.categories},
            "flag_rate": len(self.flagged_outputs) / total
        }


class PIIRedactor:
    def __init__(self):
        import re
        self.patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b')
        }

    def redact(self, text: str, replacement: str = "[REDACTED]") -> str:
        for name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                text = pattern.sub(replacement, text)
        return text
```

### 9.3 Quality Monitoring


```python
class QualityMonitor:
    def __init__(self):
        self.feedback_log = []
        self.metrics = {"bleu": [], "rouge": [], "hallucination": []}

    def log_feedback(self, prompt: str, response: str, rating: int, metadata: dict = None):
        self.feedback_log.append({
            "prompt": prompt,
            "response": response,
            "rating": rating,
            "metadata": metadata or {},
            "timestamp": __import__('time').time()
        })

    def compute_bleu(self, reference: str, candidate: str) -> float:
        ref_tokens = reference.split()
        cand_tokens = candidate.split()
        matches = sum(1 for t in cand_tokens if t in ref_tokens)
        precision = matches / len(cand_tokens) if cand_tokens else 0
        brevity_penalty = min(1, len(cand_tokens) / len(ref_tokens)) if ref_tokens else 1
        return brevity_penalty * precision

    def compute_rouge(self, reference: str, candidate: str) -> dict:
        ref_ngrams = set(zip(reference.split(), reference.split()[1:]))
        cand_ngrams = set(zip(candidate.split(), candidate.split()[1:]))
        overlap = ref_ngrams & cand_ngrams
        precision = len(overlap) / len(cand_ngrams) if cand_ngrams else 0
        recall = len(overlap) / len(ref_ngrams) if ref_ngrams else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        return {"precision": precision, "recall": recall, "f1": f1}

    def get_quality_report(self) -> dict:
        ratings = [f["rating"] for f in self.feedback_log] if self.feedback_log else [0]
        return {
            "avg_rating": np.mean(ratings),
            "total_feedback": len(self.feedback_log),
            "rating_distribution": {
                "positive": sum(1 for r in ratings if r >= 4),
                "neutral": sum(1 for r in ratings if r == 3),
                "negative": sum(1 for r in ratings if r <= 2)
            }
        }
```

## 10. Data Versioning


### 10.1 DVC (Data Version Control)


```python
# DVC-inspired data versioning
class DVCDataVersioning:
    def __init__(self, storage_path: str = "s3://dvc-store"):
        self.storage_path = storage_path
        self.cache_dir = ".dvc/cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def track(self, file_path: str) -> dict:
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5_hash.update(chunk)
        hash_value = md5_hash.hexdigest()

        # Copy to cache
        cache_path = f"{self.cache_dir}/{hash_value[:2]}/{hash_value[2:]}"
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        shutil.copy2(file_path, cache_path)

        return {"md5": hash_value, "size": os.path.getsize(file_path), "path": file_path}

    def push(self, file_path: str):
        entry = self.track(file_path)
        cache_file = f"{self.cache_dir}/{entry['md5'][:2]}/{entry['md5'][2:]}"
        remote_path = f"{self.storage_path}/{entry['md5']}"
        print(f"Pushing {cache_file} -> {remote_path}")
        return entry

    def pull(self, md5_hash: str, output_path: str):
        remote_path = f"{self.storage_path}/{md5_hash}"
        print(f"Pulling {remote_path} -> {output_path}")

    def get_pipeline_stage(self, name: str, cmd: str, deps: list,
                            outs: list, params: dict = None) -> str:
        dvc_content = {
            "stages": {
                name: {
                    "cmd": cmd,
                    "deps": deps,
                    "outs": outs,
                    "params": params or {}
                }
            }
        }
        return yaml.dump(dvc_content, default_flow_style=False)

    def reproduce(self, pipeline_file: str = "dvc.yaml"):
        with open(pipeline_file) as f:
            pipeline = yaml.safe_load(f)
        for stage_name, stage_config in pipeline.get("stages", {}).items():
            print(f"Reproducing stage: {stage_name}")
            deps_updated = all(
                self._is_changed(dep) for dep in stage_config.get("deps", [])
            )
            if deps_updated:
                subprocess.run(stage_config["cmd"], shell=True)

    def _is_changed(self, dep: str) -> bool:
        return True  # Simplified


# DVC pipeline YAML example
dvc_pipeline = """
stages:
  download:
    cmd: python scripts/download.py --output data/raw
    deps:
      - scripts/download.py
    outs:
      - data/raw
  preprocess:
    cmd: python scripts/preprocess.py --input data/raw --output data/processed
    deps:
      - scripts/preprocess.py
      - data/raw
    outs:
      - data/processed
    params:
      - preprocess.min_tokens
      - preprocess.max_length
  train:
    cmd: python scripts/train.py --data data/processed --output models/
    deps:
      - scripts/train.py
      - data/processed
    outs:
      - models/model.pkl
    params:
      - train.learning_rate
      - train.epochs
  evaluate:
    cmd: python scripts/evaluate.py --model models/model.pkl --data data/processed
    deps:
      - scripts/evaluate.py
      - models/model.pkl
      - data/processed
    metrics:
      - metrics/eval.json:
          cache: false
"""
```

### 10.2 LakeFS (Git for Data)


```python
class LakeFSClient:
    """LakeFS brings Git-like semantics to data lakes."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str):
        self.endpoint = endpoint
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(f'{access_key}:{secret_key}'.encode()).decode()}"
        }

    def create_branch(self, repository: str, name: str, source: str = "main"):
        return {"repository": repository, "branch": name, "source": source}

    def commit(self, repository: str, branch: str, message: str,
                metadata: dict = None) -> dict:
        return {
            "repository": repository,
            "branch": branch,
            "commit_message": message,
            "metadata": metadata or {},
            "committer": "ml-pipeline",
            "timestamp": time.time()
        }

    def diff(self, repository: str, branch_a: str, branch_b: str) -> list:
        """Compare two branches to see data changes."""
        return [
            {"type": "added", "path": "data/sales_2024.parquet", "size": "2.3GB"},
            {"type": "removed", "path": "data/sales_2023_old.parquet", "size": "1.1GB"},
            {"type": "changed", "path": "data/user_features.parquet", "size": "500MB"}
        ]

    def merge(self, repository: str, source_branch: str,
              destination_branch: str) -> dict:
        """Merge data changes from one branch to another."""
        conflicts = self._check_conflicts(repository, source_branch, destination_branch)
        if conflicts:
            return {"status": "conflict", "conflicts": conflicts}
        return {"status": "merged", "source": source_branch, "destination": destination_branch}

    def _check_conflicts(self, repo, src, dst):
        return []

    def create_tag(self, repository: str, name: str,
                   commit_id: str) -> dict:
        return {
            "repository": repository,
            "tag": name,
            "commit_id": commit_id,
            "created_at": time.time()
        }

    def list_commits(self, repository: str, branch: str, limit: int = 10) -> list:
        return [
            {"id": "abc123", "message": "Update features with new data",
             "committer": "ml-pipeline", "timestamp": time.time() - 3600},
            {"id": "def456", "message": "Initial data import",
             "committer": "data-team", "timestamp": time.time() - 86400},
        ][:limit]


# Data management workflow with LakeFS
class DataBranchWorkflow:
    def __init__(self, lakefs: LakeFSClient, repo: str):
        self.lakefs = lakefs
        self.repo = repo

    def experiment_branch(self, experiment_name: str) -> str:
        branch = f"experiment/{experiment_name}"
        self.lakefs.create_branch(self.repo, branch, "main")
        return branch

    def promote_after_validation(self, branch: str, validation_fn) -> dict:
        # Run validation on branch data
        validation_passed = validation_fn()
        if not validation_passed:
            return {"status": "failed", "reason": "Data validation failed"}

        # Merge to main
        result = self.lakefs.merge(self.repo, branch, "main")
        if result["status"] == "merged":
            # Create tag
            commits = self.lakefs.list_commits(self.repo, "main", 1)
            self.lakefs.create_tag(self.repo, f"release/{int(time.time())}", commits[0]["id"])
        return result
```

## 11. Retraining Strategies


### 11.1 Retraining Triggers


```python
class RetrainingStrategy:
    def __init__(self, model_name: str, model_registry: ModelRegistry):
        self.model_name = model_name
        self.registry = model_registry
        self.retraining_history = []

    def schedule_based(self, interval_days: int = 7) -> dict:
        """Time-based retraining (weekly/monthly)."""
        return {
            "strategy": "schedule",
            "interval_days": interval_days,
            "description": f"Retrain every {interval_days} days",
            "trigger": f"cron:{self._to_cron(interval_days)}"
        }

    def performance_based(self, metric: str = "accuracy",
                           threshold: float = 0.05, window: int = 1000) -> dict:
        """Retrain when model performance degrades."""
        return {
            "strategy": "performance_drift",
            "metric": metric,
            "threshold": threshold,
            "window_size": window,
            "description": f"Retrain when {metric} drops by >{threshold*100}% "
                           f"over last {window} predictions",
            "trigger": "continuous_monitoring"
        }

    def data_drift_based(self, drift_threshold: float = 0.25) -> dict:
        """Retrain when data distribution shifts."""
        return {
            "strategy": "data_drift",
            "drift_threshold": drift_threshold,
            "metric": "psi",
            "description": f"Retrain when PSI > {drift_threshold}",
            "trigger": "drift_detection_alert"
        }

    def volume_based(self, min_new_samples: int = 10000) -> dict:
        """Retrain after collecting enough new data."""
        return {
            "strategy": "volume",
            "min_new_samples": min_new_samples,
            "description": f"Retrain after {min_new_samples} new labeled samples",
            "trigger": "data_accumulation"
        }

    def _to_cron(self, days: int) -> str:
        if days == 7:
            return "0 3 * * 0"  # Sunday 3am
        elif days == 30:
            return "0 4 1 * *"  # 1st of month
        return f"0 3 */{days} * *"

    def select_strategy(self, model_stage: str, data_velocity: str) -> list:
        """Recommend retraining strategy based on model and data characteristics."""
        strategies = []
        if model_stage == "production":
            strategies.append(self.performance_based())
            strategies.append(self.data_drift_based())
        if data_velocity == "high":
            strategies.append(self.volume_based(min_new_samples=50000))
        else:
            strategies.append(self.schedule_based(30))
        return strategies


class RetrainingPipeline:
    def __init__(self, feature_store, training_fn, registry):
        self.feature_store = feature_store
        self.training_fn = training_fn
        self.registry = registry

    def run_retraining(self, model_name: str, strategy: dict) -> dict:
        """Execute retraining with the chosen strategy."""
        print(f"Starting retraining for {model_name} using {strategy['strategy']}")

        # 1. Get fresh training data
        train_data = self.feature_store.get_training_data(
            feature_view=model_name,
            entities=[],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        # 2. Train new model
        new_model, metrics = self.training_fn(train_data)

        # 3. Compare with current production model
        current_model = self.registry.get_model(model_name, "production")
        if current_model:
            improvement = self._compare_models(new_model, current_model, train_data)
        else:
            improvement = {"improvement_percent": 100, "should_deploy": True}

        # 4. Deploy if better
        if improvement["should_deploy"]:
            version = f"v{int(time.time())}"
            self.registry.register_model(new_model, model_name, version, metrics)
            self.registry.promote_model(model_name, version, "staging")

        return {
            "model": model_name,
            "strategy": strategy["strategy"],
            "metrics": metrics,
            "improvement": improvement,
            "new_version": improvement.get("version")
        }

    def _compare_models(self, new_model, current_model, data) -> dict:
        current_metrics = self._eval(current_model, data)
        new_metrics = self._eval(new_model, data)
        improvement = (new_metrics["accuracy"] - current_metrics["accuracy"]) / \
                      max(current_metrics["accuracy"], 0.001)
        return {
            "current_accuracy": current_metrics["accuracy"],
            "new_accuracy": new_metrics["accuracy"],
            "improvement_percent": improvement * 100,
            "should_deploy": improvement > 0.01  # At least 1% improvement
        }

    def _eval(self, model, data) -> dict:
        return {"accuracy": 0.95, "f1": 0.93}
```

## 12. Infrastructure-as-Code for ML


### 12.1 Terraform for ML Infrastructure


```python
class MLInfrastructureConfig:
    """Generate Terraform configuration for ML infrastructure."""

    def __init__(self, project: str, region: str = "us-east-1"):
        self.project = project
        self.region = region

    def training_cluster(self, gpu_type: str = "p4d.24xlarge",
                          min_nodes: int = 1, max_nodes: int = 10) -> str:
        return f"""
resource "aws_eks_node_group" "ml_training" {{
  cluster_name    = aws_eks_cluster.ml.name
  node_group_name = "ml-training-gpu"
  node_role_arn   = aws_iam_role.ml_nodes.arn
  subnet_ids      = aws_subnet.private[*].id

  scaling_config {{
    desired_size = {min_nodes}
    min_size     = {min_nodes}
    max_size     = {max_nodes}
  }}

  instance_types = ["{gpu_type}"]

  taint {{
    key    = "nvidia.com/gpu"
    value  = "true"
    effect = "NO_SCHEDULE"
  }}

  labels = {{
    "node-type" = "gpu-training"
  }}
}}

resource "aws_iam_role" "ml_nodes" {{
  name = "ml-gpu-node-role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{ Service = "ec2.amazonaws.com" }}
    }}]
  }})
}}
"""

    def model_registry(self) -> str:
        return f"""
resource "aws_s3_bucket" "model_registry" {{
  bucket = "ml-models-{self.project}"
  acl    = "private"

  versioning {{
    enabled = true
  }}

  lifecycle_rule {{
    enabled = true

    noncurrent_version_expiration {{
      days = 90
    }}
  }}

  server_side_encryption_configuration {{
    rule {{
      apply_server_side_encryption_by_default {{
        sse_algorithm = "AES256"
      }}
    }}
  }}
}}

resource "aws_dynamodb_table" "model_metadata" {{
  name         = "ml-model-metadata"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "model_name"
  range_key    = "version"

  attribute {{
    name = "model_name"
    type = "S"
  }}

  attribute {{
    name = "version"
    type = "S"
  }}
}}
"""

    def feature_store(self) -> str:
        return f"""
resource "aws_dynamodb_table" "online_feature_store" {{
  name         = "ml-online-features-{self.project}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "feature_view"
  range_key    = "entity_key"

  attribute {{
    name = "feature_view"
    type = "S"
  }}

  attribute {{
    name = "entity_key"
    type = "S"
  }}

  ttl {{
    attribute_name = "ttl"
    enabled        = true
  }}
}}

resource "aws_glue_catalog_table" "offline_features" {{
  name          = "offline_features"
  database_name = "ml_features"
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {{
    location      = "s3://ml-features-{self.project}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    serde_info {{
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }}
  }}
}}
"""


# ML infrastructure with Pulumi
class PulumiMLInfrastructure:
    def __init__(self):
        self.resources = []

    def add_gpu_cluster(self, name: str, gpu_count: int = 4,
                         instance_type: str = "p4d.24xlarge"):
        self.resources.append({
            "type": "gpu_cluster",
            "name": name,
            "gpu_count": gpu_count,
            "instance_type": instance_type,
            "configuration": {
                "kubernetes_version": "1.28",
                "auto_scaling": True,
                "spot_instances": False
            }
        })

    def add_mlflow_server(self, artifact_store: str = "s3"):
        self.resources.append({
            "type": "mlflow_server",
            "artifact_store": artifact_store,
            "database": "postgres",
            "configuration": {
                "artifact_location": "s3://mlflow-artifacts/",
                "backend_store": "postgresql://mlflow:password@localhost/mlflow"
            }
        })

    def add_feature_store(self, online: str = "redis", offline: str = "s3"):
        self.resources.append({
            "type": "feature_store",
            "online_store": online,
            "offline_store": offline,
            "configuration": {
                "redis_cluster": True,
                "s3_bucket": "ml-features"
            }
        })

    def deploy(self) -> dict:
        return {"resources": self.resources, "status": "deployed"}
```

## 13. Canary Deployment for Models


### 12.1 Canary Infrastructure


```python
class CanaryDeployment:
    def __init__(self, model_registry: ModelRegistry, k8s_client=None):
        self.registry = model_registry
        self.k8s = k8s_client
        self.canaries: dict = {}

    def start_canary(self, model_name: str, new_version: str,
                      initial_traffic_pct: float = 5.0) -> dict:
        canary_id = f"{model_name}-canary-{int(time.time())}"
        self.canaries[canary_id] = {
            "model_name": model_name,
            "new_version": new_version,
            "current_traffic_pct": initial_traffic_pct,
            "target_traffic_pct": 100.0,
            "increment_step": 10.0,
            "evaluation_window_minutes": 15,
            "status": "running",
            "metrics": defaultdict(list)
        }

        # Deploy canary instance
        self._deploy_canary_instance(model_name, new_version)
        return {
            "canary_id": canary_id,
            "traffic_percent": initial_traffic_pct,
            "deployment": self._configure_traffic_split(model_name, new_version,
                                                         initial_traffic_pct)
        }

    def _deploy_canary_instance(self, model_name: str, version: str):
        print(f"Deploying {model_name}:{version} as canary")

    def _configure_traffic_split(self, model_name: str, version: str,
                                   traffic_pct: float) -> dict:
        return {
            "strategy": "weighted_random",
            "stable_model": f"{model_name}:production",
            "stable_traffic": 100 - traffic_pct,
            "canary_model": f"{model_name}:{version}",
            "canary_traffic": traffic_pct,
            "routing": "service_mesh_header_based"
        }

    def record_canary_metric(self, canary_id: str, metric: str, value: float):
        canary = self.canaries.get(canary_id)
        if canary:
            canary["metrics"][metric].append(value)

    def evaluate_canary(self, canary_id: str) -> dict:
        canary = self.canaries.get(canary_id)
        if not canary:
            return {"error": "canary not found"}

        metrics = canary["metrics"]
        evaluations = {}

        # Error rate check
        if "error_rate" in metrics:
            recent_errors = metrics["error_rate"][-10:]
            avg_error = np.mean(recent_errors)
            evaluations["error_rate"] = {
                "value": avg_error,
                "passed": avg_error < 0.01  # < 1% error rate
            }

        # Latency check
        if "latency_p99" in metrics:
            recent_latency = metrics["latency_p99"][-10:]
            avg_latency = np.mean(recent_latency)
            evaluations["latency_p99"] = {
                "value": avg_latency,
                "passed": avg_latency < 2000  # < 2s P99
            }

        return {
            "canary_id": canary_id,
            "evaluations": evaluations,
            "all_passed": all(e.get("passed", False) for e in evaluations.values())
        }

    def promote_canary(self, canary_id: str) -> dict:
        canary = self.canaries.get(canary_id)
        if not canary:
            return {"error": "not found"}

        evaluations = self.evaluate_canary(canary_id)
        if not evaluations["all_passed"]:
            return {
                "action": "rollback",
                "reason": "Canary evaluation failed",
                "details": evaluations
            }

        # Promote to 100%
        self._configure_traffic_split(
            canary["model_name"], canary["new_version"], 100.0
        )
        self.registry.promote_model(
            canary["model_name"], canary["new_version"], "production"
        )
        return {"action": "promoted", "version": canary["new_version"]}

    def rollback_canary(self, canary_id: str) -> dict:
        canary = self.canaries.get(canary_id)
        if not canary:
            return {"error": "not found"}
        self._configure_traffic_split(canary["model_name"], canary["new_version"], 0.0)
        return {"action": "rollback", "version": canary["new_version"], "traffic": 0}
```

## 14. CI/CD for ML


### 14.1 ML Pipeline CI/CD


```python
class MLPipelineCI:
    def __init__(self):
        self.stages = []

    def add_stage(self, name: str, command: str):
        self.stages.append({"name": name, "command": command})

    def run(self):
        results = []
        for stage in self.stages:
            print(f"Running: {stage['name']}")
            import subprocess
            result = subprocess.run(stage["command"], shell=True, capture_output=True, text=True)
            results.append({
                "stage": stage["name"],
                "success": result.returncode == 0,
                "output": result.stdout[-500:] if result.stdout else "",
                "error": result.stderr[-500:] if result.stderr else ""
            })
            if result.returncode != 0:
                break
        return results

    def to_yaml(self) -> str:
        yaml_lines = ["pipeline:", "  stages:"]
        for stage in self.stages:
            yaml_lines.append(f"    - name: {stage['name']}")
            yaml_lines.append(f"      command: {stage['command']}")
        return "\n".join(yaml_lines)


# DVC-like data versioning
class DataVersionControl:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.dvc_file = ".dvc"

    def track_data(self, data_path: str):
        import hashlib, os
        md5_hash = hashlib.md5()
        with open(data_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        hash_value = md5_hash.hexdigest()
        dvc_entry = {
            "path": data_path,
            "md5": hash_value,
            "size": os.path.getsize(data_path)
        }
        return dvc_entry

    def checkout_data(self, data_path: str, version_hash: str):
        print(f"Checking out {data_path} at version {version_hash}")
        return True

    def get_data_pipeline(self) -> dict:
        return {
            "stages": ["download", "validate", "split", "preprocess"],
            "dependencies": ["raw_data.csv"],
            "outputs": ["train.csv", "test.csv", "val.csv"]
        }
```

### 14.2 Model CI/CD Pipeline


```python
class ModelCICD:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.tests = []

    def add_test(self, name: str, test_fn: callable, threshold: float):
        self.tests.append({"name": name, "fn": test_fn, "threshold": threshold})

    def validate_model(self, model, test_data) -> dict:
        results = {}
        all_passed = True
        for test in self.tests:
            value = test["fn"](model, test_data)
            passed = value >= test["threshold"]
            results[test["name"]] = {"value": value, "threshold": test["threshold"], "passed": passed}
            if not passed:
                all_passed = False
        return {"all_passed": all_passed, "tests": results}

    def promote_if_passed(self, model, name: str, version: str, test_data) -> bool:
        validation = self.validate_model(model, test_data)
        if validation["all_passed"]:
            self.registry.register_model(model, name, version, validation)
            self.registry.promote_model(name, version, "staging")
            return True
        return False
```

## 15. Exercise Problems


**Problem 1**: Implement a complete ML pipeline with data validation, feature engineering, training, and evaluation stages. Add experiment tracking.

**Problem 2**: Build a model registry with staging promotion. Implement a canary deployment that shifts 5% traffic and auto-rollbacks on error.

**Problem 3**: Create a drift detection system that monitors feature distributions using KS-test and triggers alerts when drift exceeds threshold.

**Problem 4**: Build an LLM observability dashboard that tracks token usage, costs, latency, and safety violations across model versions.

**Problem 5**: Implement a CI/CD pipeline for ML that validates model quality against thresholds before promoting to production.

---

## Related


- [Databases](../../08-databases/) — Vector search, embeddings storage
- [Python Backend](../../03-backend/) — ML inference APIs
- [Cloud Platforms](../../05-cloud/) — GPU/TPU infrastructure
- [Data Engineering](../../02-data-engineering/) — Training data pipelines
- [Performance Engineering](../../18-performance-engineering/) — Model optimization
