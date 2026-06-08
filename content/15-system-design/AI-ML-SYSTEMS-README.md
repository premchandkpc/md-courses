---
title: Google L5 AI/ML System Design Masterclass
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# 🔥 Google L5 AI/ML System Design Masterclass

Complete interview preparation for Google, Meta, Amazon, and other FAANG companies.

---

## 📚 What's Included

### 7 Complete System Designs (Markdown + Interactive HTML)

#### 1. **YouTube Recommendations** `01-YouTube-Recommendations.md`
- **Challenge:** Rank 1B videos for 2.5B users in <500ms
- **Key Concepts:** Candidate generation (FAISS), neural ranking, online learning, Thompson sampling
- **Complexity:** ⭐⭐⭐⭐⭐ (Most comprehensive, covers all fundamentals)
- **Duration:** 3-4 hour deep dive
- **Interactive Diagram:** `youtube-architecture.html`

#### 2. **Google Search Ranking** `02-Google-Search-Ranking.md`
- **Challenge:** Return 10 most relevant pages from 1T corpus in <200ms
- **Key Concepts:** Inverted indexes, LambdaMART, BERT embeddings, spam detection
- **Complexity:** ⭐⭐⭐⭐⭐ (Retrieval-heavy, different from recommendations)
- **Duration:** 2-3 hour deep dive
- **Interactive Diagram:** `search-architecture.html`

#### 3. **Ads CTR Prediction** `03-Ads-CTR-Prediction.md`
- **Challenge:** Predict clicks in <50ms, online learning at 1M QPS
- **Key Concepts:** DCN models, contextual bandits, feature stores, fraud detection
- **Complexity:** ⭐⭐⭐⭐ (Online learning focus, real-time)
- **Duration:** 2-3 hour deep dive
- **Interactive Diagram:** `ads-architecture.html`

#### 4. **LLM Serving Infrastructure** `04-LLM-Serving-Infrastructure.md`
- **Challenge:** Serve 70B models with <500ms TTFT at scale
- **Key Concepts:** Batching, KV cache, speculative decoding, quantization
- **Complexity:** ⭐⭐⭐⭐ (Modern infrastructure, inference optimization)
- **Duration:** 2-3 hour deep dive
- **Interactive Diagram:** `llm-architecture.html`

#### 5. **TikTok Feed Ranking** `05-TikTok-Feed-Ranking.md`
- **Challenge:** Infinite feed with exploration/exploitation at 2B MAU
- **Key Concepts:** RL, contextual bandits, long-term value optimization
- **Complexity:** ⭐⭐⭐⭐ (RL approach, different from others)
- **Duration:** 2 hour deep dive
- **Interactive Diagram:** `tiktok-architecture.html`

#### 6. **Netflix Recommendations** `06-Netflix-Recommendations.md`
- **Challenge:** Cold-start, diversity, long-term satisfaction
- **Key Concepts:** Collaborative filtering, batch pipelines, diversity penalties
- **Complexity:** ⭐⭐⭐ (Batch approach, simpler than real-time)
- **Duration:** 1.5 hour deep dive
- **Interactive Diagram:** `netflix-architecture.html`

#### 7. **Google Maps Ranking** `07-Maps-Ranking.md`
- **Challenge:** Rank 200M places by relevance + distance + popularity
- **Key Concepts:** Geospatial indexing, learning-to-rank, regional distribution
- **Complexity:** ⭐⭐⭐ (Geographic constraints, different domain)
- **Duration:** 1.5 hour deep dive
- **Interactive Diagram:** `maps-architecture.html`

---

## 🎯 Entry Points

### For Interviews
1. **Start with:** `L5-AI-ML-INTERVIEW-GUIDE.md` - Interview format, structure, progression
2. **Pick a system:** Most candidates do YouTube or Google Search first
3. **Use HTML visualizations:** `youtube-architecture.html` to think visually
4. **Go deep:** Read the markdown deep dive for each component

### For Learning
1. **Foundation (2-3 days):**
   - YouTube Recommendations
   - Google Search Ranking
   - Ads CTR Prediction

2. **Intermediate (1-2 days):**
   - LLM Serving
   - TikTok Feed
   - Netflix Recommendations

3. **Advanced (1 day):**
   - Maps Ranking
   - Comparative analysis
   - Production patterns

### For Specific Role Focus
- **Recommendations Engineer:** YouTube, Netflix, TikTok
- **Search/Retrieval Engineer:** Google Search, Maps
- **ML/Ranking Engineer:** Ads CTR, YouTube
- **Infrastructure Engineer:** LLM Serving, Ads CTR
- **Full-stack ML Engineer:** YouTube (covers everything)

---

## 🏗️ What Each Document Includes

### Each System Deep Dive Contains:

```
1. Context & Stats
   - Scale (DAU, QPS, latency)
   - Revenue impact
   - Core challenge

2. Requirements Clarification
   - Functional requirements
   - Non-functional requirements (SLAs)
   - Assumptions

3. Estimation
   - Traffic calculations
   - Storage sizing
   - Compute requirements
   - Cost analysis

4. Architecture
   - High-level system diagram
   - Component breakdown
   - Service interactions
   - Data flow

5. Deep Component Dives
   - Purpose of each component
   - APIs and contracts
   - Storage choices
   - Scaling strategy

6. ML System Details
   - Model architecture
   - Training pipeline
   - Inference optimization
   - Online learning approaches

7. Production Realities
   - Failure modes & detection
   - Monitoring & observability
   - A/B testing framework
   - Rollout strategy

8. Scaling Challenges
   - 10x, 100x, 1000x scenarios
   - Optimization strategies
   - Cost/quality tradeoffs

9. Tradeoff Analysis
   - Decision tables
   - Alternatives compared
   - When to use each approach

10. Interview Questions
    - Challenging follow-ups
    - Edge cases
    - Extensions
```

---

## 🎨 HTML Visualizations

Each system has an **interactive HTML** file showing:
- Architecture diagrams
- Component relationships
- Data flow visualizations
- Latency breakdowns
- Scaling strategies
- Monitoring dashboards

Open in browser to explore visually.

---

## 💡 Key Insights Across All Systems

### Fundamental Patterns

| Pattern | Systems | Key Idea |
|---------|---------|----------|
| **Multi-Pool Retrieval** | YouTube, Ads, Maps | Multiple retrieval methods for robustness |
| **Neural Ranking** | YouTube, Ads, Maps | Deep learning for scoring |
| **Online Learning** | YouTube, Ads, TikTok | Real-time adaptation via streaming |
| **Feature Stores** | All systems | Centralized real-time feature serving |
| **Caching Strategy** | All systems | L1 (memory), L2 (Redis), L3 (CDN) |
| **Graceful Degradation** | All systems | Fallback when primary fails |
| **A/B Testing** | All systems | Scientific validation before rollout |

### Comparison Table

| Aspect | YouTube | Search | Ads | LLM | TikTok | Netflix | Maps |
|--------|---------|--------|-----|-----|--------|---------|------|
| Retrieval | FAISS | Inverted Index | Feature lookup | N/A | Heuristic | Batch | Geospatial |
| Ranking | Neural | GBDT | Neural | Sampling | RL | Collab | Learning-to-rank |
| Online Learning | Yes | Limited | Yes | No | Yes | No | Yes |
| Latency SLA | <500ms | <200ms | <50ms | <500ms | <500ms | Hours | <200ms |
| Freshness | Real-time | Hours | Real-time | N/A | Per scroll | Daily | Real-time |

---

## 🎓 Interview Progression

### Typical Interview Flow (3-4 hours)

**Phase 1: Requirements** (10-15 min)
- Clarify what we're optimizing for
- Non-functional requirements
- Make assumptions explicit

**Phase 2: Estimation** (10-15 min)
- Back-of-envelope calculations
- Show your work
- Validate feasibility

**Phase 3: Architecture** (15-20 min)
- High-level system design
- Component boundaries
- Request flow

**Phase 4: Deep Dives** (60-90 min)
- Retrieval component
- Ranking component
- Feature engineering
- Online learning (if applicable)

**Phase 5: Production** (30-45 min)
- Failure modes
- Monitoring
- A/B testing
- Scaling strategies

**Phase 6: Challenges** (30-45 min)
- Interviewer challenges your design
- Push on bottlenecks
- Discuss tradeoffs
- Defense against attacks

---

## 🔥 Real Google L5 Interview Behavior

### Interviewer Will:
- ✅ Interrupt with follow-ups
- ✅ Challenge your assumptions
- ✅ Ask edge cases
- ✅ Test your scaling understanding
- ✅ Probe ML tradeoffs
- ✅ Question architectural choices
- ✅ Look for production thinking

### You Should:
- ✅ Think out loud
- ✅ Make assumptions explicit
- ✅ Support claims with math
- ✅ Discuss tradeoffs honestly
- ✅ Acknowledge unknowns
- ✅ Ask clarifying questions
- ✅ Show system thinking

### NOT Expected:
- ❌ Memorized answers
- ❌ Perfect solutions
- ❌ Shallow breadth
- ❌ Ignoring failures
- ❌ Over-engineering
- ❌ Hand-waving

---

## 🚀 How to Use These Materials

### Option 1: Self-Study (1-2 weeks)
1. Read `L5-AI-ML-INTERVIEW-GUIDE.md`
2. Work through YouTube deep dive (most comprehensive)
3. Try Google Search (different retrieval model)
4. Do Ads CTR (online learning focus)
5. Review comparative analysis
6. Practice interviewing yourself

### Option 2: Daily Deep Dives (5-7 days)
- Day 1: YouTube (foundation)
- Day 2: Google Search (retrieval)
- Day 3: Ads CTR (online learning)
- Day 4: LLM Serving (modern infra)
- Day 5: TikTok (RL approach)
- Day 6: Netflix (batch approach)
- Day 7: Maps (geospatial)

### Option 3: Focused Preparation (2-3 days)
- Pick 1-2 systems most relevant to your role
- Deep dive all components
- Practice explaining under pressure
- Prepare for follow-up challenges

---

## 📊 Document Statistics

- **Total Markdown:** 8 files, ~40,000 words
- **Total HTML:** 7 interactive visualizations
- **Systems Covered:** 7 major companies' real infrastructure
- **Depth Level:** Google L5/L6 (Staff Engineer equivalent)
- **Interview Complexity:** 3-4 hours per system

---

## 🎯 Success Criteria

After working through these materials, you should be able to:

- [ ] Design a complete recommendation system from scratch
- [ ] Estimate resource requirements (storage, compute, QPS)
- [ ] Explain tradeoffs between approaches
- [ ] Discuss production failure modes & solutions
- [ ] Defend your design against challenges
- [ ] Compare different systems architecturally
- [ ] Identify bottlenecks and scaling strategies
- [ ] Explain online learning & exploration/exploitation
- [ ] Design A/B testing frameworks
- [ ] Think about cost optimization

---

## 📖 Files in This Directory

```
ai-ml-systems-design/
├── L5-AI-ML-INTERVIEW-GUIDE.md (interview format & overview)
├── AI-ML-SYSTEMS-README.md (this file)
├── systems-index.html (interactive index of all systems)
│
├── 01-YouTube-Recommendations.md
├── youtube-architecture.html
│
├── 02-Google-Search-Ranking.md
├── search-architecture.html
│
├── 03-Ads-CTR-Prediction.md
├── ads-architecture.html
│
├── 04-LLM-Serving-Infrastructure.md
├── llm-architecture.html
│
├── 05-TikTok-Feed-Ranking.md
├── tiktok-architecture.html
│
├── 06-Netflix-Recommendations.md
├── netflix-architecture.html
│
├── 07-Maps-Ranking.md
├── maps-architecture.html
│
├── production-patterns.md
├── tradeoff-analysis.md
├── interview-tips.md
├── scaling-strategies.md
├── ab-testing-framework.md
└── cost-optimization.md
```

---

## 🎬 Start Here

**First time?** Open `systems-index.html` in your browser. Interactive, visual, engaging.

**Want to dive deep?** Start with `01-YouTube-Recommendations.md`. Most comprehensive.

**Short on time?** Pick `youtube-architecture.html` + YouTube markdown sections 1-3.

**Preparing for interview tomorrow?** Focus on YouTube (foundation) + one other system relevant to role.

---

## ⚡ Pro Tips

1. **Read once, think 10 times.** Don't just read—think through how you'd build this.
2. **Draw diagrams.** Use whiteboard/paper to sketch architectures.
3. **Estimate constantly.** Practice back-of-envelope math on latency, storage, compute.
4. **Defend your decisions.** Why FAISS not Milvus? Why neural ranking not GBDT? Be ready.
5. **Know the limits.** "This would need experimentation" beats "I don't know" 100%.
6. **Talk through it.** Explain your design to a friend/rubber duck. Get comfortable verbalizing.
7. **Practice under pressure.** Set a 45-min timer and see how far you get.

---

## 🔥 Reality Check

These are **real systems** at **real scale** with **real constraints**:
- 1B+ daily active users
- Sub-100ms latency requirements
- 99.99% availability
- Billions in revenue at stake
- Adversarial (spam, fraud, gaming)

Not simplified. Not theoretical. Not one-person projects.

This is what **Google L5 / Staff Engineer** thinks about every day.

---

## 📞 How to Use

### Before Interview
1. Pick a system
2. Read the markdown deep dive
3. Sketch the architecture
4. Estimate requirements
5. Prepare for "what if" questions

### During Interview
1. Clarify requirements
2. Show your math
3. Draw diagrams
4. Discuss tradeoffs
5. Handle challenges with reasoning, not memorization

### After Interview
1. Review what you struggled on
2. Deep dive that component
3. Find similar concepts in other systems
4. Keep practicing

---

**Good luck. Go deep. Think production.**

---

*Last Updated: May 2026*
*Difficulty: Google L5 / Staff Engineer*
*Expected Preparation Time: 1-2 weeks for full mastery*
