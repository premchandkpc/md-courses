---
title: Google L5 AI/ML System Design Interview Masterclass
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# 🔥 Google L5 AI/ML System Design Interview Masterclass

**Real Google L5/L6 level. Deep. Uncompromising.**

---

## 📋 Interview Structure

### Phase 1: Requirements Clarification (10-15 min)
- Functional requirements
- Non-functional requirements (DAU/MAU/QPS/latency/consistency)
- Personalization scope
- Real-time vs batch tradeoffs
- Geographic distribution

### Phase 2: Estimation (10-15 min)
- QPS calculations
- Storage sizing (embeddings, features, models)
- Network bandwidth
- GPU/compute requirements
- Cost analysis

### Phase 3: Architecture Design (15-20 min)
- High-level system diagram
- Service decomposition
- Data flow
- ML pipeline architecture
- Online/offline separation

### Phase 4: Deep Component Dives (20-30 min)
- Retrieval system (candidate generation)
- Ranking system
- Feature engineering & feature stores
- Vector databases & embeddings
- Real-time feature pipelines

### Phase 5: ML System Specifics (15-25 min)
- Model architectures
- Training pipelines
- Inference optimization
- Online learning
- Exploration vs exploitation
- Cold start problem
- Multi-objective optimization

### Phase 6: Production Realities (10-20 min)
- Failure modes
- Monitoring & observability
- A/B testing & experimentation
- Model monitoring & drift detection
- Rollout strategy

### Phase 7: Scaling Challenges (15-20 min)
- 100x traffic increase
- Latency bottlenecks
- Model inference at scale
- Vector search at scale
- Feature store scaling

---

## 🎯 Systems Covered

### 1. **YouTube Recommendations** (Most Complex)
- **Core Challenge:** Rank billions of videos for billions of users in real-time
- **ML Focus:** CTR + Watch-time prediction, freshness boost, diversity
- **Systems Focus:** Candidate generation, ranking, re-ranking pipeline
- **Scaling:** 1B+ QPS at ranking layer

### 2. **Google Search Ranking**
- **Core Challenge:** Return 10 most relevant results from trillion-page corpus
- **ML Focus:** Relevance modeling, BERT integration, query understanding
- **Systems Focus:** Retrieval (inverted index), ranking, spell correction
- **Scaling:** 10M+ QPS, sub-100ms latency SLA

### 3. **Ads CTR Prediction**
- **Core Challenge:** Predict likelihood user clicks ad (real-time)
- **ML Focus:** Online learning, contextual bandits, feature engineering
- **Systems Focus:** Real-time feature store, streaming pipelines, model serving
- **Scaling:** 1M+ QPS, <50ms inference latency

### 4. **TikTok Feed Ranking**
- **Core Challenge:** Generate infinite personalized feed (exploration/exploitation)
- **ML Focus:** Multi-armed bandits, reinforcement learning, long-term value optimization
- **Systems Focus:** Real-time ranking, user engagement prediction
- **Scaling:** 2B+ MAU, <500ms p99 latency

### 5. **Netflix Recommendations**
- **Core Challenge:** Cold-start, diversity, long-term satisfaction
- **ML Focus:** Collaborative filtering + content-based, diversity penalties
- **Systems Focus:** Batch computation, offline ML pipeline
- **Scaling:** 250M+ users, diverse catalog complexity

### 6. **Maps Ranking**
- **Core Challenge:** Rank places by relevance + distance + popularity
- **ML Focus:** Learning-to-rank, geospatial features, real-time signals
- **Systems Focus:** Geo-partitioned indexes, locality-aware serving
- **Scaling:** Geographically distributed, regional spike handling

### 7. **LLM Serving Infrastructure** (New Category)
- **Core Challenge:** Serve 70B parameter models with low latency
- **ML Focus:** Quantization, batching, speculative decoding, KV cache management
- **Systems Focus:** GPU clusters, request scheduling, backpressure
- **Scaling:** Inference optimization, cost per token

---

## 🏗️ What You'll Learn

### System Design Skills
- [ ] Massive-scale distributed architecture
- [ ] Service decomposition & APIs
- [ ] Data partitioning strategies
- [ ] Caching layers & consistency
- [ ] Failure handling & recovery
- [ ] Monitoring & observability

### ML Engineering Skills
- [ ] Retrieval systems (ANN, FAISS, Milvus)
- [ ] Ranking models (XGBoost, neural networks)
- [ ] Feature engineering at scale
- [ ] Feature stores (Tecton, Feast)
- [ ] Real-time vs batch tradeoffs
- [ ] Online learning & bandits
- [ ] Model serving optimization

### Production Engineering Skills
- [ ] A/B testing frameworks
- [ ] Experimentation infrastructure
- [ ] Model monitoring & drift
- [ ] Canary deployments
- [ ] Shadow traffic testing
- [ ] Incident response
- [ ] Cost optimization

### Distributed Systems Skills
- [ ] Kafka for streaming
- [ ] Eventual consistency patterns
- [ ] Distributed caching
- [ ] Load balancing strategies
- [ ] Graceful degradation
- [ ] Cascading failure prevention

---

## 🔴 Interview Interview Format

**Interviewer plays REAL Google L5 role:**
- Interrupt with follow-ups
- Challenge assumptions
- Push on edge cases
- Test scaling understanding
- Probe ML tradeoffs
- Question architectural choices

**Candidate (you) should:**
- Think out loud
- Make assumptions explicit
- Draw architecture diagrams
- Back up claims with math
- Discuss tradeoffs honestly
- Acknowledge unknowns

---

## 📊 Progression Path

**Day 1: Single System Deep Dive**
- Pick: YouTube OR Ads CTR OR Maps
- 3-4 hour deep interview
- Complete architecture + production reality

**Day 2: Comparative Architecture**
- YouTube vs Netflix (engagement vs satisfaction)
- Google Search vs Maps (relevance scope)
- Ads vs TikTok (online learning approaches)

**Day 3: Advanced Topics**
- Multi-system orchestration
- Cost optimization across systems
- Model serving at 100x scale
- Failure mode analysis

---

## 🎓 Interview Tips

### Structure Your Answer
```
1. Clarify requirements (restate back)
2. Make assumptions explicit
3. Back-of-envelope estimation
4. High-level architecture
5. Deep dive each component
6. Discuss tradeoffs
7. Handle follow-up challenges
```

### Show Production Thinking
- Mention monitoring/alerting
- Discuss failure scenarios
- Talk about A/B testing
- Consider cost implications
- Mention gradual rollout strategy

### Push Back (Respectfully)
- "That's a good point, but..."
- "I'd optimize for X first because..."
- "That trades off Y for Z..."

### Know Your Limits
- Say "I'd investigate that" vs guessing
- Mention where you'd experiment (A/B test)
- Acknowledge unknowns

---

## 📚 Deep Dive Documents

Each system has:
- **Requirements** - Functional & non-functional
- **Estimation** - QPS, storage, compute
- **Architecture** - Detailed component diagrams
- **ML Pipeline** - Training + inference
- **Production** - Failures + monitoring
- **Scaling** - 10x/100x challenges
- **Tradeoffs** - Decision tables

---

## 🚀 Start Here

**Option A: Single Deep Interview** (3-4 hours)
→ Start with `01-YouTube-Recommendations.md`

**Option B: Comparative Study** (2 hours each)
→ Pick 2 systems, contrast their approaches

**Option C: Your Choice**
→ Pick system most relevant to your role

---

**Remember:** Google L5 is about:
- ✅ Scale
- ✅ Tradeoffs
- ✅ Production reality
- ✅ Honest limitations
- ✅ Deep technical understanding

Not about:
- ❌ Memorizing answers
- ❌ Shallow breadth
- ❌ Perfect correctness
- ❌ Avoiding mistakes
- ❌ Having all answers

---

*Last updated: 2026-05-28*
