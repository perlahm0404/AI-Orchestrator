# LlamaIndex Evaluation for Perplexity/SurfSense Hybrid

**Date**: 2026-01-28
**Goal**: Assess LlamaIndex framework for building a cross between Perplexity and SurfSense

---

## Project Vision: Perplexity + SurfSense Hybrid

### Target Features
| Feature | Source Inspiration |
|---------|-------------------|
| AI-powered search with citations | Perplexity |
| RAG over internal knowledge | SurfSense |
| Team collaboration + RBAC | SurfSense |
| Real-time conversational interface | Both |
| External source integrations | SurfSense (20+ connectors) |
| Multi-modal support (docs, images, video) | SurfSense |

---

## LlamaIndex Repository Overview

### Stats
- **Stars**: 46,658 (top-tier framework)
- **License**: MIT (commercial-friendly)
- **Primary Language**: Python
- **Created**: November 2022
- **Activity**: Active (last push: 2026-01-28)
- **Forks**: 6,756 (strong community)

### Official Description
"LlamaIndex is the leading framework for building LLM-powered agents over your data."

---

## Core Architecture

### Key Modules

#### 1. Data Connectors
- **Purpose**: Ingest data from native sources (APIs, PDFs, SQL, etc.)
- **Coverage**: 300+ integrations via LlamaHub
- **Relevance**: ✅ Critical for SurfSense-style external source integration

#### 2. Data Indexing
- **Purpose**: Structure data in LLM-friendly intermediate representations
- **Features**: Vector stores, metadata extraction, document management
- **Relevance**: ✅ Core RAG requirement for both Perplexity and SurfSense

#### 3. Query Engines
- **Purpose**: Question-answering workflows (RAG)
- **Features**: Response synthesizers, node postprocessors
- **Relevance**: ✅ Essential for Perplexity-style cited answers

#### 4. Chat Engines
- **Purpose**: Multi-turn conversational interactions
- **Features**: Context management, conversation memory
- **Relevance**: ✅ Required for SurfSense-style team collaboration

#### 5. Agents
- **Purpose**: LLM-powered knowledge workers with tool integration
- **Features**: Event-driven workflows, autonomous task completion
- **Relevance**: ⚠️ Useful but not primary focus for search/knowledge app

---

## Technical Stack

### Language Support
- **Python**: Primary (15.5M lines)
- **TypeScript/JavaScript**: Available via [LlamaIndex.TS](https://github.com/run-llama/LlamaIndexTS)
- **Jupyter Notebooks**: Extensive examples (9.8M lines)

### Integration Model
- **Core Package**: `llama-index-core` (minimal dependencies)
- **Integration Packages**: 300+ modular plugins via LlamaHub
- **Flexibility**: Choose only what you need (LLM, embeddings, vector stores)

### Example Providers Supported
- **LLMs**: OpenAI, Anthropic, Replicate (Llama 2), Ollama, etc.
- **Embeddings**: HuggingFace, OpenAI, Cohere, etc.
- **Vector Stores**: Pinecone, Weaviate, Qdrant, Chroma, etc.

---

## Strengths for Perplexity/SurfSense Hybrid

### ✅ High Alignment

1. **Production-Ready RAG**
   - Battle-tested by thousands of projects
   - Advanced retrieval strategies (hybrid search, reranking, metadata filtering)
   - Citation support built-in

2. **Modular Architecture**
   - Start simple (5 lines of code)
   - Customize everything (data loaders, retrievers, synthesizers)
   - Swap components without rewriting (LLM-agnostic, vector-store-agnostic)

3. **Rich Integration Ecosystem**
   - 300+ data connectors (Google Drive, Slack, Notion, GitHub, etc.)
   - Matches SurfSense's 20+ external sources
   - Community-maintained via LlamaHub

4. **Query Engine Flexibility**
   - Multi-document retrieval
   - Sub-question decomposition
   - Iterative refinement
   - → Perfect for Perplexity-style complex queries

5. **Chat Engine Support**
   - Context-aware multi-turn conversations
   - Conversation memory management
   - → Enables SurfSense-style team collaboration

6. **Documentation & Community**
   - Extensive docs (developers.llamaindex.ai)
   - Active Discord, Reddit, Twitter
   - 300+ example notebooks

### ⚠️ Considerations

1. **Team Collaboration Features**
   - LlamaIndex is a RAG/agent framework, not a full-stack app
   - You'll need to build:
     - User management + RBAC (custom or use FastAPI Users)
     - Real-time collaboration (WebSockets, Electric-SQL)
     - Frontend (Next.js or similar)
   - SurfSense already has these built-in

2. **Operational Complexity**
   - LlamaIndex handles data + LLM orchestration
   - You'll need to add:
     - Database (PostgreSQL + pgvector)
     - Message queue (Celery + Redis for async tasks)
     - Deployment (Docker, K8s)
   - SurfSense provides reference architecture

3. **Learning Curve**
   - Modular flexibility = more decisions to make
   - Need to understand: indices, retrievers, synthesizers, nodes, embeddings
   - Beginner-friendly for simple use cases, expert-friendly for customization

---

## Comparison: LlamaIndex vs SurfSense

| Dimension | LlamaIndex | SurfSense |
|-----------|------------|-----------|
| **Type** | Framework (library) | Full-stack application |
| **RAG Quality** | Industry-leading, highly customizable | Good (uses LangChain + LangGraph) |
| **Data Connectors** | 300+ via LlamaHub | 20+ built-in |
| **Team Collaboration** | Not included (build yourself) | Built-in with RBAC |
| **Frontend** | Not included | Next.js included |
| **Backend** | Not included | FastAPI included |
| **Deployment** | DIY | Docker Compose ready |
| **Flexibility** | Maximum (every component swappable) | Medium (full-stack tradeoff) |
| **Time to MVP** | Medium (need to build app shell) | Fast (clone + configure) |
| **Production Ready** | Yes (framework) | Approaching (app) |

---

## Architecture Options

### Option 1: Build on LlamaIndex (Ground-Up)

**Stack**:
```
Frontend: Next.js
Backend: FastAPI
RAG Engine: LlamaIndex
Database: PostgreSQL + pgvector
Auth: FastAPI Users
Real-time: WebSockets or Electric-SQL
Deployment: Docker + K8s
```

**Pros**:
- Maximum flexibility and control
- Best-in-class RAG quality
- Choose every component (LLM, vector store, etc.)
- No bloat (only what you need)

**Cons**:
- Longer time to MVP (6-12 weeks)
- Need to build team collaboration from scratch
- More maintenance responsibility

**Best For**:
- Custom requirements (e.g., enterprise security, specific integrations)
- Team has backend/full-stack expertise
- Long-term investment in custom platform

---

### Option 2: Fork SurfSense, Enhance with LlamaIndex

**Approach**:
1. Fork SurfSense (full-stack app with team collaboration)
2. Replace LangChain RAG layer with LlamaIndex
3. Keep existing: auth, RBAC, frontend, real-time collaboration

**Pros**:
- Fast time to MVP (2-4 weeks)
- Team collaboration already built
- Docker deployment ready
- Better RAG quality than current LangChain implementation

**Cons**:
- Inherits SurfSense architecture decisions
- Need to understand existing codebase
- Potential conflicts between LangChain agents and LlamaIndex

**Best For**:
- Quick MVP to test product-market fit
- Team wants to focus on features, not infrastructure
- Comfortable with SurfSense's tech choices

---

### Option 3: Hybrid (LlamaIndex Core + SurfSense Reference)

**Approach**:
1. Build RAG backend with LlamaIndex (your core differentiator)
2. Copy/adapt SurfSense's frontend + collaboration layer
3. Use SurfSense as architectural reference, not codebase

**Pros**:
- Best RAG quality (LlamaIndex)
- Learn from SurfSense's UX/collaboration patterns
- Freedom to make different tech choices
- Can cherry-pick features

**Cons**:
- Medium effort (4-8 weeks)
- Still need to build integration layer
- More coordination between components

**Best For**:
- Want best-of-both-worlds
- Team wants to understand full stack
- Planning to diverge significantly from SurfSense

---

## Recommendation

### If Time to Market is Critical (< 1 month):
→ **Option 2: Fork SurfSense + Enhance with LlamaIndex**

**Reasoning**:
- SurfSense already has 80% of what you need (UI, collaboration, connectors)
- LlamaIndex RAG swap gives you Perplexity-quality answers
- Focus on differentiation (better search, citations, UX)

**Action Plan**:
1. Clone SurfSense, get it running locally
2. Identify RAG layer boundaries (likely in `surfsense_backend/app/agents/`)
3. Replace with LlamaIndex query/chat engines
4. Test hybrid search + citation quality
5. Deploy MVP

---

### If Building for Scale & Custom Requirements (3-6 months):
→ **Option 1: Ground-Up with LlamaIndex**

**Reasoning**:
- Maximum control over architecture
- No technical debt from inherited code
- Can optimize for specific use case (e.g., HIPAA, SOC2, specific industry)

**Action Plan**:
1. Design data model (users, workspaces, documents, citations)
2. Build FastAPI backend with LlamaIndex RAG core
3. Implement auth + RBAC (FastAPI Users or custom)
4. Build Next.js frontend with real-time features
5. Deploy on your infrastructure

---

## Technical Deep-Dive: Key LlamaIndex Features

### 1. Citation Support (Perplexity Requirement)

LlamaIndex has built-in citation tracking:

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(
    response_mode="tree_summarize",
    verbose=True
)

response = query_engine.query("What is RAG?")
# Response includes:
# - response.response (text answer)
# - response.source_nodes (list of cited sources with scores)
```

Each source node contains:
- Original text snippet
- Document metadata (title, URL, timestamp)
- Similarity score
- Node ID for deduplication

→ **Perfect for Perplexity-style cited answers**

---

### 2. Hybrid Search (SurfSense Requirement)

LlamaIndex supports multiple retrieval modes:

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine

# Vector retriever
vector_retriever = VectorIndexRetriever(index=index, similarity_top_k=10)

# BM25 (keyword) retriever
bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=10)

# Hybrid with reranking
from llama_index.core.postprocessor import SentenceTransformerRerank

query_engine = RetrieverQueryEngine(
    retriever=vector_retriever,  # or custom hybrid retriever
    node_postprocessors=[
        SentenceTransformerRerank(model="cross-encoder/ms-marco-MiniLM-L-6-v2", top_n=5)
    ]
)
```

→ **Matches SurfSense's hybrid search + reranking**

---

### 3. Multi-Modal Support

LlamaIndex supports images, audio, video via:

```python
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core.schema import ImageDocument

# Image documents
image_docs = [ImageDocument(image_path="./chart.png")]

# Multi-modal query engine
mm_llm = OpenAIMultiModal(model="gpt-4-vision-preview")
response = mm_llm.complete(
    prompt="What does this chart show?",
    image_documents=image_docs
)
```

→ **Enables SurfSense-style multi-format processing**

---

### 4. External Source Connectors

LlamaHub provides 300+ data loaders:

```python
# Google Drive
from llama_index.readers.google import GoogleDriveReader
gdrive = GoogleDriveReader()
documents = gdrive.load_data(folder_id="your_folder_id")

# Slack
from llama_index.readers.slack import SlackReader
slack = SlackReader(slack_token="your_token")
documents = slack.load_data(channel_ids=["C1234567"])

# Notion
from llama_index.readers.notion import NotionPageReader
notion = NotionPageReader(integration_token="your_token")
documents = notion.load_data(page_ids=["page_id"])
```

→ **Matches SurfSense's 20+ connectors, plus 280 more**

---

### 5. Agent System (Advanced)

LlamaIndex includes ReAct agents for complex workflows:

```python
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import QueryEngineTool

# Create tools from query engines
tools = [
    QueryEngineTool.from_defaults(
        query_engine=docs_engine,
        name="documentation_search",
        description="Search product documentation"
    ),
    QueryEngineTool.from_defaults(
        query_engine=support_engine,
        name="support_tickets",
        description="Search support ticket history"
    )
]

# Agent decides which tool to use
agent = ReActAgent.from_tools(tools, llm=llm, verbose=True)
response = agent.chat("How do I reset my password?")
```

→ **Optional: Could enable Perplexity-style multi-source synthesis**

---

## Cost Considerations

### LlamaIndex Licensing
- **MIT License**: Free for commercial use
- **No usage fees**: Pay only for underlying services (LLM API, vector DB)

### Estimated Operating Costs (1000 users, 10k queries/day)

| Component | Provider | Monthly Cost |
|-----------|----------|--------------|
| LLM (GPT-4o) | OpenAI | $500-2000 (depends on context length) |
| Embeddings | OpenAI (text-embedding-3-small) | $50-200 |
| Vector Store | Pinecone (Starter) | $70 |
| Hosting (app) | AWS/GCP | $200-500 |
| **Total** | | **$820-2770/month** |

**Cost Optimization**:
- Use local embeddings (sentence-transformers) → Save $50-200/mo
- Use Ollama for LLM (self-hosted) → Save $500-2000/mo
- Use Qdrant (self-hosted) → Save $70/mo
- **Optimized Total**: ~$200/month (hosting only)

---

## Next Steps

### Immediate Actions (Research Phase)

1. **Run LlamaIndex Locally** (1 hour)
   ```bash
   pip install llama-index llama-index-llms-openai
   # Run examples from docs/examples/
   ```
   - Goal: Understand API, query quality, citation format

2. **Run SurfSense Locally** (2 hours)
   ```bash
   git clone https://github.com/MODSetter/SurfSense.git
   cd SurfSense
   docker-compose up
   ```
   - Goal: Understand UI/UX, collaboration features, architecture

3. **Build Proof-of-Concept** (1 day)
   - Simple FastAPI endpoint with LlamaIndex
   - Test citation quality vs Perplexity
   - Test hybrid search performance
   - Goal: Validate LlamaIndex meets quality requirements

4. **Evaluate Integration Options** (2 days)
   - Map SurfSense RAG layer boundaries
   - Estimate effort for Options 1, 2, 3
   - Create technical design doc
   - Goal: Choose architecture path

---

## Open Questions

### Technical
- [ ] What vector store? (Pinecone, Weaviate, Qdrant, self-hosted?)
- [ ] What LLM strategy? (OpenAI, Anthropic, self-hosted Llama, hybrid?)
- [ ] What's the data model for team workspaces?
- [ ] How to handle real-time collaboration? (WebSockets, Electric-SQL, other?)
- [ ] What's the auth strategy? (OAuth only, or support SAML/LDAP for enterprise?)

### Product
- [ ] Who is the target user? (Individuals, small teams, enterprises?)
- [ ] What's the monetization model? (Freemium, usage-based, seats?)
- [ ] What's the key differentiator vs Perplexity? (Privacy, customization, integrations?)
- [ ] What's the key differentiator vs SurfSense? (Better UX, better search, specific industry focus?)

### Operational
- [ ] Self-hosted only, cloud-hosted, or both?
- [ ] What compliance requirements? (SOC2, HIPAA, GDPR?)
- [ ] What's the go-to-market timeline? (MVP in 1 month, 3 months, 6 months?)

---

## Conclusion

**LlamaIndex is HIGHLY APPROPRIATE for building a Perplexity/SurfSense hybrid.**

### Key Strengths:
- ✅ Production-ready RAG framework (best-in-class)
- ✅ 300+ data connectors (exceeds SurfSense)
- ✅ Built-in citation support (Perplexity requirement)
- ✅ Flexible architecture (swap any component)
- ✅ Strong community + documentation
- ✅ MIT license (commercial-friendly)

### What You'll Still Need to Build:
- User management + RBAC
- Frontend (Next.js or similar)
- Real-time collaboration
- Deployment infrastructure

### Recommended Path:
Start with **Option 2** (fork SurfSense, swap in LlamaIndex) for fastest MVP, then migrate to **Option 1** (ground-up) if you need custom architecture.

---

**Status**: Initial evaluation complete. Ready for POC phase.
