# Production AI: Engineering for Scale

## 1. Inference Infrastructure

### 1.1 GPU Provisioning and Autoscaling

```python
class GPUProvisioner:
    def __init__(self):
        self.gpu_pool = []
        self.config = {
            "instance_type": "g5.12xlarge",
            "gpu_per_instance": 4,
            "min_instances": 1,
            "max_instances": 10,
            "target_gpu_utilization": 0.8
        }

    def estimate_required_gpus(self, requests_per_second: float, latency_target_ms: float, model_size_b: float) -> int:
        tokens_per_second_per_gpu = 1000 / (model_size_b * 2)  # Rough estimate
        required_tps = requests_per_second * 100  # Average tokens per request
        required_gpus = required_tps / tokens_per_second_per_gpu
        return max(1, int(np.ceil(required_gpus)))

    def calculate_request_capacity(self, total_gpus: int, model_size_b: float, latency_sla_ms: float) -> dict:
        tokens_per_second = total_gpus * 1000 / (model_size_b * 2)
        return {
            "max_requests_per_second": tokens_per_second / 100,
            "total_gpus": total_gpus,
            "estimated_latency_ms": latency_sla_ms
        }


class Autoscaler:
    def __init__(self, min_replicas=1, max_replicas=10, target_cpu=70):
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.target_cpu = target_cpu
        self.current_replicas = min_replicas
        self.metrics_history = []

    def record_metric(self, cpu_utilization: float):
        self.metrics_history.append(cpu_utilization)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

    def decide_scaling(self) -> dict:
        avg_cpu = np.mean(self.metrics_history[-10:]) if len(self.metrics_history) >= 10 else 0
        if avg_cpu > self.target_cpu and self.current_replicas < self.max_replicas:
            return {"action": "scale_up", "reason": f"CPU at {avg_cpu:.0f}%"}
        elif avg_cpu < self.target_cpu * 0.5 and self.current_replicas > self.min_replicas:
            return {"action": "scale_down", "reason": f"CPU at {avg_cpu:.0f}%"}
        return {"action": "none", "reason": "Stable"}

    def apply_scaling(self, action: str):
        if action == "scale_up":
            self.current_replicas += 1
        elif action == "scale_down":
            self.current_replicas -= 1
        return self.current_replicas
```

### 1.2 Inference Batching

```python
class DynamicBatcher:
    def __init__(self, max_batch_size=32, max_latency_ms=100, batch_window_ms=10):
        self.max_batch_size = max_batch_size
        self.max_latency_ms = max_latency_ms
        self.batch_window_ms = batch_window_ms
        self.queue = []
        self.last_batch_time = __import__('time').time()

    def add_request(self, request):
        self.queue.append(request)
        return self.try_batch()

    def try_batch(self):
        now = __import__('time').time()
        time_since_last = (now - self.last_batch_time) * 1000
        if len(self.queue) >= self.max_batch_size or time_since_last >= self.batch_window_ms:
            batch = self.queue[:self.max_batch_size]
            self.queue = self.queue[self.max_batch_size:]
            self.last_batch_time = now
            return batch
        return None

    def get_stats(self):
        return {
            "queue_size": len(self.queue),
            "max_batch_size": self.max_batch_size,
            "utilization": len(self.queue) / self.max_batch_size if self.queue else 0
        }


class ContinuousBatching:
    def __init__(self, model, max_batch_size=64):
        self.model = model
        self.max_batch_size = max_batch_size
        self.active_requests = []
        self.waiting_requests = []

    def submit(self, request):
        if len(self.active_requests) < self.max_batch_size:
            self.active_requests.append(request)
        else:
            self.waiting_requests.append(request)

    def step(self):
        if not self.active_requests:
            return
        batch_inputs = [r["input"] for r in self.active_requests]
        outputs = self.model.generate(batch_inputs)
        for req, output in zip(self.active_requests, outputs):
            req["output"] = output
            req["done"] = True
        self.active_requests = []
        self.fill_batch()

    def fill_batch(self):
        available = self.max_batch_size - len(self.active_requests)
        if available > 0 and self.waiting_requests:
            new_requests = self.waiting_requests[:available]
            self.waiting_requests = self.waiting_requests[available:]
            self.active_requests.extend(new_requests)

    def get_throughput(self, duration_seconds: float) -> float:
        completed = sum(1 for r in self.active_requests if r.get("done"))
        return completed / duration_seconds if duration_seconds > 0 else 0
```

## 2. Latency Optimization

### 2.1 KV Cache Management

```python
class KVCacheManager:
    def __init__(self, max_cache_size_gb=24):
        self.max_cache_size_gb = max_cache_size_gb
        self.cache_entries = {}
        self.total_cache_size = 0

    def estimate_cache_size(self, n_layers: int, n_heads: int, d_head: int, seq_len: int, dtype_bytes=2) -> float:
        bytes_per_layer = n_heads * d_head * seq_len * dtype_bytes * 2  # K + V
        total_bytes = bytes_per_layer * n_layers
        return total_bytes / (1024 ** 3)  # Convert to GB

    def can_allocate(self, request_id: str, size_gb: float) -> bool:
        if self.total_cache_size + size_gb > self.max_cache_size_gb:
            self.evict_lru()
        if self.total_cache_size + size_gb <= self.max_cache_size_gb:
            self.cache_entries[request_id] = {"size_gb": size_gb, "last_access": __import__('time').time()}
            self.total_cache_size += size_gb
            return True
        return False

    def evict_lru(self):
        if not self.cache_entries:
            return
        oldest = min(self.cache_entries, key=lambda k: self.cache_entries[k]["last_access"])
        self.total_cache_size -= self.cache_entries[oldest]["size_gb"]
        del self.cache_entries[oldest]

    def access(self, request_id: str):
        if request_id in self.cache_entries:
            self.cache_entries[request_id]["last_access"] = __import__('time').time()


class PagedAttention:
    def __init__(self, block_size=16, num_blocks=1024):
        self.block_size = block_size
        self.num_blocks = num_blocks
        self.free_blocks = list(range(num_blocks))
        self.allocated_blocks = {}

    def allocate_blocks(self, num_tokens: int, request_id: str) -> list:
        num_blocks_needed = (num_tokens + self.block_size - 1) // self.block_size
        if len(self.free_blocks) < num_blocks_needed:
            return []
        allocated = self.free_blocks[:num_blocks_needed]
        self.free_blocks = self.free_blocks[num_blocks_needed:]
        self.allocated_blocks[request_id] = allocated
        return allocated

    def free_blocks(self, request_id: str):
        if request_id in self.allocated_blocks:
            self.free_blocks.extend(self.allocated_blocks[request_id])
            self.free_blocks.sort()
            del self.allocated_blocks[request_id]

    def get_utilization(self) -> float:
        total = self.num_blocks
        used = total - len(self.free_blocks)
        return used / total
```

### 2.2 Inference Optimization Techniques

```python
class InferenceOptimizer:
    def __init__(self):
        self.techniques = {}

    def register_technique(self, name: str, speedup: float, memory_reduction: float, quality_impact: float):
        self.techniques[name] = {
            "speedup": speedup,
            "memory_reduction": memory_reduction,
            "quality_impact": quality_impact
        }

    def recommend(self, model_size_b: float, latency_target_ms: float, gpu_memory_gb: float) -> list:
        recommendations = []
        if model_size_b * 2 > gpu_memory_gb:
            recommendations.append("quantization_int4")
        if latency_target_ms < 50:
            recommendations.append("kv_cache_optimization")
        if model_size_b > 7:
            recommendations.append("tensor_parallelism")
        if latency_target_ms < 20:
            recommendations.append("speculative_decoding")
        recommendations.append("continuous_batching")
        return recommendations


# Flash Attention v2 implementation
class FlashAttention:
    def __init__(self, block_size_m=64, block_size_n=64):
        self.block_m = block_size_m
        self.block_n = block_size_n

    def forward(self, Q, K, V):
        batch, heads, seq_len, d_k = Q.shape
        output = np.zeros_like(Q)
        for i in range(0, seq_len, self.block_m):
            q_block = Q[:, :, i:i+self.block_m]
            row_max = np.full((batch, heads, q_block.shape[2], 1), -float('inf'))
            row_sum = np.zeros((batch, heads, q_block.shape[2], 1))
            output_block = np.zeros_like(q_block)
            for j in range(0, seq_len, self.block_n):
                k_block = K[:, :, j:j+self.block_n]
                v_block = V[:, :, j:j+self.block_n]
                scores = q_block @ k_block.transpose(0, 1, 3, 2) / np.sqrt(d_k)
                new_row_max = np.maximum(row_max, scores.max(axis=-1, keepdims=True))
                exp_scores = np.exp(scores - new_row_max)
                row_sum = row_sum * np.exp(row_max - new_row_max) + exp_scores.sum(axis=-1, keepdims=True)
                output_block = output_block * np.exp(row_max - new_row_max) + exp_scores @ v_block
                row_max = new_row_max
            output[:, :, i:i+self.block_m] = output_block / row_sum
        return output
```

## 3. Cost Optimization

### 3.1 Model Selection and Caching

```python
class CostOptimizer:
    def __init__(self):
        self.model_pricing = {
            "gpt-4": {"cost_per_1k_input": 0.03, "cost_per_1k_output": 0.06, "latency_ms": 2000},
            "gpt-3.5-turbo": {"cost_per_1k_input": 0.001, "cost_per_1k_output": 0.002, "latency_ms": 500},
            "claude-3-haiku": {"cost_per_1k_input": 0.00025, "cost_per_1k_output": 0.00125, "latency_ms": 300},
            "claude-3-sonnet": {"cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015, "latency_ms": 1000},
            "mistral-large": {"cost_per_1k_input": 0.002, "cost_per_1k_output": 0.006, "latency_ms": 800},
            "llama-3-70b": {"cost_per_1k_input": 0.001, "cost_per_1k_output": 0.002, "latency_ms": 600}
        }

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.model_pricing.get(model, {"cost_per_1k_input": 0.01, "cost_per_1k_output": 0.02})
        input_cost = (input_tokens / 1000) * pricing["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * pricing["cost_per_1k_output"]
        return input_cost + output_cost

    def select_model(self, task: str, input_tokens: int, output_tokens: int, quality_requirement: str = "high") -> str:
        if quality_requirement == "high":
            candidates = ["gpt-4", "claude-3-sonnet", "llama-3-70b"]
        elif quality_requirement == "medium":
            candidates = ["gpt-3.5-turbo", "mistral-large", "claude-3-haiku"]
        else:
            candidates = ["claude-3-haiku", "gpt-3.5-turbo"]

        costs = [(c, self.estimate_cost(c, input_tokens, output_tokens)) for c in candidates]
        return min(costs, key=lambda x: x[1])[0]


class ResponseCache:
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl_seconds

    def make_key(self, model: str, prompt: str, temperature: float = 0) -> str:
        import hashlib
        raw = f"{model}:{prompt}:{temperature}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str) -> str:
        entry = self.cache.get(key)
        if entry and (__import__('time').time() - entry["timestamp"]) < self.ttl:
            return entry["response"]
        if entry:
            del self.cache[key]
        return None

    def set(self, key: str, response: str):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache, key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest]
        self.cache[key] = {"response": response, "timestamp": __import__('time').time(), "hits": 0}

    def get_hit_rate(self) -> float:
        total = len(self.cache)
        if total == 0:
            return 0
        hits = sum(1 for v in self.cache.values() if v.get("hits", 0) > 0)
        return hits / total


class PromptCompressor:
    def __init__(self, max_compression_ratio=0.5):
        self.max_compression_ratio = max_compression_ratio

    def compress(self, prompt: str, min_ratio: float = 0.3) -> str:
        target_length = int(len(prompt) * max(min_ratio, self.max_compression_ratio))
        if len(prompt) <= target_length:
            return prompt
        lines = prompt.split('\n')
        compressed = []
        for line in lines:
            if len(line) > 100:
                words = line.split()
                compressed_line = ' '.join(words[:len(words)//2] + words[-len(words)//4:])
                compressed.append(compressed_line)
            else:
                compressed.append(line)
        result = '\n'.join(compressed)
        if len(result) > target_length:
            result = result[:target_length] + "..."
        return result

    def semantic_compress(self, prompt: str, llm) -> str:
        compression_prompt = f"Compress this prompt while preserving key information:\n{prompt}\n\nCompressed version:"
        compressed = llm(compression_prompt)
        return compressed
```

## 4. Safety and Security

### 4.1 Content Filtering and Guardrails

```python
class ContentFilter:
    def __init__(self):
        self.rules = []
        self.blocked_categories = set()

    def add_rule(self, name: str, pattern: str, action: str = "block"):
        import re
        self.rules.append({"name": name, "pattern": re.compile(pattern, re.IGNORECASE), "action": action})

    def check(self, text: str) -> dict:
        for rule in self.rules:
            if rule["pattern"].search(text):
                return {"allowed": rule["action"] == "flag", "rule": rule["name"], "action": rule["action"]}
        return {"allowed": True, "rule": None, "action": "allow"}

    def redact(self, text: str) -> str:
        for rule in self.rules:
            if rule["action"] == "redact":
                text = rule["pattern"].sub("[REDACTED]", text)
        return text


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60, tokens_per_minute: int = 100000):
        self.rpm_limit = requests_per_minute
        self.tpm_limit = tokens_per_minute
        self.request_window = []
        self.token_window = []

    def check_rate_limit(self, tokens: int = 0) -> dict:
        now = __import__('time').time()
        self.request_window = [t for t in self.request_window if now - t < 60]
        self.token_window = [t for t in self.token_window if now - t < 60]
        rpm = len(self.request_window)
        tpm = len(self.token_window)
        return {
            "allowed": rpm < self.rpm_limit and (tpm + tokens) < self.tpm_limit,
            "rpm": rpm,
            "rpm_limit": self.rpm_limit,
            "tpm": tpm + tokens,
            "tpm_limit": self.tpm_limit
        }

    def consume(self, tokens: int = 0):
        now = __import__('time').time()
        self.request_window.append(now)
        self.token_window.extend([now] * tokens)


class JailbreakDetector:
    def __init__(self):
        self.jailbreak_patterns = [
            "ignore previous instructions",
            "ignore all rules",
            "DAN",
            "do anything now",
            "you are free",
            "jailbroken",
            "roleplay as",
            "pretend to be",
            "override",
            "bypass"
        ]

    def detect(self, prompt: str) -> dict:
        prompt_lower = prompt.lower()
        matches = []
        for pattern in self.jailbreak_patterns:
            if pattern.lower() in prompt_lower:
                matches.append(pattern)
        return {"detected": len(matches) > 0, "patterns": matches, "severity": len(matches)}

    def score_prompt(self, prompt: str) -> float:
        prompt_lower = prompt.lower()
        score = 0.0
        score += prompt_lower.count("ignore") * 0.1
        score += prompt_lower.count("override") * 0.2
        score += prompt_lower.count("pretend") * 0.1
        score += prompt_lower.count("roleplay") * 0.1
        score += len([p for p in self.jailbreak_patterns if p in prompt_lower]) * 0.3
        return min(1.0, score)
```

## 5. Evaluation

### 5.1 Automated Metrics

```python
class NLPEvaluator:
    def bleu_score(self, reference: str, candidate: str, max_n: int = 4) -> float:
        ref_tokens = reference.split()
        cand_tokens = candidate.split()
        precisions = []
        for n in range(1, max_n + 1):
            ref_ngrams = set(zip(*[ref_tokens[i:] for i in range(n)]))
            cand_ngrams = list(zip(*[cand_tokens[i:] for i in range(n)]))
            matches = sum(1 for ng in cand_ngrams if ng in ref_ngrams)
            total = len(cand_ngrams) if cand_ngrams else 1
            precisions.append(matches / total)
        bp = min(1, len(cand_tokens) / len(ref_tokens)) if ref_tokens else 1
        if min(precisions) == 0:
            return 0.0
        geo_mean = np.exp(np.mean([np.log(p) for p in precisions]))
        return bp * geo_mean

    def rouge_score(self, reference: str, candidate: str) -> dict:
        ref_sentences = reference.split('.')
        cand_sentences = candidate.split('.')
        ref_words = set(reference.lower().split())
        cand_words = set(candidate.lower().split())
        overlap = ref_words & cand_words
        precision = len(overlap) / len(cand_words) if cand_words else 0
        recall = len(overlap) / len(ref_words) if ref_words else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        return {"rouge-1": {"p": precision, "r": recall, "f1": f1}}

    def meteor_score(self, reference: str, candidate: str) -> float:
        ref_words = reference.lower().split()
        cand_words = candidate.lower().split()
        matches = sum(1 for w in cand_words if w in ref_words)
        precision = matches / len(cand_words) if cand_words else 0
        recall = matches / len(ref_words) if ref_words else 0
        if precision + recall == 0:
            return 0
        f_mean = 10 * precision * recall / (9 * precision + recall)
        chunks = self.count_chunks(ref_words, cand_words)
        penalty = 0.5 * (chunks / matches) if matches > 0 else 1
        return f_mean * (1 - penalty)

    def count_chunks(self, ref, cand):
        chunks = 0
        in_chunk = False
        cand_set = set(cand)
        for w in ref:
            if w in cand_set:
                if not in_chunk:
                    chunks += 1
                    in_chunk = True
            else:
                in_chunk = False
        return chunks


class LLMAsJudge:
    def __init__(self, judge_llm):
        self.judge = judge_llm

    def evaluate(self, prompt: str, response: str, criteria: list) -> dict:
        results = {}
        for criterion in criteria:
            eval_prompt = f"""
You are evaluating an AI response.
Criterion: {criterion}
Prompt: {prompt}
Response: {response}

Rate the response on this criterion from 1-5:
"""
            score_text = self.judge(eval_prompt)
            try:
                score = float(score_text.strip()[0])
            except (ValueError, IndexError):
                score = 3.0
            results[criterion] = score
        return results

    def evaluate_pairwise(self, prompt: str, response_a: str, response_b: str) -> str:
        eval_prompt = f"""
Compare these two responses:
Prompt: {prompt}
Response A: {response_a}
Response B: {response_b}

Which is better? Respond with "A", "B", or "Tie":
"""
        return self.judge(eval_prompt).strip()
```

## 6. RAG Production

### 6.1 Chunking Strategies

```python
class ChunkingStrategy:
    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def fixed_size_chunks(self, text: str) -> list:
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunk = ' '.join(words[start:end])
            chunks.append({"text": chunk, "start": start, "end": end})
            start += self.chunk_size - self.overlap
        return chunks

    def sentence_chunks(self, text: str) -> list:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        for sentence in sentences:
            words = sentence.split()
            if current_length + len(words) > self.chunk_size and current_chunk:
                chunks.append({"text": ' '.join(current_chunk)})
                current_chunk = current_chunk[-self.overlap:] if self.overlap else []
                current_length = sum(len(c.split()) for c in current_chunk)
            current_chunk.append(sentence)
            current_length += len(words)
        if current_chunk:
            chunks.append({"text": ' '.join(current_chunk)})
        return chunks

    def semantic_chunks(self, text: str, embedding_fn) -> list:
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_embedding = None
        for para in paragraphs:
            if not para.strip():
                continue
            para_embedding = embedding_fn(para)
            if current_embedding is not None:
                similarity = np.dot(current_embedding, para_embedding) / (np.linalg.norm(current_embedding) * np.linalg.norm(para_embedding))
                if similarity > 0.8 and len(current_chunk.split()) + len(para.split()) < self.chunk_size * 2:
                    current_chunk += "\n\n" + para
                    continue
            if current_chunk:
                chunks.append({"text": current_chunk})
            current_chunk = para
            current_embedding = para_embedding
        if current_chunk:
            chunks.append({"text": current_chunk})
        return chunks
```

### 6.2 Embedding Selection and Hybrid Search

```python
class EmbeddingSelector:
    def __init__(self):
        self.models = {
            "text-embedding-3-small": {"dimensions": 1536, "cost_per_1k": 0.002, "quality": "high"},
            "text-embedding-3-large": {"dimensions": 3072, "cost_per_1k": 0.013, "quality": "best"},
            "bge-large-en-v1.5": {"dimensions": 1024, "cost_per_1k": 0.0, "quality": "high"},
            "e5-mistral-7b-instruct": {"dimensions": 4096, "cost_per_1k": 0.0, "quality": "best"}
        }

    def select(self, corpus_size: int, latency_sla_ms: int, budget: float) -> str:
        candidates = []
        for name, info in self.models.items():
            if info["cost_per_1k"] == 0 or (corpus_size * info["cost_per_1k"] / 1000) <= budget:
                candidates.append((name, info))
        if not candidates:
            return "text-embedding-3-small"
        return min(candidates, key=lambda x: x[1]["dimensions"])[0]


class HybridSearch:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.documents = []

    def index(self, docs: list, embeddings: list):
        self.documents = [{"text": d, "embedding": e} for d, e in zip(docs, embeddings)]

    def search(self, query: str, query_embedding: list, top_k: int = 10) -> list:
        bm25_scores = self.bm25_search(query)
        vector_scores = self.vector_search(query_embedding)
        combined = []
        for i in range(len(self.documents)):
            bm25 = bm25_scores.get(i, 0)
            vector = vector_scores.get(i, 0)
            combined.append({
                "index": i,
                "text": self.documents[i]["text"],
                "score": self.alpha * vector + (1 - self.alpha) * bm25
            })
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]

    def bm25_search(self, query: str) -> dict:
        query_terms = query.lower().split()
        scores = {}
        for i, doc in enumerate(self.documents):
            doc_words = doc["text"].lower().split()
            score = 0
            for term in query_terms:
                tf = doc_words.count(term)
                idf = np.log((len(self.documents) + 1) / (1 + sum(1 for d in self.documents if term in d["text"].lower())))
                score += (tf * idf) / (tf + 1.5 * (1 - 0.75 + 0.75 * len(doc_words) / 100))
            scores[i] = score
        return scores

    def vector_search(self, query_embedding: list) -> dict:
        scores = {}
        for i, doc in enumerate(self.documents):
            sim = np.dot(query_embedding, doc["embedding"]) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc["embedding"]))
            scores[i] = sim
        return scores


class Reranker:
    def __init__(self, reranker_fn):
        self.reranker = reranker_fn

    def rerank(self, query: str, candidates: list, top_k: int = 5) -> list:
        scored = []
        for c in candidates:
            relevance = self.reranker(query, c["text"])
            scored.append({"text": c["text"], "original_score": c["score"], "rerank_score": relevance})
        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_k]

    def cross_encoder_score(self, query: str, passage: str) -> float:
        import hashlib
        return float(hashlib.md5(f"{query}:{passage}".encode()).hexdigest()[:8], 16) / 10**8
```

## 7. CI/CD for ML

### 7.1 Model CI/CD Pipeline

```python
class ModelCICDPipeline:
    def __init__(self):
        self.stages = []

    def add_stage(self, name: str, script: str, timeout_minutes: int = 30):
        self.stages.append({"name": name, "script": script, "timeout": timeout_minutes})

    def generate_github_actions(self) -> str:
        yaml = """name: ML Pipeline CI/CD
on:
  push:
    branches: [main]
    paths:
      - 'models/**'
      - 'data/**'
pull_request:
  branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
"""
        for stage in self.stages:
            yaml += f"""      - name: {stage['name']}
        run: {stage['script']}
"""
        return yaml

    def generate_gitlab_ci(self) -> str:
        yaml = "stages:\n"
        for stage in self.stages:
            yaml += f"  - {stage['name']}\n"
        for stage in self.stages:
            yaml += f"""
{stage['name']}:
  stage: {stage['name']}
  script:
    - {stage['script']}
  timeout: {stage['timeout']}m
"""
        return yaml


class DataValidationCI:
    def __init__(self):
        self.checks = []

    def add_check(self, name: str, check_fn: callable):
        self.checks.append({"name": name, "fn": check_fn})

    def run_all(self, data) -> dict:
        results = {}
        for check in self.checks:
            try:
                passed = check["fn"](data)
                results[check["name"]] = {"passed": passed, "error": None}
            except Exception as e:
                results[check["name"]] = {"passed": False, "error": str(e)}
        return results


class ModelValidationGate:
    def __init__(self, metrics_thresholds: dict):
        self.thresholds = metrics_thresholds

    def evaluate(self, metrics: dict) -> dict:
        results = {}
        all_passed = True
        for metric, threshold in self.thresholds.items():
            value = metrics.get(metric, 0)
            passed = value >= threshold
            results[metric] = {"value": value, "threshold": threshold, "passed": passed}
            if not passed:
                all_passed = False
        results["all_passed"] = all_passed
        return results

    def generate_report(self, metrics: dict) -> str:
        evaluation = self.evaluate(metrics)
        report = "# Model Validation Report\n\n"
        report += "## Metrics\n\n"
        report += "| Metric | Value | Threshold | Passed |\n"
        report += "|--------|-------|-----------|--------|\n"
        for metric, info in evaluation.items():
            if metric != "all_passed":
                report += f"| {metric} | {info['value']:.4f} | {info['threshold']:.4f} | {'PASS' if info['passed'] else 'FAIL'} |\n"
        report += f"\n## Overall: {'PASSED' if evaluation['all_passed'] else 'FAILED'}\n"
        return report
```

## 8. Production Monitoring

### 8.1 Real-Time Monitoring

```python
class ProductionMonitor:
    def __init__(self):
        self.slos = {}
        self.incidents = []

    def define_slo(self, name: str, target: float, window_minutes: int = 60):
        self.slos[name] = {"target": target, "window": window_minutes, "measurements": []}

    def record_measurement(self, slo_name: str, value: float):
        if slo_name in self.slos:
            self.slos[slo_name]["measurements"].append({"value": value, "timestamp": __import__('time').time()})

    def check_slo(self, slo_name: str) -> dict:
        slo = self.slos.get(slo_name)
        if not slo:
            return {"error": "SLO not found"}
        cutoff = __import__('time').time() - slo["window"] * 60
        recent = [m for m in slo["measurements"] if m["timestamp"] > cutoff]
        if not recent:
            return {"status": "unknown", "measured": 0}
        good = sum(1 for m in recent if m["value"] >= slo["target"])
        ratio = good / len(recent)
        return {"status": "healthy" if ratio >= 0.99 else "warning", "sli": ratio, "target": slo["target"], "measurements": len(recent)}

    def create_incident(self, title: str, severity: str, description: str):
        incident = {
            "id": len(self.incidents) + 1,
            "title": title,
            "severity": severity,
            "description": description,
            "created_at": __import__('time').time(),
            "resolved_at": None
        }
        self.incidents.append(incident)
        return incident

    def resolve_incident(self, incident_id: int):
        for incident in self.incidents:
            if incident["id"] == incident_id:
                incident["resolved_at"] = __import__('time').time()
                return True
        return False
```

### 8.2 Alerting

```python
class AlertManager:
    def __init__(self):
        self.rules = []
        self.alerts = []

    def add_rule(self, name: str, metric: str, condition: str, threshold: float, severity: str = "warning"):
        self.rules.append({"name": name, "metric": metric, "condition": condition, "threshold": threshold, "severity": severity})

    def evaluate(self, metrics: dict) -> list:
        triggered = []
        for rule in self.rules:
            value = metrics.get(rule["metric"])
            if value is None:
                continue
            if rule["condition"] == ">" and value > rule["threshold"]:
                triggered.append(rule)
            elif rule["condition"] == "<" and value < rule["threshold"]:
                triggered.append(rule)
            elif rule["condition"] == "==" and value == rule["threshold"]:
                triggered.append(rule)
        for rule in triggered:
            self.alerts.append({
                "rule": rule["name"],
                "value": metrics[rule["metric"]],
                "threshold": rule["threshold"],
                "timestamp": __import__('time').time(),
                "acknowledged": False
            })
        return triggered

    def acknowledge(self, alert_index: int):
        if alert_index < len(self.alerts):
            self.alerts[alert_index]["acknowledged"] = True

    def get_unacknowledged(self) -> list:
        return [a for a in self.alerts if not a["acknowledged"]]
```

## 9. Exercise Problems

**Problem 1**: Implement a dynamic batching server that collects requests for 10ms or until batch size reaches 32, then processes them. Measure throughput vs latency tradeoff.

**Problem 2**: Build a cost optimization system that routes queries to different model tiers based on task complexity, estimated tokens, and latency requirements.

**Problem 3**: Implement a hybrid search system combining BM25 and vector similarity. Tune the alpha parameter for different query types.

**Problem 4**: Create a comprehensive monitoring dashboard tracking P50/P95/P99 latency, error rates, token usage, and cost per request.

**Problem 5**: Build a CI/CD pipeline for ML models that validates data quality, runs evaluation on a held-out set, checks metric thresholds, and promotes to staging only if all gates pass.

---

## Related

- [Databases](../../08-databases/) — Vector search, embeddings storage
- [Python Backend](../../03-backend/) — ML inference APIs
- [Cloud Platforms](../../05-cloud/) — GPU/TPU infrastructure
- [Data Engineering](../../02-data-engineering/) — Training data pipelines
- [Performance Engineering](../../18-performance-engineering/) — Model optimization
