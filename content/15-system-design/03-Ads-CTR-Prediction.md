# Ads CTR Prediction - L5 Deep Dive

> **[🎨 View Interactive Diagram](ads-architecture.html)** | [← Back to Index](systems-index.html)

*"Predict which ad a user will click in <50ms, millions of times per second."*

---

## 🎯 Context

**Google Ads Scale:**
- 400M+ ad impressions per day
- 1M+ QPS during peak
- $280B annual revenue (ads)
- CTR prediction critical (determines ranking & pricing)
- Adversarial users (advertisers, click fraudsters)

**Core Challenge:** Online learning at extreme scale + adversarial robustness.

---

## 📋 Requirements

### Functional
1. Predict CTR for (user, ad) pair <50ms
2. Handle continuous feature updates
3. Detect & prevent click fraud
4. Support A/B testing for models
5. Refresh predictions in real-time

### Non-Functional
- QPS: 1M+
- Latency: p99 <50ms
- Accuracy: AUC >0.95
- Availability: 99.99%
- Fraud detection: <0.5% false positive rate

---

## 📊 Estimation

### Traffic

```
Daily impressions: 400M
QPS = 400M / 86400 = 4,600 QPS
Peak (multiple ads per impression): 1M QPS

Breakdown:
- Search ads: 400M impressions
- Display ads: 1B+ impressions
- Video ads: 1B+ impressions
```

### Compute

**Model Inference:**
```
Per prediction:
- Load user features: 1ms
- Load ad features: 1ms
- Feature computation: 2ms
- Model inference: 10ms
- Total: 14ms

QPS: 1M
GPUs per second: 1M * 14ms / 1000ms = 14K GPU-milliseconds/second

But batching helps:
- Batch size: 10K
- Batch latency: 10ms
- Throughput: 10K queries / 10ms = 1M QPS

GPUs needed: 50 (with redundancy: 300)
```

### Storage

**Model State:**
```
Weights: ~100MB per model
Feature embeddings: 1B ads * 10 features * 4 bytes = 40GB
User profiles: 2B users * 100 features * 4 bytes = 800GB
```

---

## 🏗️ Architecture

```
User impression
    │
    ▼
┌─────────────────────────┐
│ Feature Collection      │
│ (user, context, ad)     │
└──────────┬───────────────┘
           │
    ┌──────┴──────────────┐
    │                     │
    ▼                     ▼
┌─────────────┐  ┌──────────────┐
│ Real-time   │  │ Precomputed  │
│ Features    │  │ Features     │
│ (Kafka)     │  │ (Feature DB) │
└──────┬──────┘  └──────┬───────┘
       │                │
       └────────┬───────┘
                │
                ▼
    ┌─────────────────────────┐
    │ CTR Model Inference     │
    │ (Neural Network)        │
    │ Predict click prob      │
    └──────────┬──────────────┘
               │
               ▼
    ┌─────────────────────────┐
    │ Rank Ads by CTR         │
    │ (highest CTR first)     │
    └──────────┬──────────────┘
               │
               ▼
    ┌─────────────────────────┐
    │ Serving (show ads)      │
    │ + log impression        │
    └──────────┬──────────────┘
               │
               ▼
            Ad shown
               │
               ▼ (user clicks or skips)
    ┌─────────────────────────┐
    │ Feedback Loop           │
    │ (log click to Kafka)    │
    └─────────────────────────┘
```

---

## 🤖 ML: CTR Prediction Model

### Model Architecture

```
Input Features (200):
├─ User features (100)
│  ├─ Demographics (age, gender, country)
│  ├─ User history embeddings (256D compressed → 32D)
│  ├─ Past CTR rate
│  ├─ Past conversion rate
│  ├─ Engagement features
│  └─ Device type
│
├─ Ad features (60)
│  ├─ Ad text embeddings
│  ├─ Ad image embeddings
│  ├─ Category
│  ├─ Advertiser reputation
│  ├─ Ad age
│  └─ Quality score
│
└─ Context (40)
   ├─ Time of day
   ├─ Device type
   ├─ Location
   ├─ Query (for search ads)
   └─ Seasonality

Model:
Deep & Cross Network (DCN)

            Input (200D)
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
    Cross Tower      Deep Tower
    (interacts)      (learns)
        │                │
     Cross1            Dense1
        │               ReLU
     Cross2            Dense2
        │               ReLU
     Cross3            Dense3
        │                │
        └────────┬───────┘
                 │
                 ▼
            Dense(64)
             ReLU
                 │
                 ▼
            Dense(1)
             Sigmoid
                 │
                 ▼
            CTR [0-1]
```

### Training

**Data:**
```
Source: Impression logs
- Daily: 400M impressions
- Label: click=1, no_click=0
- Class imbalance: CTR ~2% (200:1 ratio)

Handling imbalance:
- Weighted loss: weight_positive = 50
- Down-sample negatives to 1:10 ratio
- Use focal loss: more weight on hard negatives
```

**Loss Function:**
```
Binary cross-entropy with class weighting:

Loss = -w+ * y*log(ŷ) - w- * (1-y)*log(1-ŷ)

where:
  w+ = 50 (positive class weight - clicks are rare)
  w- = 1 (negative class weight)
  y = actual (0 or 1)
  ŷ = predicted probability
```

**Training Schedule:**
```
Batch training (daily):
- Data: 400M fresh impressions
- Batch size: 64K
- Learning rate: 0.001 with decay
- Epochs: 3
- Time: 4 hours on 100 GPUs
- Validation: holdout 10% of data

Online training (hourly):
- Mini-batch: 100K recent impressions
- Learning rate: 0.0001 (small, to avoid drift)
- Update: new user/ad interactions
- Result: model adapts to user trends
```

---

## 💬 Online Learning

### Real-Time Feature Updates

```
Stream pipeline:
Impression → Kafka → Flink → Feature Store

Updates (every 1 minute):
├─ User CTR rate (aggregate from last 1000 clicks)
├─ User conversion rate
├─ Ad performance (CTR over time)
├─ Seasonal trends
└─ Emerging interests

Implementation:
├─ Kafka topic: "impressions"
├─ Flink job: aggregate clicks by (user, time_window)
├─ Redis update: user CTR rate
├─ Inference: uses fresh features
```

### Bandit Algorithm for Ad Ranking

```
Problem: If CTR model is wrong, we show wrong ads
Solution: Exploration via Thompson Sampling

For each ad:
├─ Maintain Beta(alpha, beta) distribution
├─ alpha = number of clicks
├─ beta = number of skips

Ranking decision:
├─ Sample theta_i ~ Beta(alpha_i, beta_i) for each ad
├─ Rank ads by theta_i (includes uncertainty)
├─ High uncertainty → higher chance of exploration

Example:
  Ad A: alpha=1000, beta=4000 (CTR=20%, certain)
    theta_A ~ Beta(1000, 4000) → mostly 20%
  
  Ad B: alpha=10, beta=40 (CTR=20%, uncertain)
    theta_B ~ Beta(10, 40) → varies wildly, often high!
  
  Result: Ad B might rank higher (exploration opportunity)

Feedback:
  If Ad B gets click → alpha_B += 1 → becomes more certain
  If Ad B no click → beta_B += 1 → becomes less attractive
```

### Contextual Bandits

```
Problem: Thompson sampling doesn't use context
Solution: Contextual bandits per user segment

For each (user_segment, ad_category) pair:
├─ Maintain CTR estimate
├─ Rank ads for that segment
├─ Learn segment-specific preferences

Example:
  18-25 year old in US + Tech category:
    → RL model predicts click probability
    → Update based on feedback
    → Segment sees different ranking than 50+ year old
```

---

## 🔧 Real-Time Feature Store

**Problem:** Computing features for 1M QPS is slow

**Solution:** Precomputed cache + streaming updates

```
Redis-based feature store:
├─ User features (hot)
│  └─ Key: "user:{user_id}"
│  └─ Value: [demographics, embedding, ctr_rate, ...]
│  └─ TTL: 1 hour (refreshed by streaming)
│  └─ Size: 2B users * 400 bytes = 800GB
│
├─ Ad features (medium)
│  └─ Key: "ad:{ad_id}"
│  └─ Value: [text_embed, image_embed, category, ...]
│  └─ TTL: 1 day
│  └─ Size: 100M ads * 500 bytes = 50GB
│
└─ Context features (computed on-demand)
   └─ Time of day, location, device
   └─ Computation: <1ms

Access pattern:
├─ p95: cache hit (feature available)
├─ p99: recompute (stale feature, recompute fresh)
└─ Cache hit rate: ~98%
```

---

## 🛡️ Fraud Detection

```
Problem: Click fraud (fake clicks to burn competitor budget)

Signals:
├─ Rapid clicks from same IP (suspicious)
├─ Click rate > expected CTR (too good)
├─ Clicks from data center IPs (bots)
├─ Unusual device/browser fingerprint
├─ Geographic anomalies

Detection model:
├─ Random forest (fast, interpretable)
├─ 100 features from impression logs
├─ Real-time scoring

Action:
├─ Mark suspicious click with fraud_score
├─ If fraud_score > 0.9: exclude from billing
├─ Advertiser refund
├─ Blacklist source

Trade-off:
├─ False positive rate: 0.5% (some real users falsely marked)
├─ False negative rate: 5% (some fraud slips through)
├─ Conservative threshold (prefer false positive)
```

---

## ⚡ Production

### Handling Feedback Latency

```
Problem: Click happens 500ms after prediction
- User clicks ad after 0.5 seconds
- Feedback logged to Kafka
- Aggregated every 1 minute
- Features updated in feature store

Effect: Model sees feedback with ~1 min lag

Impact on learning:
├─ User interest shifts → model learns ~1 min later
├─ Usually acceptable (user interests don't change in seconds)
├─ Handled by online learning (updates hourly)

Edge case: Breaking news (interests change in minutes)
└─ Mitigated by heavy weighting of recent signals
```

### Model Monitoring

```
Alerts (real-time):
├─ AUC drops >0.01 (model degradation)
├─ CTR prediction error >20% (systematic bias)
├─ Inference latency spike
├─ Fraud rate spike

Actions:
├─ If AUC drops: investigate data quality, retrain
├─ If latency spike: scale GPU cluster
├─ If fraud spike: tighten fraud detection threshold

Model retraining schedule:
├─ Daily batch retrain (4 hours)
├─ Hourly online updates (light, <10 min compute)
├─ A/B test new model (1% traffic first)
```

---

## 📊 A/B Testing Framework

```
Pipeline:
1. Develop new CTR model
2. Train on historical data
3. Shadow traffic test
   └─ Run both models, compare results (no impact on users)
4. Online A/B test
   ├─ 1% users get new model
   ├─ 99% get old model
   ├─ Measure: CTR, conversion rate, ad spend per user
5. Rollout
   ├─ If metrics improve: gradual rollout (10% → 50% → 100%)
   ├─ If metrics degrade: rollback immediately

Duration:
├─ A/B test: 1-2 weeks
├─ Statistical power: needs ~1M impressions to detect 0.5% change

Result: Only improvements ship
```

---

## 🔴 Failure Scenarios

### Failure 1: Feature Store Timeout

```
Symptom: p99 latency jumps to 200ms (SLA: 50ms)

Cause:
- Feature store (Redis) becomes slow
- Network latency spike
- Cache eviction (features dropping out)

Mitigation:
├─ Fallback: use cached features from 1 hour ago
├─ Impact: CTR prediction uses stale features (less accurate)
├─ Quality: ~2-3% CTR accuracy drop
├─ User impact: ads shown are slightly less relevant
└─ Complete in <5ms (fast fallback)
```

### Failure 2: Model Inference Timeout

```
Symptom: 1% of users get no ads (no predictions)

Cause:
- GPU cluster bottleneck
- Queue too long

Mitigation:
├─ Drop to fallback model (simpler, faster)
├─ Or: return ads by CTR of previous hour
├─ Or: return top-performing ads (no personalization)
└─ Better to serve something than nothing
```

### Failure 3: Click Fraud Wave

```
Symptom: CTR spikes 20% (unusual), advertiser receives refund requests

Cause:
- Competitor click-bombing
- Botnet attack
- Compromised user account

Detection:
├─ Click rate spike + suspicious pattern
├─ Fraud detection model fires
└─ Alert on-call

Action:
├─ Increase fraud detection threshold (stricter)
├─ Identify source (IP, account)
├─ Block source
├─ Refund advertiser
└─ Investigate account security
```

---

## 🚀 Scaling

### 10x Traffic (10M QPS)

```
Current constraint: Model inference (50ms)

Solution 1: Quantization
├─ float32 → int8 (4x compression)
├─ Latency: 50ms → 25ms
├─ Accuracy: 98% (0.5% AUC drop acceptable)

Solution 2: Batch larger
├─ Current batch: 10K
├─ Increase: 100K
├─ Latency: 25ms → 40ms (trade: more accumulation)

Solution 3: Distillation
├─ Train 10x smaller student model
├─ On-device inference (mobile)
├─ Latency: 40ms → 5ms
└─ Run on CPU instead of GPU

Solution 4: Approximate inference
├─ Don't evaluate all ads
├─ Use heuristic to filter to top-100
├─ Only predict for top-100
└─ 10x fewer predictions

Use: Distillation + larger batches
Result: Handle 10M QPS with 500 GPUs (vs 3000 needed without optimization)
```

---

## 💭 Interview Questions

1. How would you handle a new advertiser with no click history?
2. If fraud detection model has 10% false positive rate, how do you decide?
3. How would you test that online learning doesn't degrade model?
4. What if feature store is down - what's your fallback strategy?
5. How do you optimize for both CTR and conversion rate simultaneously?

---

*Last Updated: 2026-05-28*
