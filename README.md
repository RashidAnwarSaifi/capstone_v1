# Enterprise Document Q&A Agent (GenAI Capstone)

A Streamlit app with a multi-page UI (Home / Agents / Sources / Settings)
that lets you upload enterprise documents (PDF, TXT, CSV, Excel), builds a
local vector knowledge base from them, and answers follow-up questions in a
chat UI using Retrieval-Augmented Generation (RAG) and a choice of AI
agents. Conversations and LLM settings persist in the browser's IndexedDB.

## Setup

1. **Create a virtual environment and install dependencies**

use Python 3.13 or lower not 3.14

```bash
# Windows
python3.13 -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3.13 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

2. **Run the app**

```bash
.venv/bin/python -m streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Architecture

A graphical diagram of the same layout described below is in
[`docs/architecture.html`](docs/architecture.html) (editable Mermaid
diagram-as-code; open it in a browser, or use the **Architecture** link in
the app's sidebar). If the CDN it loads its renderer from is blocked on your
network, paste the `<pre class="mermaid">` block into
[mermaid.live](https://mermaid.live) instead.

app.py                      Entry point: page config + routing to the ui/ pages
ui/                         Streamlit UI, one module per concern
  state.py                  Session state, IndexedDB hydration, document ingestion
  sidebar.py                Sidebar nav, chat list, user badge
  home.py                   Home/chat page: history, send flow, running agents
  pages.py                  Agents / Sources / Settings / Architecture / Instructions
  styles.py                 Loads the static assets below
  static/                   Plain .css/.js assets (no Python strings)
config/settings.py          All configuration, loaded from .env
llm/                        Swappable LLM layer
  base.py                   BaseLLM interface (generate())
  groq_client.py            Groq implementation (default)
  gemini_client.py          Gemini implementation (secondary option)
  factory.py                get_llm(overrides) builds the right client from .env or Settings-page overrides
ingestion/                  Document loading + chunking
  loaders.py                PDF / TXT / CSV / Excel -> raw text
  chunker.py                raw text -> overlapping chunks
vectorstore/store.py        Chroma-backed vector store (add / query / delete-by-source / clear)
vectorstore/embeddings.py   Local Hugging Face sentence-transformer embedding model
agents/                     Selectable agents, all implementing BaseAgent.run()
  base.py                   BaseAgent interface
  qa_agent.py               Document Q&A Agent: plan -> retrieve -> reason -> validate
  summarizer_agent.py       Summarizer Agent: retrieve -> bullet-point summary
  fact_checker_agent.py     Fact-Checker Agent: draft -> itemized claim-by-claim check
  registry.py               AGENTS registry the chat UI's agent picker uses
storage/indexeddb.py        Browser IndexedDB bridge (conversations + LLM setting overrides)
utils/guardrails.py         Input validation and grounding checks
data/                       Uploaded files + Chroma DB (server-local, gitignored)

### Switching LLM providers

Every backend (`groq_client.py`, `gemini_client.py`) implements the same
`BaseLLM.generate()`. `llm/factory.py` builds the right one from either
`.env` (`LLM_PROVIDER`) or a runtime `overrides` dict coming from the
**Settings** page. Default provider is **`groq`**; **`gemini`** is the
secondary option. No code changes are needed to switch providers.

### Where things are stored

- **Conversations** and **LLM setting overrides** (provider/model/API keys
  you edit in Settings) live in the browser's **IndexedDB**
  (`storage/indexeddb.py`, driven from Python via `streamlit_javascript`) -
  not on the server disk. Each browser/profile has its own chat history and
  settings. "Reset to .env defaults" on the Settings page clears the
  IndexedDB override so the app falls back to `.env`.
- **Uploaded documents** and the **Chroma vector database** live on the
  server disk under `data/` (gitignored), since that's what the retrieval
  pipeline needs to search.

### Agents

Three agents are registered in `agents/registry.py` and selectable (single
or multiple) from the multiselect above the chat box on the Home page:

| Agent | What it does |
|---|---|
| **Document Q&A Agent** | plan (query rewrite) -> retrieve -> reason (draft answer) -> validate (grounding check) |
| **Summarizer Agent** | retrieve -> bullet-point summary of the relevant content |
| **Fact-Checker Agent** | draft an answer -> itemize each claim as Supported/Unsupported against the sources |

Selecting multiple agents runs each one against the same question and shows
each as its own labeled chat bubble with its own trace, so you can compare
outputs side by side.

### Document selection

The Sources page lists every uploaded document with a delete button. The
"Limit to documents" multiselect on the Home page scopes retrieval to
specific files (via a Chroma metadata filter); leave it empty to search all
indexed documents.

## Using the app

1. **Sources** page -> upload one or more documents (PDF, TXT, CSV, XLSX) and
   click **Process documents**. This extracts text, chunks it, embeds the
   chunks, and stores them in the local Chroma vector database
   (`data/chroma/`). Delete individual documents or clear the whole
   knowledge base from the same page.
2. **Home** page -> pick one or more agents and optionally scope to specific
   documents, then ask a question in the chat box. Each selected agent
   replies as its own labeled bubble with sources and an expandable trace.
3. **Agents** page -> reference/catalog of what each agent does.
4. **Settings** page -> pick an LLM provider and edit its model/API key; Save
   persists it to your browser's IndexedDB. Reset falls back to `.env`.
5. Sidebar -> **New chat** starts a fresh conversation; each conversation is
   listed under "Recent chats" (click to switch, 🗑️ to delete). All of this
   is stored in your browser's IndexedDB. **Architecture** and
   **Instructions** links open the architecture diagram and this README
   from inside the app.

## Task coverage (capstone brief, 1-10)

1. **Project foundation** - modular package layout (`config/`, `llm/`,
   `ingestion/`, `vectorstore/`, `agents/`, `storage/`, `utils/`), `.env`-driven
   configuration, `requirements.txt` frozen from a real install.
2. **User interaction layer** - Streamlit multi-page UI: Home (chat), Agents,
   Sources (upload/ask), Settings.
3. **Document ingestion** - `ingestion/loaders.py` handles PDF, TXT, CSV, XLSX/XLS.
4. **Data prep for semantic search** - `ingestion/chunker.py` splits text into
   overlapping chunks sized via `.env` (`CHUNK_SIZE`/`CHUNK_OVERLAP`).
5. **Vector-based knowledge store** - `vectorstore/store.py` (Chroma, persisted
   to disk) + `vectorstore/embeddings.py` (local Hugging Face
   sentence-transformer model, downloaded from the HF Hub on first use).
6. **Intelligent document retrieval** - `VectorStore.query()` with cosine
   similarity search and optional per-document filtering.
7. **RAG pipeline** - every agent combines retrieved chunks with an LLM call
   to produce a grounded response (see `agents/qa_agent.py` and friends).
8. **Agent-based reasoning** - three agents in `agents/registry.py`
   (Q&A, Summarizer, Fact-Checker), user-selectable single or multi, each
   planning/retrieving/reasoning/validating with an inspectable trace.
9. **Reliability & safety controls** - `utils/guardrails.py` (input/upload
   validation, no-context fallback), per-agent grounding checks, try/except
   around every LLM and ingestion call in `app.py`.
10. **Documentation** - this README (architecture, setup, usage) plus inline
    "why" comments at key decision points.
