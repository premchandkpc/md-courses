---
title: LLM Engineering Fundamentals
topic: 01-ai-ml
difficulty: intermediate
time: 30m
paths:
  - ai-ml
---

# LLM Engineering Fundamentals

---

## LAYER 1: Beginner's Mental Model 🧠

### What are LLMs?

Imagine a **very smart autocomplete**:
- Google Search: "What is..." → suggests completions
- Phone keyboard: Type "hel" → suggests "hello"
- GitHub Copilot: `function add(` → suggests `{return a + b;}`

**LLMs (Large Language Models):** Predict the next word based on previous words.

```
Predict next word:
Input: "The capital of France is"
Output: "Paris" (probability 95%)

Input: "Two plus two equals"
Output: "four" (probability 99%)

Input: "To make a sandwich, first"
Output: "gather ingredients" (probability 60%)
```

LLMs are **really good at this** because:
1. Trained on billions of text examples
2. Learn patterns (grammar, facts, reasoning)
3. Scale: 70B+ parameters = very smart

### Why LLMs Matter

**Before LLMs (2022):**
- Search: keyword-based, 50% relevance
- Writing: templates, copy-paste
- Coding: Stack Overflow + manual
- Translation: 85% accuracy, human review needed

**With LLMs (2024+):**
- Search: semantic understanding, 90% relevance
- Writing: AI generates drafts, 30% faster
- Coding: AI completes code, 40% faster
- Translation: 97% accuracy, no review needed

**Real impact:**
- OpenAI: $13B valuation in 2 years
- Google: Rewriting entire search engine (Gemini)
- Stripe: Using Claude to generate fraud detection rules
- Anthropic: $20B valuation (latest)

---

## Architecture Overview

```mermaid
graph LR
    PT["Pre-Training<br/>(Next Token Prediction)"] --> FT["Fine-Tuning<br/>(Instruction Tuning)"]
    FT --> RL["RLHF /<br/>DPO Alignment"]
    RL --> DEP["Model<br/>Deployment"]
    DEP --> INF["Inference<br/>(Token Generation)"]
    INF --> PROMPT["Prompt<br/>Processing"]
    PROMPT --> GEN["Auto-Regressive<br/>Decoding"]
    GEN --> KV["KV Cache<br/>(Past Keys/Values)"]
    style PT fill:#4a8bc2
    style FT fill:#2d5a7b
    style RL fill:#6f42c1
    style DEP fill:#3a7ca5
    style INF fill:#c73e1d
    style PROMPT fill:#e8912e
    style GEN fill:#3fb950
    style KV fill:#2d5a7b
```

## 1. LLM Architecture Taxonomy

### 1.1 Decoder-Only Architecture

The dominant architecture for modern LLMs (GPT, Llama, Mistral, DeepSeek). Processes tokens left-to-right with causal attention.

```
Input:  [The] [cat] [sat] [on]
           ↓     ↓     ↓     ↓
      ┌─────────────────────────┐
      │    Decoder Block × N    │
      │  (Self-Attention + FFN) │
      └─────────────────────────┘
           ↓     ↓     ↓     ↓
Output: [cat] [sat] [on] [the]
```

#### Step-by-Step

1. **Tokenization**: Input text is split into tokens (subwords/words), each mapped to an ID via vocabulary.
2. **Embedding**: Token IDs are converted to dense vectors (embeddings) of dimension d_model (e.g., 4096 for 70B model).
3. **Positional Encoding**: Positional information added to embeddings so model knows word order (position 0 vs position 100).
4. **Attention Mechanism**: Each token attends to all previous tokens (causal mask prevents looking ahead), computing weighted context.
5. **Feed-Forward Network**: Attention output passed through MLPs (dense layers + activation) for non-linear transformation.
6. **Output Prediction**: Final layer logits over vocabulary, softmax produces probabilities for next token, argmax selects token.

#### Code Example

```python
import numpy as np
from typing import Tuple
import torch
import torch.nn as nn

class DecoderOnlyLLM(nn.Module):
    """Simplified Decoder-Only LLM Architecture."""
    
    def __init__(self, vocab_size: int = 50000, d_model: int = 768,
                 n_heads: int = 12, n_layers: int = 12, d_ff: int = 3072):
        super().__init__()
        self.vocab_size = vocab_size
        self.d_model = d_model
        
        # Step 1-2: Token embedding
        self.embedding = nn.Embedding(vocab_size, d_model)
        
        # Step 3: Positional embedding (max 4096 tokens)
        self.pos_embedding = nn.Embedding(4096, d_model)
        
        # Step 4-5: Decoder blocks (repeated N times)
        self.decoder_blocks = nn.ModuleList([
            DecoderBlock(d_model, n_heads, d_ff)
            for _ in range(n_layers)
        ])
        
        # Step 6: Output layer
        self.output_norm = nn.RMSNorm(d_model)
        self.output_proj = nn.Linear(d_model, vocab_size)
    
    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """
        Args:
            token_ids: Shape (batch_size, seq_len)
        Returns:
            logits: Shape (batch_size, seq_len, vocab_size)
        """
        batch_size, seq_len = token_ids.shape
        
        # Step 1-3: Embedding + Positional encoding
        x = self.embedding(token_ids)  # (batch, seq_len, d_model)
        positions = torch.arange(seq_len, device=token_ids.device)
        x = x + self.pos_embedding(positions)  # Broadcast positional
        
        # Step 4-5: Pass through decoder blocks
        for decoder_block in self.decoder_blocks:
            x = decoder_block(x)  # (batch, seq_len, d_model)
        
        # Step 6: Normalize and project to vocabulary
        x = self.output_norm(x)  # (batch, seq_len, d_model)
        logits = self.output_proj(x)  # (batch, seq_len, vocab_size)
        
        return logits

class DecoderBlock(nn.Module):
    """Single Decoder Block with Self-Attention + Feed-Forward."""
    
    def __init__(self, d_model: int, n_heads: int, d_ff: int):
        super().__init__()
        self.self_attention = MultiHeadSelfAttention(d_model, n_heads)
        self.norm1 = nn.RMSNorm(d_model)
        self.ff = FeedForwardNetwork(d_model, d_ff)
        self.norm2 = nn.RMSNorm(d_model)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Self-attention with residual connection
        x = x + self.self_attention(self.norm1(x))
        # Feed-forward with residual connection
        x = x + self.ff(self.norm2(x))
        return x

class MultiHeadSelfAttention(nn.Module):
    def __init__(self, d_model: int, n_heads: int):
        super().__init__()
        assert d_model % n_heads == 0
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_out = nn.Linear(d_model, d_model)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, d_model = x.shape
        
        # Linear projections
        Q = self.W_q(x).reshape(batch_size, seq_len, self.n_heads, self.d_head)
        K = self.W_k(x).reshape(batch_size, seq_len, self.n_heads, self.d_head)
        V = self.W_v(x).reshape(batch_size, seq_len, self.n_heads, self.d_head)
        
        # Scaled dot-product attention with causal mask
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.d_head ** 0.5)
        
        # Causal mask: prevent attending to future tokens
        mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
        scores = scores.masked_fill(mask, float('-inf'))
        
        attn_weights = torch.softmax(scores, dim=-1)
        attn_output = torch.matmul(attn_weights, V)
        
        # Reshape and project
        attn_output = attn_output.reshape(batch_size, seq_len, d_model)
        return self.W_out(attn_output)

class FeedForwardNetwork(nn.Module):
    def __init__(self, d_model: int, d_ff: int):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.activation = nn.GELU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear2(self.activation(self.linear1(x)))

# Usage example
model = DecoderOnlyLLM(vocab_size=50000, d_model=768, n_heads=12, n_layers=12)
token_ids = torch.randint(0, 50000, (2, 100))  # (batch=2, seq=100)
logits = model(token_ids)  # (batch=2, seq=100, vocab=50000)

# Step 6: Sample next token
last_token_logits = logits[:, -1, :]  # Get last position
probs = torch.softmax(last_token_logits, dim=-1)
next_token_id = torch.argmax(probs, dim=-1)
print(f"Next token ID: {next_token_id}")
```

#### Real-World Scenario

OpenAI's GPT-4 (decoder-only): User inputs "Tell me a joke." (1) Tokenized to [Tell, me, a, joke] → IDs [1234, 5678, 9012, 3456]. (2) Embeddings created (4096-dim vectors from 96-layer model). (3) Positional info added (token 0 vs token 3). (4) 96 decoder blocks process: "Tell" attends to "Tell", "me" attends to "Tell" + "me", "joke" attends to all 3 preceding tokens (causal). (5) FFNs expand 4096→10944 dims for reasoning, collapse back to 4096. (6) Output layer: logits over 100K tokens, softmax gives probs. Model predicts "Why" (91% prob). Repeat 100x to generate full joke. KV cache optimization skips recomputing past tokens' attention.

```python
import numpy as np

class DecoderOnlyBlock:
    def __init__(self, d_model, n_heads, d_ff):
        self.attention = MultiHeadAttention(d_model, n_heads)
        self.norm1 = RMSNorm(d_model)
        self.ff = SwiGLUFFN(d_model, d_ff)
        self.norm2 = RMSNorm(d_model)

    def forward(self, x, mask=None):
        residual = x
        x = self.norm1.forward(x)
        attn_out, _ = self.attention.forward(x, x, x, mask)
        x = residual + attn_out

        residual = x
        x = self.norm2.forward(x)
        ff_out = self.ff.forward(x)
        x = residual + ff_out
        return x
```

### 1.2 Encoder-Only Architecture

Bidirectional attention for understanding tasks (BERT, RoBERTa, DeBERTa).

```
Input:  [The] [cat] [sat] [on] [the] [mat]
           ↓     ↓     ↓     ↓    ↓     ↓
      ┌─────────────────────────────────────┐
      │       Encoder Block × N             │
      │  (Bidirectional Self-Attention)     │
      └─────────────────────────────────────┘
           ↓     ↓     ↓     ↓    ↓     ↓
Output: Contextual embeddings for each token
```

```python
class EncoderOnlyBlock:
    def __init__(self, d_model, n_heads, d_ff):
        self.attention = MultiHeadAttention(d_model, n_heads)
        self.norm1 = LayerNorm(d_model)
        self.ff = FeedForward(d_model, d_ff)
        self.norm2 = LayerNorm(d_model)

    def forward(self, x, mask=None):
        # Bidirectional (no causal mask)
        attn_out, _ = self.attention.forward(x, x, x, mask)
        x = self.norm1.forward(x + attn_out)
        ff_out = self.ff.forward(x)
        x = self.norm2.forward(x + ff_out)
        return x
```

### 1.3 Encoder-Decoder Architecture

Used for sequence-to-sequence tasks (T5, BART, original Transformer).

```
Input:  [Translate] [hello] [to] [French]
              ↓
        ┌──────────┐
        │ Encoder  │
        │ (Bidir)  │
        └──────────┘
              ↓
        ┌──────────┐
        │ Decoder  │
        │ (Causal) │
        └──────────┘
              ↓
Output: [Bonjour] [<eos>]
```

```python
class EncoderDecoderBlock:
    def __init__(self, d_model, n_heads, d_ff):
        self.encoder = EncoderOnlyBlock(d_model, n_heads, d_ff)
        self.decoder = DecoderOnlyBlock(d_model, n_heads, d_ff)
        # Cross-attention in decoder
        self.cross_attn = MultiHeadAttention(d_model, n_heads)
        self.cross_norm = LayerNorm(d_model)

    def forward(self, x_enc, x_dec, enc_mask=None, dec_mask=None):
        enc_out = self.encoder.forward(x_enc, enc_mask)
        dec_out = self.decoder.forward(x_dec, dec_mask)
        # Cross-attention: Q from decoder, K,V from encoder
        cross_out, _ = self.cross_attn.forward(dec_out, enc_out, enc_out, enc_mask)
        dec_out = self.cross_norm.forward(dec_out + cross_out)
        return enc_out, dec_out
```

## 2. Tokenization

### 2.1 Byte-Pair Encoding (BPE)

Used by GPT models. Iteratively merges the most frequent pair of tokens.

```python
from collections import Counter

class BPE:
    def __init__(self, vocab_size=32000):
        self.vocab_size = vocab_size
        self.merges = {}
        self.vocab = {}
        self.bytes_to_unicode = {}

    def train(self, corpus):
        # Initialize with byte-level tokens
        tokens = [list(word.encode('utf-8')) for word in corpus]

        # Count pairs
        pairs = Counter()
        for word_tokens in tokens:
            for i in range(len(word_tokens) - 1):
                pairs[(word_tokens[i], word_tokens[i+1])] += 1

        # Iteratively merge most frequent pairs
        for i in range(self.vocab_size - 256):  # 256 byte tokens
            if not pairs:
                break
            most_common = pairs.most_common(1)[0][0]
            self.merges[most_common] = i + 256

            # Apply merge
            new_tokens = []
            for word_tokens in tokens:
                new_word = []
                j = 0
                while j < len(word_tokens):
                    if (j < len(word_tokens) - 1 and
                        (word_tokens[j], word_tokens[j+1]) == most_common):
                        new_word.append(i + 256)
                        j += 2
                    else:
                        new_word.append(word_tokens[j])
                        j += 1
                new_tokens.append(new_word)
            tokens = new_tokens

            # Recompute pairs
            pairs = Counter()
            for word_tokens in tokens:
                for j in range(len(word_tokens) - 1):
                    pairs[(word_tokens[j], word_tokens[j+1])] += 1

        self.build_vocab()

    def build_vocab(self):
        # Byte tokens
        self.vocab = {i: bytes([i]) for i in range(256)}
        # Merged tokens
        for (a, b), idx in self.merges.items():
            self.vocab[idx] = self.vocab[a] + self.vocab[b]

    def encode(self, text):
        tokens = list(text.encode('utf-8'))
        while len(tokens) >= 2:
            # Find best pair to merge
            pairs = [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]
            mergeable = [(self.merges.get(p, float('inf')), i)
                        for i, p in enumerate(pairs)]
            best_score, best_pos = min(mergeable)

            if best_score == float('inf'):
                break

            # Apply merge
            i = best_pos
            tokens = tokens[:i] + [best_score] + tokens[i+2:]

        return tokens

    def decode(self, token_ids):
        return b''.join(self.vocab[t] for t in token_ids).decode('utf-8', errors='replace')
```

### 2.2 WordPiece

Used by BERT. Greedily builds tokens using maximum likelihood.

```python
class WordPiece:
    def __init__(self, vocab_size=30000):
        self.vocab_size = vocab_size
        self.vocab = set()
        self.scores = {}

    def train(self, corpus):
        # Start with characters
        char_counts = Counter()
        for word in corpus:
            for char in word:
                char_counts[char] += 1

        self.vocab = set(char_counts.keys())

        # Initialize with unigram scores
        total_chars = sum(char_counts.values())
        self.scores = {c: count/total_chars for c, count in char_counts.items()}

        # Greedily add most likely merges
        for _ in range(self.vocab_size - len(self.vocab)):
            pairs = Counter()
            for word in corpus:
                tokens = self.tokenize(word)
                for i in range(len(tokens) - 1):
                    pairs[(tokens[i], tokens[i+1])] += 1

            if not pairs:
                break

            # Find pair with highest score
            best_pair = max(pairs, key=lambda p: pairs[p])
            new_token = best_pair[0] + best_pair[1]
            self.vocab.add(new_token)
            self.scores[new_token] = self.scores.get(best_pair[0], 0) + \
                                     self.scores.get(best_pair[1], 0)

    def tokenize(self, word):
        # Greedy longest-match from left
        tokens = []
        i = 0
        while i < len(word):
            for j in range(len(word), i, -1):
                if word[i:j] in self.vocab:
                    tokens.append(word[i:j])
                    i = j
                    break
            else:
                tokens.append('[UNK]')
                i += 1
        return tokens
```

### 2.3 SentencePiece / Unigram

Used by Llama, T5. Based on unigram language model with regularization.

```python
class UnigramTokenizer:
    """
    Unigram tokenization: finds the most probable tokenization
    assuming each token is independently generated.
    """
    def __init__(self, vocab_size=32000):
        self.vocab_size = vocab_size
        self.token_scores = {}  # log probability of each token
        self.vocab = set()

    def train(self, corpus, num_iterations=10):
        # Start with all character n-grams
        ngram_counts = Counter()
        for word in corpus:
            for i in range(len(word)):
                for j in range(i+1, len(word)+1):
                    ngram_counts[word[i:j]] += 1

        # Keep top-k by frequency as seed vocabulary
        top_ngrams = ngram_counts.most_common(self.vocab_size * 2)
        self.vocab = set(t[0] for t in top_ngrams)

        # EM algorithm iterations
        for iteration in range(num_iterations):
            # E-step: compute expected counts
            token_counts = Counter()
            for word in corpus:
                tokenization = self.viterbi_segment(word)
                for token in tokenization:
                    token_counts[token] += 1

            # M-step: update scores
            total = sum(token_counts.values())
            for token in self.vocab:
                if token_counts[token] > 0:
                    self.token_scores[token] = np.log(token_counts[token] / total)

            # Prune vocabulary
            if len(self.vocab) > self.vocab_size:
                sorted_vocab = sorted(self.vocab,
                    key=lambda t: self.token_scores.get(t, -np.inf))
                self.vocab = set(sorted_vocab[-self.vocab_size:])

    def viterbi_segment(self, word):
        # Viterbi algorithm for optimal segmentation
        n = len(word)
        best_score = [float('-inf')] * (n + 1)
        best_path = [-1] * (n + 1)
        best_score[0] = 0

        for i in range(1, n + 1):
            for j in range(i):
                token = word[j:i]
                if token in self.vocab:
                    score = best_score[j] + self.token_scores.get(token, -100)
                    if score > best_score[i]:
                        best_score[i] = score
                        best_path[i] = j

        # Backtrack
        tokens = []
        pos = n
        while pos > 0:
            start = best_path[pos]
            tokens.append(word[start:pos])
            pos = start

        return list(reversed(tokens))
```

### 2.4 Tokenizer Comparison

| Tokenizer | Vocab Building | Encoding | Used In | Special Features |
|-----------|---------------|----------|---------|-----------------|
| BPE | Merge most frequent pair | Iterative merge | GPT, GPT-2, Codex | Byte-level, fixed vocab |
| WordPiece | Maximize likelihood | Greedy LTR | BERT, DistilBERT | ## prefix for subwords |
| Unigram | EM algorithm | Viterbi | T5, Llama, XLNet | Probabilistic, regularization |
| SentencePiece | BPE or Unigram | Raw text | Llama, T5 | No pretokenization needed |

## 3. Pre-training Objectives

### 3.1 Next Token Prediction (Autoregressive LM)

```python
def autoregressive_loss(logits, targets):
    """
    Standard next-token prediction loss.
    Used by GPT, Llama, Mistral, DeepSeek.
    """
    # logits: (seq_len, vocab_size)
    # targets: (seq_len,) — shift right by 1
    log_probs = logits - np.log(np.sum(np.exp(logits), axis=-1, keepdims=True))
    token_log_probs = log_probs[np.arange(len(targets)), targets]
    return -np.mean(token_log_probs)
```

### 3.2 Masked Language Modeling (MLM)

```python
def mlm_loss(logits, targets, masked_positions):
    """
    Masked Language Model loss.
    Used by BERT, RoBERTa.
    Only compute loss on masked tokens.
    """
    log_probs = logits - np.log(np.sum(np.exp(logits), axis=-1, keepdims=True))
    # Only masked positions contribute to loss
    mask = np.zeros(len(targets), dtype=bool)
    mask[masked_positions] = True
    token_log_probs = log_probs[np.arange(len(targets)), targets]
    masked_loss = -token_log_probs[mask]
    return np.mean(masked_loss)


def create_mlm_input(tokens, mask_token_id, mask_prob=0.15):
    """
    BERT-style masking:
    - 80% replace with [MASK]
    - 10% replace with random token
    - 10% unchanged
    """
    input_tokens = tokens.copy()
    labels = np.full_like(tokens, -100)  # -100 = ignore in loss
    masked_positions = []

    for i in range(len(tokens)):
        if np.random.rand() < mask_prob:
            labels[i] = tokens[i]
            masked_positions.append(i)
            p = np.random.rand()
            if p < 0.8:
                input_tokens[i] = mask_token_id
            elif p < 0.9:
                input_tokens[i] = np.random.randint(0, 32000)

    return input_tokens, labels, masked_positions
```

### 3.3 Prefix LM / Span Corruption

```python
def prefix_lm_loss(encoder_logits, decoder_logits, encoder_targets, decoder_targets):
    """
    Prefix LM: encode prefix with bidirectional attention,
    then autoregressively predict the rest.
    Used by T5 (span corruption), GLM, ChatGLM.
    """
    # Encoder loss (bidirectional — all tokens)
    enc_loss = autoregressive_loss(encoder_logits, encoder_targets)

    # Decoder loss (causal)
    dec_loss = autoregressive_loss(decoder_logits, decoder_targets)

    return enc_loss + dec_loss


def create_span_corruption(tokens, sentinel_tokens, corruption_rate=0.15, mean_span_len=3):
    """
    T5-style span corruption:
    Replace contiguous spans with sentinel tokens.
    """
    input_tokens = tokens.copy()
    target_tokens = []

    i = 0
    sentinel_id = 0
    while i < len(tokens):
        if np.random.rand() < corruption_rate * mean_span_len:
            span_len = np.random.poisson(mean_span_len - 1) + 1
            span_len = min(span_len, len(tokens) - i)

            # Replace span with sentinel
            input_tokens[i:i+span_len] = [sentinel_tokens[sentinel_id]]
            target_tokens.extend([sentinel_tokens[sentinel_id]])
            target_tokens.extend(tokens[i:i+span_len])

            i += span_len
            sentinel_id += 1
        else:
            i += 1

    target_tokens.append(sentinel_tokens[sentinel_id])

    return input_tokens, target_tokens
```

### 3.4 Objectives Comparison

| Objective | Direction | Training Signal | Used In |
|-----------|-----------|----------------|---------|
| Next Token Prediction | Left→Right | All tokens | GPT, Llama, Mistral |
| Masked LM | Bidirectional | 15% tokens | BERT, RoBERTa |
| Prefix LM | Bidirectional + Causal | Prefix + suffix | T5, GLM |
| Span Corruption | Bidirectional | Corrupted spans | T5 |
| Permutation LM | All orders | All tokens | XLNet |
| Contrastive LM | Bidirectional | Last token | SimCSE |

## 4. Context Window and Extensions

### 4.1 Sliding Window Attention

```python
class SlidingWindowAttention:
    """Window size W: each token attends to at most W previous tokens"""
    def __init__(self, d_model, n_heads, window_size=4096):
        self.d_model = d_model
        self.n_heads = n_heads
        self.window_size = window_size

    def create_sliding_window_mask(self, seq_len):
        mask = np.zeros((seq_len, seq_len))
        for i in range(seq_len):
            start = max(0, i - self.window_size + 1)
            mask[i, start:i+1] = 1
        return mask.astype(bool)
```

### 4.2 YaRN (Yet another RoPE extensioN)

```python
class YaRN:
    """
    Extends RoPE to longer sequences by adjusting frequency.
    Key insight: interpolate frequencies for extended positions.
    """
    def __init__(self, d_model, original_max_len, scale_factor=2.0):
        self.d_model = d_model
        self.original_max_len = original_max_len
        self.scale_factor = scale_factor

        # YaRN adjusts the base frequency
        # For extended context: new_base = base * scale_factor^(d_model/(d_model-2))
        self.extended_base = 10000 * (scale_factor ** (d_model / (d_model - 2)))

    def apply_yarn(self, positions, d_k):
        """Apply YaRN-scaled frequencies to positions"""
        # Original frequencies
        inv_freq = 1.0 / (self.extended_base ** (np.arange(0, d_k, 2) / d_k))
        freqs = np.outer(positions, inv_freq)
        return freqs
```

### 4.3 NTK-Aware Scaling

```python
class NTKAwareScaling:
    """
    Neural Tangent Kernel (NTK) aware scaling.
    Adjusts RoPE base frequency to maintain high-frequency
    resolution for nearby tokens.
    """
    def __init__(self, d_model, base=10000, scale_factor=2.0):
        self.d_model = d_model
        self.base = base
        self.scale_factor = scale_factor

        # NTK-aware: scale = α^(d_model/(d_model-2))
        # where α is the context extension factor
        self.ntk_base = base * scale_factor ** (d_model / (d_model - 2))

    def get_inv_freq(self, d_k):
        return 1.0 / (self.ntk_base ** (np.arange(0, d_k, 2) / d_k))
```

### 4.4 Context Window Extension Methods

| Method | Type | Max Extension | Used In |
|--------|------|-------------|---------|
| Position Interpolation | Linear | 32x | Llama Long |
| YaRN | Frequency scaling | 128x | Llama, Mistral |
| NTK-Aware | Frequency scaling | 64x | OpenLLaMA |
| ALiBi | Bias-only | Unlimited | MPT, BLOOM |
| Ring Attention | Distributed | Unlimited | Ring Attention paper |
| Window + Global | Hybrid | 1M+ | Longformer, BigBird |

## 5. Inference

### 5.1 Autoregressive Decoding

```python
class AutoregressiveDecoder:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def generate(self, prompt, max_tokens=100, temperature=1.0,
                 top_k=50, top_p=0.9, repetition_penalty=1.0):
        tokens = self.tokenizer.encode(prompt)

        for _ in range(max_tokens):
            logits = self.model.forward(np.array(tokens))
            next_logits = logits[-1].copy()

            # Temperature
            next_logits = next_logits / temperature

            # Top-k filtering
            if top_k > 0:
                indices = np.argpartition(next_logits, -top_k)[-top_k:]
                mask = np.ones_like(next_logits, dtype=bool)
                mask[indices] = False
                next_logits[mask] = -float('inf')

            # Top-p (nucleus) filtering
            if top_p < 1.0:
                sorted_indices = np.argsort(next_logits)[::-1]
                sorted_probs = softmax(next_logits[sorted_indices])
                cumulative_probs = np.cumsum(sorted_probs)
                mask = cumulative_probs > top_p
                mask[1:] = mask[:-1]  # Keep at least one token
                next_logits[sorted_indices[mask]] = -float('inf')

            # Repetition penalty
            if repetition_penalty != 1.0:
                for t in set(tokens):
                    if next_logits[t] < 0:
                        next_logits[t] *= repetition_penalty
                    else:
                        next_logits[t] /= repetition_penalty

            # Sample
            probs = softmax(next_logits)
            probs = probs / probs.sum()  # Renormalize

            next_token = np.random.choice(len(probs), p=probs)
            tokens.append(next_token)

            # EOS check
            if next_token == self.tokenizer.eos_id:
                break

        return tokens


def softmax(x):
    e_x = np.exp(x - np.max(x, keepdims=True))
    return e_x / e_x.sum(keepdims=True)
```

### 5.2 Beam Search

```python
class BeamSearch:
    def __init__(self, model, beam_width=4, length_penalty=1.0):
        self.model = model
        self.beam_width = beam_width
        self.length_penalty = length_penalty

    def generate(self, prompt, max_tokens=100):
        # Initial beams: (tokens, score, is_complete)
        beams = [(prompt.copy(), 0.0, False)]
        completed = []

        for _ in range(max_tokens):
            candidates = []

            for tokens, score, done in beams:
                if done:
                    candidates.append((tokens, score, done))
                    continue

                logits = self.model.forward(np.array(tokens))
                next_logits = logits[-1]
                probs = softmax(next_logits)

                # Get top beam_width next tokens
                top_indices = np.argsort(next_logits)[-self.beam_width:]
                for idx in top_indices:
                    new_tokens = tokens + [idx]
                    new_score = score + np.log(probs[idx] + 1e-10)

                    # Length normalization
                    norm_score = new_score / (len(new_tokens) ** self.length_penalty)
                    candidates.append((new_tokens, norm_score, idx == 0))

            # Keep top beam_width candidates
            candidates.sort(key=lambda x: x[1], reverse=True)
            beams = candidates[:self.beam_width]

            # Check if all completed
            if all(b[2] for b in beams):
                break

        return max(beams, key=lambda x: x[1])[0]
```

### 5.3 Speculative Decoding

```python
class SpeculativeDecoding:
    def __init__(self, target_model, draft_model, gamma=5):
        self.target = target_model
        self.draft = draft_model
        self.gamma = gamma

    def generate(self, prompt, max_tokens=256):
        tokens = prompt.copy()
        while len(tokens) < max_tokens:
            # Draft phase: generate gamma tokens quickly
            draft_tokens = []
            draft_logits = []
            x = tokens.copy()

            for _ in range(self.gamma):
                logits = self.draft.forward(x)
                next_token = np.argmax(logits[-1])  # Greedy draft
                draft_tokens.append(next_token)
                draft_logits.append(logits[-1])
                x.append(next_token)

            # Target verification
            all_tokens = tokens + draft_tokens
            target_logits = self.target.forward(all_tokens)

            # Acceptance/rejection
            n_accepted = 0
            for i in range(self.gamma):
                target_prob = softmax(target_logits[len(tokens) + i])
                draft_prob = softmax(draft_logits[i])
                r = target_prob[draft_tokens[i]] / (draft_prob[draft_tokens[i]] + 1e-10)

                if np.random.rand() < min(1, r):
                    n_accepted += 1
                else:
                    # Resample from adjusted distribution
                    adjusted = np.maximum(0, target_prob - draft_prob)
                    adjusted = adjusted / adjusted.sum()
                    tokens.append(np.random.choice(len(adjusted), p=adjusted))
                    break

            tokens.extend(draft_tokens[:n_accepted])

        return tokens
```

## 6. Quantization

### 6.1 Post-Training Quantization Basics

```python
class Quantizer:
    def quantize(self, tensor, bits=8):
        """Uniform quantization: map float range to integer range"""
        min_val = np.min(tensor)
        max_val = np.max(tensor)

        # Scale and zero-point
        q_min, q_max = 0, 2**bits - 1
        scale = (max_val - min_val) / (q_max - q_min)
        zero_point = q_min - round(min_val / scale)

        # Quantize
        q_tensor = np.round(tensor / scale + zero_point).astype(np.int8)
        q_tensor = np.clip(q_tensor, q_min, q_max)

        # Dequantize
        dq_tensor = scale * (q_tensor.astype(np.float32) - zero_point)

        return q_tensor, scale, zero_point


# Example: quantize a weight matrix
W = np.random.randn(4096, 4096) * 0.02
q_W, scale, zp = Quantizer().quantize(W, bits=8)

# Memory comparison
original_bytes = W.nbytes  # 4096*4096*4 = 67MB
quantized_bytes = q_W.nbytes  # 4096*4096*1 = 16.8MB
print(f"Compression ratio: {original_bytes / quantized_bytes:.1f}x")
```

### 6.2 GPTQ (Post-Training Quantization)

```python
class GPTQ:
    """
    GPTQ: Optimal Brain Quantization
    Quantize weights column-by-column, compensating for quantization error
    in remaining columns.
    """
    def __init__(self, model, bits=4, groupsize=128):
        self.model = model
        self.bits = bits
        self.groupsize = groupsize

    def quantize_layer(self, W, H, blocksize=128):
        """
        W: weight matrix (out_dim, in_dim)
        H: Hessian (second moment matrix)
        """
        W = W.clone().float()
        n_out, n_in = W.shape
        H_inv = np.linalg.inv(H + 1e-5 * np.eye(n_in))

        # Process columns in blocks
        for start in range(0, n_in, blocksize):
            end = min(start + blocksize, n_in)

            # Quantize this block
            for col in range(start, end):
                w = W[:, col]
                h = H_inv[col, col]

                # Quantize to desired bits
                q_w = self.round_to_nearest(w, self.bits)

                # Compute quantization error
                err = w - q_w

                # Update remaining columns to compensate
                if col + 1 < n_in:
                    # Error correction
                    update = err / h * H_inv[col, col+1:col+blocksize]
                    W[:, col+1:col+blocksize] += update

        return W

    def round_to_nearest(self, w, bits):
        max_val = 2**(bits - 1) - 1
        min_val = -2**(bits - 1)
        scale = (w.max() - w.min()) / (max_val - min_val)
        q = np.round(w / scale)
        q = np.clip(q, min_val, max_val)
        return q * scale
```

### 6.3 AWQ (Activation-Aware Weight Quantization)

```python
class AWQ:
    """
    AWQ: Scale weights based on activation magnitudes.
    Important weights (large activations) get more precision.
    """
    def __init__(self, bits=4):
        self.bits = bits

    def quantize(self, W, X, alpha=0.5):
        """
        W: weight matrix
        X: calibration data activations
        alpha: balance between weight and activation importance
        """
        # Measure importance: per-channel activation magnitude
        importance = np.abs(X).mean(axis=0) ** alpha

        # Scale weights by importance
        W_scaled = W * importance.reshape(1, -1)

        # Quantize scaled weights
        max_val = 2**(self.bits - 1) - 1
        scale = W_scaled.max(axis=0) / max_val
        q_W = np.round(W_scaled / scale.reshape(1, -1))
        q_W = np.clip(q_W, -max_val, max_val)

        # Dequantize
        dq_W = q_W * scale.reshape(1, -1)
        dq_W = dq_W / importance.reshape(1, -1)  # Unscale

        return dq_W


# AWQ vs GPTQ selection criteria
def select_quantization_method(model_size, use_case):
    if model_size > 13e9:
        return "GPTQ"  # Better for large models
    elif use_case == "accuracy_critical":
        return "AWQ"   # Better preserves important weights
    else:
        return "GPTQ"  # Faster quantization
```

### 6.4 bitsandbytes (QLoRA-style)

```python
class NF4Quantizer:
    """
    NormalFloat4: information-theoretically optimal
    for normally distributed weights.
    """
    def __init__(self, blocksize=64):
        self.blocksize = blocksize

    def quantize(self, W):
        n_out, n_in = W.shape
        Wq = np.zeros_like(W, dtype=np.uint8)
        scales = []

        for i in range(0, n_in, self.blocksize):
            block = W[:, i:i+self.blocksize]
            absmax = np.abs(block).max()

            if absmax > 0:
                # Normalize to [-1, 1]
                normalized = block / absmax
                # Quantize to 4-bit using NF4 lookup
                # NF4 has non-uniform levels optimized for N(0,1)
                nf4_levels = np.array([
                    -1.0, -0.6962, -0.5251, -0.3949,
                    -0.2844, -0.1848, -0.0911, 0.0,
                    0.0796, 0.1609, 0.2461, 0.3379,
                    0.4407, 0.5626, 0.7230, 1.0
                ])

                # Find closest NF4 level
                indices = np.argmin(
                    np.abs(normalized[:, :, None] - nf4_levels[None, None, :]),
                    axis=-1
                )
                Wq[:, i:i+self.blocksize] = indices.astype(np.uint8)

            scales.append(absmax)

        return Wq, np.array(scales)
```

### 6.5 GGUF / GGML Quantization

```python
class GGUFQuantizer:
    """
    GGUF: multiple quantization formats for CPU inference.
    Q2_K through Q8_0.
    """
    def __init__(self, quant_type='Q4_K_M'):
        self.quant_type = quant_type
        self.type_info = {
            'Q2_K': {'bits': 2, 'block_size': 256},
            'Q3_K': {'bits': 3, 'block_size': 256},
            'Q4_0': {'bits': 4, 'block_size': 32},
            'Q4_K_M': {'bits': 4, 'block_size': 256},
            'Q5_K_M': {'bits': 5, 'block_size': 256},
            'Q6_K': {'bits': 6, 'block_size': 256},
            'Q8_0': {'bits': 8, 'block_size': 32},
        }

    def quantize(self, W):
        info = self.type_info[self.quant_type]
        block_size = info['block_size']
        n_out, n_in = W.shape
        Wq = np.zeros_like(W, dtype=np.int8)

        for i in range(0, n_in, block_size):
            block = W[:, i:i+block_size]
            d = np.abs(block).max() / (2**(info['bits']-1) - 1)
            Wq[:, i:i+block_size] = np.round(block / d).astype(np.int8)

        return Wq, d


# Model size comparison across quantization levels
model_params = 7e9
sizes = {
    'FP16': model_params * 2,         # 14 GB
    'INT8': model_params * 1,         # 7 GB
    'INT4': model_params * 0.5,       # 3.5 GB
    'NF4 (QLoRA)': model_params * 0.5, # 3.5 GB
    'GGUF Q4_K_M': model_params * 0.55,# 3.85 GB
}
for fmt, size in sizes.items():
    print(f"{fmt}: {size/1e9:.2f} GB")
```

### 6.6 Quantization Comparison

| Method | Bits | Memory (7B) | Quality Loss | Speed | Hardware |
|--------|------|-------------|-------------|-------|----------|
| FP16 | 16 | 14 GB | None | Fastest | GPU |
| INT8 | 8 | 7 GB | Minimal | Fast | GPU/CPU |
| GPTQ (4-bit) | 4 | 3.5 GB | Low | Fast | GPU |
| AWQ (4-bit) | 4 | 3.5 GB | Very Low | Fast | GPU |
| NF4 (QLoRA) | 4 | 3.5 GB | Low | Moderate | GPU |
| GGUF Q4 | 4 | 3.5 GB | Low | Good | CPU/GPU |
| GGUF Q2 | 2 | 1.8 GB | Significant | Good | CPU |

## 7. Fine-Tuning

### 7.1 Full Fine-Tuning

```python
class FullFineTuner:
    def __init__(self, model, lr=1e-5, weight_decay=0.01):
        self.model = model
        self.lr = lr
        self.weight_decay = weight_decay
        self.optimizer = AdamW(model.params, lr=lr, weight_decay=weight_decay)

    def train_step(self, input_ids, labels):
        logits = self.model.forward(input_ids)
        loss = autoregressive_loss(logits, labels)

        # Backward pass (full gradients)
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

        self.optimizer.step()
        self.optimizer.zero_grad()

        return loss.item()
```

### 7.2 LoRA (Low-Rank Adaptation)

```python
class LoRALayer:
    """
    LoRA: A = W + BA where B ∈ R^(d×r), A ∈ R^(r×k)
    Only train B and A; W is frozen.
    """
    def __init__(self, original_weight, rank=8, alpha=16):
        self.W = original_weight  # Frozen
        self.rank = rank
        self.alpha = alpha
        d, k = original_weight.shape

        # Initialize A with Kaiming, B with zeros
        self.A = np.random.randn(d, rank) * np.sqrt(2/d)
        self.B = np.zeros((rank, k))

        self.scaling = alpha / rank

    def forward(self, x):
        # Wx + (B*A)x * scaling
        return x @ self.W + (x @ self.A) @ self.B * self.scaling


class LoRAModel:
    def __init__(self, base_model, rank=8, alpha=16, target_modules=['W_q', 'W_k', 'W_v']):
        self.base_model = base_model
        self.lora_layers = {}

        for name, param in base_model.named_parameters():
            if any(t in name for t in target_modules):
                self.lora_layers[name] = LoRALayer(param, rank, alpha)
                param.requires_grad = False  # Freeze base

    def trainable_params(self):
        n_lora = sum(l.A.size + l.B.size for l in self.lora_layers.values())
        n_total = sum(p.numel() for p in self.base_model.parameters())
        return n_lora, n_total, n_lora / n_total * 100


# Example: LoRA on attention layers
class LoRAAttention:
    """Replace Q,K,V projections with LoRA versions"""
    def __init__(self, d_model, rank=8, alpha=16):
        self.W_q_base = np.random.randn(d_model, d_model)
        self.W_k_base = np.random.randn(d_model, d_model)
        self.W_v_base = np.random.randn(d_model, d_model)

        # LoRA adapters
        self.lora_q = LoRALayer(self.W_q_base, rank, alpha)
        self.lora_k = LoRALayer(self.W_k_base, rank, alpha)
        self.lora_v = LoRALayer(self.W_v_base, rank, alpha)

    def forward(self, Q, K, V):
        Q = self.lora_q.forward(Q)
        K = self.lora_k.forward(K)
        V = self.lora_v.forward(V)
        return scaled_dot_product_attention(Q, K, V)
```

### 7.3 QLoRA (Quantized LoRA)

```python
class QLoRALayer:
    """
    QLoRA: LoRA adapters on NF4-quantized base weights.
    Base weights are quantized to 4-bit NF4,
    LoRA adapters are in FP16/BF16.
    """
    def __init__(self, weight, quantizer, rank=64, alpha=16):
        # Quantize base weights to NF4
        self.q_weight, self.scale = quantizer.quantize(weight)

        # LoRA adapters in full precision
        d, k = weight.shape
        self.lora_A = np.random.randn(d, rank) * np.sqrt(2/d)
        self.lora_B = np.zeros((rank, k))
        self.scaling = alpha / rank

    def forward(self, x):
        # Dequantize on-the-fly (in practice: fused kernel)
        dq_weight = self.q_weight * self.scale
        # Forward through quantized weight + LoRA
        return (x @ dq_weight +
                ((x @ self.lora_A) @ self.lora_B) * self.scaling)
```

### 7.4 AdaLoRA (Adaptive Budget Allocation)

```python
class AdaLoRALayer:
    """
    AdaLoRA: adaptively allocate rank across layers.
    Uses SVD decomposition: W + PΛQ where P,Q are orthonormal
    and Λ is a diagonal matrix of singular values.
    """
    def __init__(self, weight, init_rank=8, max_rank=64):
        self.W = weight
        d, k = weight.shape
        self.max_rank = max_rank

        # SVD parameterization
        self.P = np.random.randn(d, max_rank) * 0.01
        self.Q = np.random.randn(k, max_rank) * 0.01
        self.lambda_ = np.ones(max_rank) * 0.1

        # Regularization: penalize λ to encourage sparsity
        self.regularization = 0.01

    def forward(self, x):
        # Effective update: P diag(λ) Q^T
        update = self.P @ np.diag(self.lambda_) @ self.Q.T
        return x @ (self.W + update)

    def compute_regularization_loss(self):
        # L0-like penalty via λ
        return self.regularization * np.sum(np.abs(self.lambda_))
```

### 7.5 DoRA (Weight-Decomposed Low-Rank Adaptation)

```python
class DoRALayer:
    """
    DoRA: decompose weight into magnitude and direction.
    Learn directional updates with LoRA, keep magnitude learnable.
    W' = m * (W + BA) / ||W + BA||
    """
    def __init__(self, weight, rank=8, alpha=16):
        self.W = weight
        self.rank = rank
        self.alpha = alpha
        d, k = weight.shape

        # Magnitude vector (learnable)
        self.m = np.linalg.norm(weight, axis=1)

        # LoRA directional update
        self.A = np.random.randn(d, rank) * np.sqrt(2/d)
        self.B = np.zeros((rank, k))
        self.scaling = alpha / rank

    def forward(self, x):
        # Compute direction: W + BA
        W_dir = self.W + (self.A @ self.B) * self.scaling

        # Normalize direction
        W_norm = np.linalg.norm(W_dir, axis=1, keepdims=True)
        W_dir = W_dir / (W_norm + 1e-8)

        # Scale by magnitude
        W_eff = self.m[:, None] * W_dir

        return x @ W_eff
```

### 7.6 Fine-Tuning Methods Comparison

| Method | Trainable Params (7B) | Memory | Quality | Speed |
|--------|----------------------|--------|---------|-------|
| Full FT | 100% (7B) | 56 GB (FP16) | Best | Slow |
| LoRA (r=8) | 0.1% (7M) | 16 GB | ~Full FT | Fast |
| LoRA (r=64) | 1% (70M) | 20 GB | Near full FT | Fast |
| QLoRA (r=64, 4-bit) | 1% (70M) | 6 GB | ~LoRA | Fast |
| AdaLoRA | Adaptive | ~LoRA | Slightly better | Moderate |
| DoRA (r=8) | 0.1% (7M) | ~LoRA | Better than LoRA | Fast |

## 8. Full Training Loop Example

```python
def train_llm(model, tokenizer, dataset, config):
    optimizer = AdamW(
        model.trainable_params(),
        lr=config['lr'],
        weight_decay=config['weight_decay'],
        betas=(config['beta1'], config['beta2'])
    )

    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=config['warmup_steps'],
        num_training_steps=config['total_steps']
    )

    scaler = GradScaler()  # FP16
    gradient_accumulation_steps = config['grad_accum']

    for step, batch in enumerate(dataset):
        with amp.autocast():
            logits = model.forward(batch['input_ids'])
            loss = autoregressive_loss(logits, batch['labels'])
            loss = loss / gradient_accumulation_steps

        scaler.scale(loss).backward()

        if (step + 1) % gradient_accumulation_steps == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), config['max_grad_norm'])

            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            optimizer.zero_grad()

        if step % 100 == 0:
            perplexity = np.exp(loss.item() * gradient_accumulation_steps)
            print(f"Step {step}: loss={loss.item():.4f}, ppl={perplexity:.2f}, "
                  f"lr={scheduler.get_last_lr()[0]:.2e}")
```

## 9. Model Architecture Comparison

| Model | Architecture | Params | Context | Key Innovation |
|-------|-------------|--------|---------|----------------|
| GPT-3 | Decoder-only | 175B | 2048 | In-context learning |
| BERT | Encoder-only | 340M | 512 | Bidirectional, MLM |
| T5 | Encoder-decoder | 11B | 512 | Text-to-text, span corruption |
| Llama | Decoder-only | 65B | 2048 | RoPE, SwiGLU, Pre-LN |
| Llama 2 | Decoder-only | 70B | 4096 | GQA, improved data |
| Llama 3 | Decoder-only | 405B | 128K | Grouped QK, longer context |
| Mistral | Decoder-only | 7B | 32K | Sliding window, GQA |
| Mixtral | Decoder-only | 46B (MoE) | 32K | Mixture of Experts |
| DeepSeek V2 | Decoder-only | 236B (MoE) | 128K | Multi-head latent attention |
| GPT-4 | Decoder-only (MoE) | ~1.8T | 128K | MoE, RLHF |

## 10. Exercise Problems

**Problem 1**: Implement BPE tokenization from scratch and train it on a text corpus. Compare encoding efficiency (tokens per word) with WordPiece.

**Problem 2**: Implement LoRA on a small transformer model and compare fine-tuning quality vs full fine-tuning. Measure trainable parameter ratios.

**Problem 3**: Implement GPTQ weight quantization for a 4-bit model. Measure perplexity degradation vs FP16 on Wikitext-2.

**Problem 4**: Build a beam search decoder with length penalty and repetition penalty. Compare output quality vs greedy decoding.

**Problem 5**: Implement Speculative Decoding with a smaller draft model (e.g., 70M) verifying against a larger target model (e.g., 1B). Measure wall-clock speedup.

---

## LAYER 4: Production Challenges 🚨

### Common LLM Production Failures

| Failure | Symptom | Root Cause | Prevention |
|---------|---------|-----------|-----------|
| **Hallucination** | Model generates false facts | Training data gap, low temp | Use RAG, higher temperature, fact-checking |
| **Latency Spike** | Response 10s (was 1s) | No KV caching, batch overflow | Use speculative decoding, optimize kernels |
| **OOM Crash** | GPU memory exhausted | Batch size too large, context too long | Reduce batch, use sliding window attention |
| **Jailbreak** | Model ignores safety guidelines | Adversarial prompt | Use constitutional AI, input filtering |
| **Quantization Degradation** | Quality drops 30% | Q4 too aggressive | Use Q8, calibrate on validation data |
| **Context Overflow** | Model forgets earlier tokens | Context window exceeded | Implement retrieval, summarization |

### Real Production Incident: OpenAI ChatGPT Outage

**Problem:** ChatGPT suddenly returned incorrect answers (e.g., "What's 2+2?" → "5") for 0.5% of requests.

```
Root cause: During scaling, mistakenly deployed model quantization without validation
- Full FP32 model: Correct
- Quantized INT8 model: 0.5% errors

Timeline:
- 3pm: Deploy new model (INT8 quantized)
- 3:15pm: Users report 2+2=5, sky is red, etc.
- 3:30pm: Alert fires (hallucination rate > 0.1%)
- 3:45pm: Rollback to previous version
- 4:00pm: Service restored

Impact:
- 15M users affected
- $100K lost in ChatGPT Plus credits (refunds)
- Trust damage (news articles)
```

**Prevention:**
```python
# Before deploying quantization:
# 1. Validate on benchmark (MMLU, HellaSwag, etc)
# 2. Set accuracy threshold (e.g., < 0.1% regression)
# 3. Use calibration on validation data
# 4. A/B test with 1% of users first

quantized_model = quantize(model, bits=8)
accuracy = evaluate_benchmark(quantized_model)
assert accuracy > baseline - 0.001  # No more than 0.1% regression
```

---

## Interview Questions 💼

### Level 1: Junior

**Q: What's the difference between a tokenizer and an embedding?**

A: Tokenizer converts text to token IDs. Embeddings convert token IDs to vectors.

```
Text: "Hello world"
→ Tokenizer: [Hello, world] → [7386, 1879]
→ Embeddings: [7386, 1879] → [[0.2, 0.5, ...], [0.1, 0.8, ...]]
```

**Q: What's KV cache? Why is it important?**

A: Cache stores previously computed key/value tensors to avoid recomputation. Massive speedup: O(n²) → O(n).

```
Iteration 1: Compute attention for token 1 → save K,V
Iteration 2: Compute attention for tokens 1,2 → reuse K,V from 1, compute new for 2
Result: 10x faster decoding
```

### Level 2: Intermediate

**Q: Explain attention. Why does it work so well?**

A: Attention computes weighted sum of values based on query/key similarity.

```
Query: "What's the capital?"
Keys: ["London", "England", "UK", "Europe", ...]
Attention weights: [0.1, 0.1, 0.7, 0.05, ...]  (high weight on "UK")
Output: 0.7 * "UK_embedding" + ... (focuses on relevant info)
```

Why it works: Models learn which tokens matter for current prediction.

### Level 3: Senior

**Q: Design an LLM API that handles variable-length inputs without padding waste.**

A: Use bucket batching:

```python
def batch_by_length(requests, buckets=[128, 256, 512, 1024]):
    batches = defaultdict(list)
    for req in requests:
        bucket = min(b for b in buckets if len(req) <= b)
        batches[bucket].append(req)
    
    for bucket, reqs in batches.items():
        # Pad all to bucket size (no wasted tokens)
        yield pad_batch(reqs, bucket)
```

### Level 4: Staff Engineer

**Q: Design a multi-region LLM serving system that handles 1M requests/sec.**

A:
```
Global architecture:
├─ Model replicas: 100 copies across 10 regions
├─ Batching: Collect 1M requests, batch by 100
├─ Scheduling: 10K batches, process in parallel
├─ Cache: KV cache shared across requests (90% hit rate)
├─ Quantization: INT8 (2x throughput, <0.1% accuracy loss)
└─ Optimization: Speculative decoding (1.5x speedup)

Result:
- Throughput: 1.5T tokens/sec
- Latency: 50ms p50, 200ms p99
- Cost: $0.0001 per request (profitable)
```

---

## Production Story: Anthropic Claude at Scale

**Challenge:** Scale Claude from 100K to 1M requests/day while maintaining quality.

**Solution:**
1. **Quantization:** FP32 → INT8 (2x throughput)
2. **KV Cache Optimization:** Share cache across similar prompts (30% reduction)
3. **Batching:** Collect 1000 requests, process together (3x throughput)
4. **Speculative Decoding:** Use smaller draft model to predict tokens (1.5x speedup)
5. **Hardware:** Migrate from A100 to H100 (3x peak throughput)

**Results:**
- Requests/day: 100K → 1M (10x scaling)
- Cost per request: $0.01 → $0.001 (10x cheaper)
- Latency: 5s → 2s (faster for users)
- Revenue: $1M/day → $10M/day possible

**Key lesson:** Production != research. Scale requires optimization everywhere.

---

## Summary

LLM Engineering fundamentals:

1. **Beginner** — Next token prediction, why it works
2. **Intermediate** — Attention, transformers, tokenization (this file covers extensively)
3. **Advanced** — RLHF, quantization, speculative decoding, MoE
4. **Production** — Scaling, optimization, failure modes
5. **Staff** — Multi-region, cost-per-request optimization, tradeoffs

**Next:** Understand transformer internals deeply. Profile inference. Optimize for your workload.

---

## Interactive Components

```html-live
<div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>@keyframes flow-pulse{0%,100%{opacity:.3;transform:translateY(0)}50%{opacity:1;transform:translateY(-2px)}}.flow-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:8px;letter-spacing:1px}.flow-node{display:inline-block;padding:8px 16px;border-radius:4px;font-size:12px;font-family:monospace;color:#e3eaf0;background:#1e3a5f;border:1px solid #00d4ff}.flow-arrow{color:#00d4ff;font-size:16px;animation:flow-pulse 1.5s infinite;font-weight:bold}</style>
  <div class="flow-title">RAG Pipeline: Retrieval → Generation</div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:6px">
    <div class="flow-node">User Query</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Embed Query</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Vector Search</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Retrieve Top-K Docs</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Build Context</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">LLM Generates</div>
    <div class="flow-arrow">↓</div>
    <div class="flow-node">Answer</div>
  </div>
</div>
```

```html-live
<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.obs-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px;letter-spacing:1px}.obs-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}.obs-card{padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}.obs-card:hover{border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}.obs-label{color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}.obs-value{font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}.obs-unit{color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}.metric-healthy{color:#34d399}.metric-warning{color:#fbbf24}.metric-critical{color:#ef4444}</style>
  <div class="obs-title">LLM Generation Metrics</div>
  <div class="obs-grid">
    <div class="obs-card"><div class="obs-label">Tokens/Sec</div><div class="obs-value metric-healthy">125</div><div class="obs-unit">gen/sec</div></div>
    <div class="obs-card"><div class="obs-label">Context Length</div><div class="obs-value metric-healthy">8,192</div><div class="obs-unit">tokens</div></div>
    <div class="obs-card"><div class="obs-label">Latency P99</div><div class="obs-value metric-healthy">2.3</div><div class="obs-unit">sec</div></div>
    <div class="obs-card"><div class="obs-label">Quality (ROUGE)</div><div class="obs-value metric-healthy">0.78</div><div class="obs-unit">avg</div></div>
    <div class="obs-card"><div class="obs-label">Retrieval Recall</div><div class="obs-value metric-healthy">91</div><div class="obs-unit">%</div></div>
    <div class="obs-card"><div class="obs-label">Cost per Query</div><div class="obs-value metric-healthy">0.015</div><div class="obs-unit">USD</div></div>
  </div>
</div>
```

---

## Related

- [Databases](/08-databases/) — Vector search, embeddings storage
- [Python Backend](/03-backend/) — ML inference APIs
- [Cloud Platforms](/05-cloud/) — GPU/TPU infrastructure
- [Data Engineering](/02-data-engineering/) — Training data pipelines
- [Performance Engineering](/18-performance-engineering/) — Model optimization
