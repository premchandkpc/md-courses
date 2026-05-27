# 🤖 AI Engineering Tutor — Architecture Blueprint

> **Status:** v0.1 — Foundational  
> **Owner:** Platform Architecture Team  
> **Last Updated:** 2026-05-27

---

## 1. Overview

The AI Tutor Engine is an LLM-powered interactive tutor that understands engineering concepts at depth, retrieves relevant knowledge from the platform's curated content, and responds with explanations, diagrams, simulations, and code examples. It uses a Retrieval-Augmented Generation (RAG) pipeline grounded in the Knowledge Graph, with tool-calling capabilities to execute simulations, generate visualizations, and run code.

---

## 2. AI Orchestration Architecture

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                      AI TUTOR ORCHESTRATOR                          │
 │                                                                     │
 │  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐       │
 │  │  Request   │──▶│  Router  │──▶│Executor  │──▶│ Aggregator │       │
 │  │ Interceptor│  │          │  │          │  │            │       │
 │  └────────────┘  └──────────┘  └──────────┘  └────────────┘       │
 │       │               │              │               │              │
 │       ▼               ▼              ▼               ▼              │
 │  Auth, rate-     Intent          Execute        Combine           │
 │  limit, cost     classification  selected       text + tool       │
 │  tracking        prompt routing  capabilities   results            │
 │                                                                     │
 │  ┌──────────────────────────────────────────────────────────────┐   │
 │  │                    Capability Modules                         │   │
 │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
 │  │  │ Explain  │ │ Generate │ │ Review   │ │ Debug         │   │   │
 │  │  │ Concept  │ │ Diagram  │ │ Arch     │ │ Scenario      │   │   │
 │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
 │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │   │
 │  │  │ Create   │ │ Suggest  │ │ Generate │ │ Execute        │   │   │
 │  │  │ Scenario │ │ Learning │ │ Quiz     │ │ Code           │   │   │
 │  │  │          │ │ Path     │ │          │ │                │   │   │
 │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │   │
 │  └──────────────────────────────────────────────────────────────┘   │
 └─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                     RAG PIPELINE                                     │
 │  Query → Embed → Vector Search → Graph Traverse → Prompt → LLM →   │
 │  Response                                                           │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## 3. RAG Pipeline

```
 ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
 │  User    │───▶│  Query   │───▶│  Retrieve│───▶│  Context │───▶│  LLM     │
 │  Query   │    │  Processor│   │  Pipeline│   │  Assembly│   │  Generate│
 └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │              │              │               │               │
       ▼              ▼              ▼               ▼               ▼
  "Explain       Rewrite,      1. Embed query     Merge top-K     Construct
  Kafka ISR"    expand,       2. Vector search    chunks +        system +
                classify       3. BM25 FTS        graph context   user prompt,
                 intent        4. Graph           + tool          stream tokens
                                traversal         schemas         → client
```

### 3.1 Query Processing

```typescript
interface QueryProcessor {
  rewrite(query: string, context?: ConversationContext): string
  // Expands: "explain ISR" → "Explain Kafka In-Sync Replicas (ISR) mechanism"

  classifyIntent(query: string): Intent
  // Returns: EXPLAIN | GENERATE_DIAGRAM | REVIEW_ARCH | DEBUG_SCENARIO |
  //          GENERATE_QUIZ | SUGGEST_PATH | EXECUTE_CODE | CREATE_SCENARIO

  extractEntities(query: string): ExtractedEntity[]
  // Returns: [{ type: 'concept', name: 'ISR' },
  //           { type: 'topic', name: 'Kafka' }]

  generateSearchQueries(query: string): string[]
  // Generates multiple search queries for better recall
  // ["Kafka In-Sync Replicas", "ISR Kafka replication", "Kafka ISR mechanism"]
}
```

### 3.2 Retrieval Pipeline

```typescript
interface Retriever {
  vectorSearch(query: string, k: number): ScoredChunk[]
  // Uses: Neo4j vector index on Concept.embedding
  // Returns: [{ chunk: "ISR definition...", score: 0.92, source: conceptId }]

  bm25Search(query: string, k: number): ScoredChunk[]
  // Uses: PostgreSQL full-text search on content_chunks table
  // tsvector index on chunk_text column

  graphTraversal(conceptIds: string[], depth: number): GraphContext
  // Starting from matched concepts, traverse outgoing edges up to depth
  // Collects: prerequisites, related concepts, patterns, tools, simulators

  hybridSearch(query: string, k: number): ScoredChunk[]
  // Reciprocal Rank Fusion of vectorSearch + bm25Search
  // Re-ranks with cross-encoder
}
```

### 3.3 Context Assembly

```typescript
function assembleContext(
  chunks: ScoredChunk[],
  graphCtx: GraphContext,
  query: Intent,
  maxTokens: number = 8000
): string {
  // Priority ordering:
  // 1. Exact concept definitions (highest relevance)
  // 2. Prerequisite context (needed to understand the answer)
  // 3. Related concepts (breadth)
  // 4. Code examples
  // 5. Visual diagrams (mermaid/text)
  // 6. Tool/simulator references

  // Truncate to maxTokens using sliding window
  // Add source metadata for citation

  return assembleWithTemplate(contextTemplate, {
    definitions: formatDefinitions(chunks.filter(c => c.type === 'definition')),
    prerequisites: formatGraphNodes(graphCtx.prerequisites),
    related: formatGraphNodes(graphCtx.related),
    examples: formatCodeExamples(chunks.filter(c => c.type === 'code')),
    resources: formatResources(graphCtx.resources),
  })
}
```

---

## 4. LLM Integration

### 4.1 Multi-Model Architecture

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                      MODEL TIER CHAIN                                │
 │                                                                     │
 │  Request ──▶ Intent Classification ──▶ Model Selection               │
 │                                           │                         │
 │                                           ▼                         │
 │                                   ┌──────────────┐                  │
 │                          ┌──────▶│  GPT-4o       │  Complex explain,│
 │                          │       │  (Primary)    │  diagram gen     │
 │                          │       └──────┬───────┘                  │
 │                          │              │ (if rate-limited)         │
 │                          │              ▼                           │
 │                          │       ┌──────────────┐                  │
 │                          ├──────▶│  Claude 3.5   │  Code, arch     │
 │                          │       │  Sonnet       │  review          │
 │                          │       └──────┬───────┘                  │
 │                          │              │ (if quota exceeded)       │
 │                          │              ▼                           │
 │                          │       ┌──────────────┐                  │
 │                          └──────▶│  Ollama       │  Low-cost,       │
 │                                  │  (local)      │  simple Q&A      │
 │                                  └──────────────┘                  │
 └─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Prompt Caching

```typescript
// System prompts cached by capability
const promptCache = new LRUCache<string, string>({
  max: 100,
  ttl: 3600_000,  // 1 hour
})

async function getSystemPrompt(capability: Capability, context: Context): Promise<string> {
  const key = `${capability}_${context.language}_${context.difficulty}`
  let prompt = promptCache.get(key)
  if (!prompt) {
    prompt = await compilePromptTemplate(capability, context)
    promptCache.set(key, prompt)
  }
  // Inject dynamic context (few-shot examples from DB)
  const examples = await getFewShotExamples(capability, context.topic)
  return injectExamples(prompt, examples)
}
```

### 4.3 Context Window Management

```typescript
function manageContextWindow(messages: Message[], maxTokens: number): Message[] {
  let totalTokens = countTokens(messages)

  while (totalTokens > maxTokens) {
    // Strategy: Summarize oldest messages first
    if (messages.length > 4) {
      const oldest = messages.splice(1, 2)  // remove oldest user+assistant pair
      const summary = summarizeMessages(oldest)
      messages.splice(1, 0, { role: 'system', content: `[Summary: ${summary}]` })
    } else {
      // Truncate last response
      messages[messages.length - 1].content = truncate(
        messages[messages.length - 1].content,
        maxTokens - countTokens(messages.slice(0, -1))
      )
      break
    }
    totalTokens = countTokens(messages)
  }

  return messages
}
```

---

## 5. Tool Calling System

```typescript
interface Tool {
  name: string
  description: string
  parameters: JSONSchema
  execute(params: Record<string, unknown>, context: ToolContext): Promise<ToolResult>
}

const tools: Tool[] = [
  {
    name: 'execute_simulation',
    description: 'Run a distributed system simulation scenario and return results',
    parameters: {
      type: 'object',
      properties: {
        scenario: { type: 'string', enum: ['kafka-broker-failure', 'raft-election', 'tcp-handshake'] },
        params: { type: 'object' }
      }
    },
    async execute(params) {
      const sim = await simulationEngine.run(params.scenario, params.params)
      return { status: 'completed', metrics: sim.metrics, events: sim.events }
    }
  },
  {
    name: 'generate_diagram',
    description: 'Generate a diagram (mermaid or SVG) of a system architecture or flow',
    parameters: {
      type: 'object',
      properties: {
        type: { type: 'string', enum: ['architecture', 'sequence', 'flow', 'topology'] },
        description: { type: 'string' }
      }
    },
    async execute(params) {
      const diagram = await diagramGenerator.generate(params.type, params.description)
      return { format: 'mermaid', content: diagram }
    }
  },
  {
    name: 'query_graph',
    description: 'Query the knowledge graph for concepts, prerequisites, relationships',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        type: { type: 'string', enum: ['concept', 'relationship', 'path', 'neighborhood'] }
      }
    },
    async execute(params) {
      return await knowledgeGraph.query(params.query, params.type)
    }
  },
  {
    name: 'search_code',
    description: 'Search code examples and patterns in the repository',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        language: { type: 'string' },
        limit: { type: 'number', default: 5 }
      }
    }
  },
  {
    name: 'run_code',
    description: 'Execute code in a sandboxed environment',
    parameters: {
      type: 'object',
      properties: {
        code: { type: 'string' },
        language: { type: 'string', enum: ['python', 'javascript', 'go', 'java'] },
        timeout: { type: 'number', default: 10 }
      }
    },
    async execute(params) {
      return await codeSandbox.execute(params.code, params.language, params.timeout)
    }
  },
  {
    name: 'debug_scenario',
    description: 'Analyze a simulation or system failure scenario and suggest fixes',
    parameters: {
      type: 'object',
      properties: {
        scenario: { type: 'string' },
        symptoms: { type: 'array', items: { type: 'string' } }
      }
    },
    async execute(params) {
      const analysis = await debugEngine.analyze(params.scenario, params.symptoms)
      return { diagnosis: analysis.diagnosis, fixes: analysis.suggestedFixes }
    }
  },
  {
    name: 'review_architecture',
    description: 'Review an architecture description against best practices',
    parameters: {
      type: 'object',
      properties: {
        architecture: { type: 'string' },
        patterns: { type: 'array', items: { type: 'string' } }
      }
    },
    async execute(params) {
      return await archReviewer.review(params.architecture, params.patterns)
    }
  }
]
```

---

## 6. Conversation Memory

### 6.1 Memory Architecture

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                     CONVERSATION MEMORY                              │
 │                                                                     │
 │  ┌─────────────────────────────────────────────────────────────┐    │
 │  │                    Short-Term Memory                          │    │
 │  │  Sliding window of last N messages (default: 20)             │    │
 │  │  + Periodic summarization of earlier messages                │    │
 │  │  Stored in Redis with TTL (30 min session timeout)           │    │
 │  └─────────────────────────────────────────────────────────────┘    │
 │                              │                                       │
 │                              ▼                                       │
 │  ┌─────────────────────────────────────────────────────────────┐    │
 │  │                    Long-Term Memory                           │    │
 │  │  Vector store (PGVector) of significant conversation turns   │    │
 │  │  Entity extraction: concepts/topics discussed → graph nodes  │    │
 │  │  Key facts extracted and stored with source attribution       │    │
 │  │  Retrieved on related queries for continuity                  │    │
 │  └─────────────────────────────────────────────────────────────┘    │
 │                              │                                       │
 │                              ▼                                       │
 │  ┌─────────────────────────────────────────────────────────────┐    │
 │  │                    Episodic Memory                            │    │
 │  │  Full session recordings for replay/debug                    │    │
 │  │  Stored in S3 as compressed JSONL (max 7 days retention)     │    │
 │  │  Used for: quality review, model fine-tuning data, analytics │    │
 │  └─────────────────────────────────────────────────────────────┘    │
 └─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Long-Term Memory Retrieval

```typescript
async function retrieveRelevantMemory(
  query: string,
  userId: string,
  k: number = 5
): Promise<MemoryEntry[]> {
  // 1. Embed the query
  const embedding = await embedder.embed(query)

  // 2. Vector search on user's long-term memory
  const memories = await pgvector.query(
    'SELECT content, metadata, 1 - (embedding <=> $1) AS similarity FROM memories ' +
    'WHERE user_id = $2 AND similarity > 0.7 ORDER BY similarity DESC LIMIT $3',
    [embedding, userId, k]
  )

  // 3. Attach source concepts from knowledge graph
  for (const memory of memories) {
    const concepts = await knowledgeGraph.search(memory.metadata.concepts)
    memory.context = concepts
  }

  return memories
}
```

---

## 7. User Intent Classification

```typescript
enum Intent {
  EXPLAIN_CONCEPT = 'explain_concept',
  GENERATE_DIAGRAM = 'generate_diagram',
  REVIEW_ARCHITECTURE = 'review_architecture',
  CREATE_SCENARIO = 'create_scenario',
  DEBUG_ISSUE = 'debug_issue',
  GENERATE_QUIZ = 'generate_quiz',
  SUGGEST_PATH = 'suggest_learning_path',
  EXECUTE_CODE = 'execute_code',
  COMPARE_CONCEPTS = 'compare_concepts',
  GENERAL_QUESTION = 'general_question',
}

function classifyIntent(query: string, history: Message[]): Intent {
  // Fast path: pattern matching
  if (query.match(/^(explain|what is|how does|define)\b/i)) return Intent.EXPLAIN_CONCEPT
  if (query.match(/^(diagram|draw|visualize|show me)\b/i)) return Intent.GENERATE_DIAGRAM
  if (query.match(/^(review|audit|evaluate)\b.*arch/i)) return Intent.REVIEW_ARCHITECTURE
  if (query.match(/^(debug|fix|why is|why did)\b/i)) return Intent.DEBUG_ISSUE
  if (query.match(/^(quiz|test me|practice)\b/i)) return Intent.GENERATE_QUIZ
  if (query.match(/^(path|roadmap|learn|study plan)\b/i)) return Intent.SUGGEST_PATH
  if (query.match(/^(run|execute|compile)\b/i)) return Intent.EXECUTE_CODE
  if (query.match(/^(compare|vs|versus|difference)\b/i)) return Intent.COMPARE_CONCEPTS
  if (query.match(/^(scenario|simulate|create.*sim)\b/i)) return Intent.CREATE_SCENARIO

  // Slow path: LLM-based classification (cached)
  return llmClassifyIntent(query, history)
}
```

---

## 8. Prompt Templates

```typescript
const PROMPT_TEMPLATES: Record<Capability, PromptTemplate> = {
  explain_concept: {
    system: `You are an expert distributed systems tutor. Explain concepts clearly with:
1. A concise definition
2. Why it matters (motivation)
3. How it works (mechanism with step-by-step)
4. Visual ASCII diagram where applicable
5. Code/config example
6. Common pitfalls
7. Related concepts (mention for further learning)

Always cite sources from the knowledge base.
If unsure about a detail, say so. Never hallucinate.`,

    user: `Explain "{concept}" from the {topic} domain.
User level: {difficulty}
Include: {include_sections}`,
  },

  generate_diagram: {
    system: `You generate mermaid.js diagrams for system architectures, protocol flows, and topologies. 
Return ONLY valid mermaid code. Choose the appropriate diagram type:
- sequenceDiagram for protocol flows
- flowchart LR for architectures
- graph TB for topologies
- stateDiagram-v2 for state machines`,

    user: `Generate a {type} diagram for: {description}
Style: {style}`,
  },

  debug_scenario: {
    system: `You are a senior SRE debug engineer. Given system symptoms:
1. List possible root causes (most likely first)
2. For each: explain why it could cause the symptom
3. Suggest verification steps
4. Recommend mitigation/fix
5. Show relevant monitoring queries`,

    user: `System: {system_type}
Symptom: {symptom}
Recent changes: {changes}
Relevant metrics: {metrics}`,
  },

  generate_quiz: {
    system: `Generate quiz questions that test deep understanding, not recall.
Mix of: multiple choice, scenario-based, and code-review questions.
Each question must have: question, options (for MCQ), answer, explanation, and which concept it tests.
Difficulty: {difficulty}`,

    user: `Generate {count} questions about {topic}
Difficulty: {difficulty}
Types: {types}`,
  }
}
```

---

## 9. Code Execution Sandbox

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                    CODE EXECUTION SANDBOX                            │
 │                                                                     │
 │  Request ──▶ Language Detection ──▶ Sandbox Selection                │
 │                                        │                            │
 │                                        ▼                            │
 │                          ┌──────────────────────┐                   │
 │                          │   WebContainer (JS)  │  In-browser       │
 │                          │   Pyodide (Python)   │  WASM-based       │
 │                          │   Go Playground (Go) │  Remote API       │
 │                          │   Judge0 (Java)      │  Container API    │
 │                          └──────────────────────┘                   │
 │                                        │                            │
 │                                        ▼                            │
 │  ┌────────────────────────────────────────────────────────────┐     │
 │  │                    Security Controls                         │     │
 │  │  • Time limit: 30s                                          │     │
 │  │  • Memory limit: 256MB                                      │     │
 │  │  • Network: blocked (no outbound connections)               │     │
 │  │  • Filesystem: read-only except /tmp                        │     │
 │  │  • Syscalls: filtered via seccomp                           │     │
 │  │  • CPU: limited to 1 core                                   │     │
 │  └────────────────────────────────────────────────────────────┘     │
 │                                                                     │
 │  Output ──▶ stdout/stderr capture ──▶ Return to LLM ──▶ User       │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Quality Assurance

```typescript
interface QAEngine {
  validateResponse(response: string, context: RAGContext): ValidationResult
  checkFactualConsistency(response: string, knowledgeBase: Chunk[]): FactCheck[]
  detectHallucination(response: string, context: RAGContext): Hallucination[]
  verifyCitations(response: string): CitationVerification[]
}

// Self-consistency check
async function selfConsistencyCheck(
  query: string,
  response: string,
  model: string,
  n: number = 3
): Promise<ConsistencyScore> {
  // Generate N alternative responses with low temperature
  const alternatives = await Promise.all(
    Array(n).fill(null).map(() => generateResponse(query, { temperature: 0.7 }))
  )

  // Extract key claims from all responses
  const claims = [response, ...alternatives].flatMap(extractClaims)

  // Cluster claims and check agreement rate
  const clusters = clusterClaims(claims)
  const agreementRate = clusters.filter(c => c.agreement > 0.7).length / clusters.length

  // Flag low-agreement clusters as potential hallucinations
  const flagged = clusters.filter(c => c.agreement < 0.5)

  return {
    score: agreementRate,
    flaggedClaims: flagged,
    suggestedCorrections: flagged.map(f => f.majorityClaim),
  }
}
```

---

## 11. Performance & Cost Management

```typescript
interface CostManager {
  // Token budgeting per request
  maxInputTokens: 8000
  maxOutputTokens: 2000
  maxContextTokens: 32000

  // Model tiering by cost
  modelTiers: {
    cheap:   ['ollama/llama3', 'claude-3-haiku'],
    medium:  ['gpt-4o-mini', 'claude-3-sonnet'],
    expensive: ['gpt-4o', 'claude-3-opus'],
  }

  // Select tier based on complexity
  selectModel(intent: Intent, userTier: string): string {
    if (intent === 'GENERAL_QUESTION') return this.modelTiers.cheap[0]
    if (intent === 'EXPLAIN_CONCEPT') return this.modelTiers.medium[0]
    if (intent === 'REVIEW_ARCHITECTURE') return this.modelTiers.expensive[0]
    return userTier === 'premium' ? this.modelTiers.expensive[0] : this.modelTiers.medium[0]
  }

  // Request caching (identical queries within TTL)
  async getCachedResponse(query: string, context: string): Promise<string | null> {
    const hash = crypto.createHash('sha256').update(query + context).digest('hex')
    return redis.get(`ai_cache:${hash}`)
  }
}
```

---

## 12. Response Streaming

```
 Client (EventSource/WS)         AI Tutor API            LLM Provider
 ──────────────────────    ────────────────────    ─────────────────
        │                         │                        │
        │  POST /api/ai/tutor     │                        │
        │  { query: "Explain..."} │                        │
        │────────────────────────▶│                        │
        │                         │   Classify intent      │
        │                         │   Retrieve context     │
        │                         │   Build prompt         │
        │                         │                        │
        │                         │   POST /v1/chat        │
        │                         │───────────────────────▶│
        │                         │                        │
        │  event: token           │   stream: "Kafka"     │
        │◀────────────────────────│────────────────────────│
        │  event: token           │   stream: " ISR"      │
        │◀────────────────────────│────────────────────────│
        │  event: token           │   stream: " stands"   │
        │◀────────────────────────│────────────────────────│
        │  event: tool_call       │                        │
        │  { tool: "query_graph", │                        │
        │    args: { query:... }} │                        │
        │◀────────────────────────│                        │
        │                         │                        │
        │  (execute tool client-side or via backend)        │
        │                         │                        │
        │  event: tool_result     │                        │
        │  { result: {...} }      │                        │
        │────────────────────────▶│                        │
        │                         │  Resume generation     │
        │                         │───────────────────────▶│
        │  event: done            │                        │
        │◀────────────────────────│────────────────────────│
        │  event: sources         │                        │
        │  { citations: [...] }   │                        │
        │◀────────────────────────│                        │
```

Responses are streamed using Server-Sent Events (SSE) with `text/event-stream`. Tool calls are intercepted and executed server-side, with the result injected back into the generation loop.
