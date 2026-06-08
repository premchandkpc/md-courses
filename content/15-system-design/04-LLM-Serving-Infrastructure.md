---
title: LLM Serving Infrastructure - L5 Deep Dive
topic: 15-system-design
difficulty: advanced
time: 30m
paths:
  - system-design
  - staff
---

# LLM Serving Infrastructure - L5 Deep Dive

> **[🎨 View Interactive Diagram](llm-architecture.html)** | [← Back to Index](systems-index.html)

*"Serve 70B parameter models with 500ms latency to millions of users."*

---

## 🤖 Context

**Gemini/GPT Scale:**
- Billions of daily requests
- 70B-540B parameter models
- Sub-500ms latency requirement
- High cost per inference ($$$)
- Safety constraints (no toxic output)

**Core Challenge:** Inference optimization at massive scale + cost minimization.

---

## 📋 Requirements

### Functional
1. Process natural language prompts
2. Generate text sequentially (token-by-token)
3. Support multi-turn conversations
4. Apply safety filtering
5. Log all requests for safety/auditing

### Non-Functional
- QPS: 100K+ concurrent users
- Latency: p50 <100ms, p99 <500ms per token
- Cost: <$0.01 per 1K tokens
- Availability: 99.99%
- Memory: <100GB per model instance (fit on 1-2 GPUs)

---

## 📊 Estimation

### Token Generation Time

```
Model: 70B parameters
Batch size: 1 user at a time (interactive)
Inference time per token: 100ms

Why 100ms?
- 70B params * 2 bytes (fp16) = 140GB model
- GPU memory: 80GB per H100 GPU
- 2 GPUs per model instance

Token generation:
- Read model from GPU memory: 140GB / 10GB/s = 14ms
- Compute attention: 70ms
- Compute MLP: 15ms
- Total: ~100ms per token

For 100-token response: 10 seconds (too slow!)
```

### Optimization 1: Batching

```
Instead of 1 user:
- Batch 100 users together
- Each user at different stage:
  ├─ User 1: computing token 50
  ├─ User 2: computing token 25
  ├─ User 3: computing token 10
  └─ ...

Key insight: Batching hides sequential latency
- Single token generation: 100ms
- Batched 100 tokens from 100 users: 100ms (all in parallel!)

Throughput: 100 tokens / 100ms = 1000 tokens/sec per GPU
```

### Optimization 2: KV Cache

```
Problem: During generation, recompute attention for all previous tokens

Key-Value Cache:
├─ Store computed K,V for previous tokens
├─ Reuse in next generation
├─ Avoids recomputation

Memory:
- Per token in context: 
  KV size = 2 * num_layers * hidden_dim * seq_len * 2 bytes
  = 2 * 80 * 8000 * 1000 * 2 = ~2.56GB per seq_len=1000

Trade-off:
├─ Memory growth with context length
├─ But computation reduction: ~10x faster
└─ Acceptable trade

Result:
- Token generation: 100ms → 10ms (with KV cache)
- Throughput: 1000 tokens/sec → 10,000 tokens/sec per GPU
```

### Tokens per User per Day

```
Concurrent users: 100K
Avg session length: 10 exchanges
Tokens per exchange:
├─ Prompt: 100 tokens
├─ Response: 300 tokens

Total tokens per user per day: 10 * (100 + 300) = 4000 tokens

Daily tokens: 100K concurrent * 4000 = 400M tokens/day

QPS (tokens): 400M / 86400 = 4600 tokens/sec
```

### GPU Cluster Size

```
With optimizations (batching + KV cache):
- Throughput: 10,000 tokens/sec per GPU
- Daily demand: 4600 tokens/sec
- GPUs needed: 4600 / 10000 = 0.5 GPUs

But with redundancy/headroom:
- Peak: 3x average = 13,800 tokens/sec
- GPUs needed: 13,800 / 10000 = 1.4 GPUs
- With redundancy (5x): 7 GPUs

So: 10-20 H100 GPUs for 100K concurrent users (surprisingly few!)
Cost: 20 GPUs * $2/hour = $40/hour (if on-demand)
```

---

## 🏗️ Architecture

```
User Request
    │
    ▼
┌─────────────────────────────┐
│ Request Router              │
│ (route to available GPU)    │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Request Batching Queue      │
│ (accumulate batch of 100)   │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Context Manager             │
│ (load conversation history) │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Tokenizer                   │
│ (prompt → token IDs)        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Model Inference             │
│ (LLM forward pass)          │
│ Batched inference on GPU    │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Token Sampling              │
│ (pick next token)           │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Safety Filter               │
│ (check output)              │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Stream Response             │
│ (send token to user)        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Logging                     │
│ (store for analysis)        │
└─────────────────────────────┘
```

---

## 🤖 Serving Strategy

### Token-by-Token Streaming

```
Traditional (generate all at once):
├─ User sends prompt
├─ Model waits for complete response (30 tokens * 100ms = 3s)
├─ User sees nothing for 3 seconds
├─ Then complete response appears
└─ Poor UX (feels slow)

Streaming (token-by-token):
├─ User sends prompt
├─ Server generates token 1 (100ms) → stream to user
├─ User sees token 1 immediately (better!)
├─ Server generates token 2 (100ms)
├─ Server generates token 3 (100ms)
└─ User sees progressive completion (better UX)

Implementation:
├─ Use WebSocket or Server-Sent Events (SSE)
├─ Send each token as it completes
├─ Client renders progressively
└─ Perceived latency: first token (good!)
```

### Request Batching

```
Without batching:
├─ User 1 request → queue → GPU picks up
├─ User 2 request → queue → GPU picks up (User 1 still computing)
├─ Sequential execution
└─ Wasted compute (could batch)

With batching:
├─ User 1,2,3,...,100 requests arrive
├─ Wait 10ms for batch to accumulate
├─ GPU processes all 100 together
├─ Each completes in parallel
└─ 100x throughput!

Trade-off:
├─ Accumulation latency: 10ms
├─ But single token generation still 100ms
├─ So total first-token latency: 110ms (acceptable)
└─ Huge throughput gain
```

### Speculative Decoding

```
Problem: Token generation is sequential (100ms per token)
Can't parallelize generation of token i+1 until token i computed

Solution: Guess next token, verify in parallel

Speculative approach:
├─ Model generates token i (100ms)
├─ While Model computes token i+1:
│  ├─ Smaller model guesses tokens i+1, i+2, i+3
│  ├─ Guess: "The quick brown fox..."
│  └─ Latency: 20ms for 3 tokens
│
├─ Model finishes token i+1
├─ Verify if guessed tokens match
├─ If yes: accept all 3, save compute
├─ If no: revert to model output

Result:
├─ Best case: 3x speedup
├─ Average case: 1.5-2x speedup
└─ Trade: need small drafter model (overhead)
```

---

## 🛡️ Safety & Cost Control

### Safety Filtering

```
Pipeline:
├─ Prompt → Prompt safety check
│  ├─ Block harmful requests early
│  └─ Return error to user
│
├─ Model generates response
│
├─ Output → Output safety check
│  ├─ Detect toxic/harmful content
│  ├─ Block before returning
│  └─ Log for analysis

Implementation:
├─ DLP (Data Loss Prevention) model
├─ Run on model output
├─ Latency: <50ms (separate GPU)
└─ Precision: 99% (false positive rate 1%)
```

### Token Limit Control

```
Problem: User requests 100K token response (expensive!)

Solution: Max token limit per user

Rules:
├─ Free users: max 500 tokens per request
├─ Paid users: max 2000 tokens per request
├─ Enforce at request time (stop generation early)

Implementation:
├─ Track generated token count
├─ Stop at limit
├─ Truncate gracefully (end of sentence)
└─ Return "truncated" flag to client
```

---

## 📊 Model Management

### Multi-Model Serving

```
Deploy multiple models:
├─ Small (7B params)
│  ├─ Fast: 10ms per token
│  ├─ Latency SLA: <200ms
│  ├─ Cost: cheap
│  └─ Use for: simple queries
│
├─ Medium (70B params)
│  ├─ Balanced: 100ms per token
│  ├─ Latency SLA: <500ms
│  ├─ Cost: medium
│  └─ Use for: general queries
│
└─ Large (540B params)
   ├─ Powerful: 500ms per token
   ├─ Latency SLA: <2s
   ├─ Cost: expensive
   └─ Use for: complex reasoning

Router logic:
├─ Classify query complexity
├─ Route to appropriate model
├─ Balance cost/quality
```

### Model Caching

```
Problem: Similar queries need similar responses

Solution: Cache query → response

Implementation:
├─ Hash(prompt) → cached response
├─ TTL: 24 hours
├─ Cache hit rate: ~30% (repeated queries)

Cache memory:
├─ Store top 1M queries + responses
├─ Response size: avg 500 tokens
├─ Memory: 1M * 2KB = 2GB (compress)
├─ Distributed across cache tier

Result:
├─ 30% of requests: <10ms (cache hit)
├─ 70% of requests: 100-500ms (model inference)
├─ Weighted avg: 350ms
```

---

## ⚡ Production

### Monitoring

```
Metrics:
├─ Time-to-first-token (TTFT)
│  └─ Latency to first token (user perception)
├─ Tokens-per-second (TPS)
│  └─ Generation speed after first token
├─ Cost-per-token
│  └─ GPU compute cost
└─ Queue depth
   └─ Pending requests (backpressure)

Alerts:
├─ TTFT > 500ms
├─ Queue depth > 1000
├─ Cost per token > $0.02
└─ Error rate > 0.1%
```

### Handling Overload

```
Graceful degradation:
├─ When queue > 1000:
│  └─ Switch to smaller model (fast but less accurate)
│
├─ When queue > 5000:
│  └─ Return cached response (if available)
│
├─ When queue > 10000:
│  └─ Reject request with "system busy" (backpressure)

Cost control:
├─ Enforce max tokens per user
├─ Rate limit: 10 requests/min per user
├─ Queue priority: paying users first
```

---

## 🚀 Scaling

### 10x Traffic

```
Current: 100K concurrent → 7 GPUs
Scaled: 1M concurrent → 70 GPUs (linear scaling)

Optimizations:
├─ Quantization (fp16 → int8)
│  └─ 50% memory, 2x speed
│  └─ Result: 50 GPUs instead of 70
│
├─ Pruning (remove unimportant weights)
│  └─ 30% smaller model
│  └─ Result: 40 GPUs
│
├─ Mixture of Experts (conditional compute)
│  └─ Only activate relevant experts
│  └─ Result: 30 GPUs

Cost:
├─ Current: 7 * $2/hr = $14/hr
├─ Scaled: 30 * $2/hr = $60/hr
└─ Acceptable for 10x capacity
```

---

## 💭 Interview Questions

1. How would you handle a 1-hour model outage during peak traffic?
2. What if speculative decoding guesses wrong - how to recover?
3. How would you optimize for cost if token demand increases 10x?
4. How do you prevent a single user from consuming all GPU capacity?
5. What's the trade-off between accuracy and latency in model selection?

---

*Last Updated: 2026-05-28*
