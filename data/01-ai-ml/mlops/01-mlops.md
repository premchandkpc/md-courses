# MLOps: Machine Learning Operations

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

## 4. Feature Stores

### 4.1 Online and Offline Feature Serving

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

## 5. Model Serving

### 5.1 Serving Infrastructure

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

### 5.2 Serving Configuration

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

## 6. A/B Testing and Deployment Strategies

### 6.1 Deployment Strategies

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

## 7. Model Monitoring

### 7.1 Data Drift Detection

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

### 7.2 Monitoring Dashboard

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

## 8. LLM Observability

### 8.1 Token Usage and Cost Tracking

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

### 8.2 Safety Monitoring

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

### 8.3 Quality Monitoring

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

## 9. CI/CD for ML

### 9.1 ML Pipeline CI/CD

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

### 9.2 Model CI/CD Pipeline

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

## 10. Exercise Problems

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
