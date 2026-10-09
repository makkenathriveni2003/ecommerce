# ShopZone Day 20 AI Focus — Full Stack Implementation Guide

## 1. Overview & Architecture
The Day 20 AI Focus implementation adds an end-to-end AI Shopping Assistant to ShopZone. It integrates multi-provider LLM support (Google Gemini, Groq, Mistral, OpenAI), Server-Sent Events (SSE) streaming chat, an intelligent fallback strategy, and Retrieval-Augmented Generation (RAG) strictly grounded in ShopZone's PostgreSQL product catalog.

```
 +-------------------------------------------------------------------------+
 |                     ShopZone React 19 Frontend                          |
 |  (/ai-assistant route, AICitationCard, SSE Stream Reader, AbortController) |
 +------------------------------------+------------------------------------+
                                      | POST /api/ai/chat/stream (SSE)
                                      v
 +-------------------------------------------------------------------------+
 |                     FastAPI Backend (/api/ai/...)                       |
 |                                                                         |
 |  +-----------------------+      +------------------------------------+  |
 |  |   AIChatOrchestrator  | <--> |     ChromaVectorStore (Local)      |  |
 |  +-----------+-----------+      |   (38+ Products Chunked & Indexed) |  |
 |              |                  +-----------------+------------------+  |
 |              v                                    |                     |
 |  +-----------------------+                        | Recursive Text      |
 |  |  AIFallbackManager    |                        | Splitter & Embedder |
 |  +-----------+-----------+                        v                     |
 |              |                 +--------------------------------------+ |
 |              |                 | PostgreSQL Catalogue (Product Table) | |
 |              |                 +--------------------------------------+ |
 |              +-----------------------------------------+                |
 |              |                    |                    |                |
 |              v                    v                    v                |
 |     +-----------------+  +-----------------+  +-----------------+       |
 |     | Gemini Provider |  |  Groq Provider  |  | Mistral Provider|       |
 |     +-----------------+  +-----------------+  +-----------------+       |
 +-------------------------------------------------------------------------+
```

---

## 2. Supported LLM Providers & Models

| Provider | Supported Models | Env API Key | Streaming Protocol | Free Tier Status |
| :--- | :--- | :--- | :--- | :--- |
| **Google Gemini** | `gemini-1.5-flash`, `gemini-1.5-pro` | `GEMINI_API_KEY` | Native SSE via Google API | Free Tier available via Google AI Studio |
| **Groq** | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` | `GROQ_API_KEY` | OpenAI-compatible SSE | Generous free rate limits for developers |
| **Mistral** | `mistral-small-latest`, `open-mistral-7b` | `MISTRAL_API_KEY` | OpenAI-compatible SSE | Free API access tier |
| **OpenAI Compatible** | Configurable via `OPENAI_MODEL` | `OPENAI_API_KEY` | SSE standard format | Pay-per-token or local models (e.g. Ollama/vLLM) |

---

## 3. Environment Variables Configuration

Set these in `backend/.env`:

```env
# AI Primary Provider and Fallback Order
AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_PROVIDERS=groq,mistral,openai
AI_MAX_RETRIES=2
AI_TIMEOUT_SECONDS=30.0

# LLM Credentials
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-small-latest

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1

# ChromaDB & Embeddings Configuration
CHROMA_PERSIST_DIRECTORY=chroma_db
CHROMA_COLLECTION_NAME=shopzone_catalog
EMBEDDING_PROVIDER=local_hash
EMBEDDING_MODEL=text-embedding-004
```

> **Security Note:** All API keys are loaded strictly on the backend and are never sent to the browser or logged in request traces.

---

## 4. RAG Pipeline & Catalog Sync

1. **Text Chunking**: Products are converted to informative documents with fields: Name, Category, Price in INR (`₹`), Stock, and Description. They are split into manageable chunks using LangChain's `RecursiveCharacterTextSplitter`.
2. **Embeddings**: Supports `local_hash` (deterministic, zero-dependency 384-dimensional fallback for offline/test reliability) as well as `gemini` and `mistral` embedding models.
3. **ChromaDB Storage**: Stored persistently under `backend/chroma_db/`.
4. **Synchronization**:
   - Initialized at application lifespan startup.
   - Incrementally updated whenever products are created or updated via `ProductService`.
   - Admin re-indexing CLI script:
     ```powershell
     cd backend
     python scripts/reindex_catalog.py
     ```
   - Admin re-indexing HTTP endpoint: `POST /api/ai/index/reindex` (Requires Admin Bearer token).

---

## 5. Streaming API Protocol (SSE)

Endpoint: `POST /api/ai/chat/stream`
Payload:
```json
{
  "message": "Which headphones are available under ₹3,000?",
  "conversation_history": []
}
```

Events dispatched over `text/event-stream`:
- `event: provider` — Selected provider and model: `{"provider": "gemini", "model": "gemini-1.5-flash"}`
- `event: citations` — Array of matching products: `[{"product_id": 3, "product_name": "Headphones", "category": "Accessories", "price": 3000.0, "stock": 50, "url": "/products/3"}]`
- `event: chunk` — Token stream: `{"chunk": "ShopZone offers..."}`
- `event: provider_change` — Emitted during fallback: `{"from": "gemini", "to": "groq", "reason": "rate_limit"}`
- `event: done` — Completion signal: `{"status": "completed", "provider": "gemini", "citations_count": 1}`
- `event: error` — Safe sanitized error: `{"error": "Failed to generate response."}`

---

## 6. Prompt Engineering & Defense
The assistant uses `SHOPZONE_SYSTEM_PROMPT` located in `backend/app/services/ai/prompts.py`:
- **Catalog Grounding**: The assistant answers strictly using the `<verified_catalogue_context>` block.
- **Hallucination Prevention**: If a product is not in the catalogue, the assistant explicitly states that ShopZone does not carry it and suggests existing items.
- **Currency Compliance**: All prices are formatted in Indian Rupees (`₹`).
- **Untrusted Context Isolation**: Retrieved descriptions and user prompts are treated as untrusted data to defend against indirect prompt injections and jailbreaks.

---

## 7. Frontend Integration
- **Route**: Accessible at `/ai-assistant` and linked in the navigation bar.
- **Features**:
  - Progressive token streaming using `ReadableStream` reader.
  - Interactive clickable citation cards (`AICitationCard`) linking directly to `/products/:id`.
  - Quick-start recommendation pills for fast queries.
  - Full keyboard accessibility: `Enter` to send, `Shift+Enter` for newlines.
  - Generation controls: `Stop` button via `AbortController` and `Clear` button.
  - Error state handling with seamless retry capability.
  - Mobile responsive matching ShopZone's modern design tokens (`--green`, `--surface`, `--line`, `--ink`).

---

## 8. Verification & Running Tests

### Backend Tests
```powershell
cd backend
..\.venv\Scripts\pytest.exe -v
```
All 64 backend tests pass (17 AI feature tests + 22 existing backend tests + 25 Day 18 tests).

### Frontend Tests & Build
```powershell
cd frontend
npm run typecheck
npm run lint
npm test -- --run
npm run build
```
All frontend test suites pass, TypeScript reports 0 errors, and the production build compiles cleanly.
