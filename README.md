# Production-Grade Corrective RAG (CRAG) Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.9-blue.svg?style=flat)](https://python.langchain.com/docs/langgraph)
[![Cohere](https://img.shields.io/badge/Cohere-Command--R7B-purple.svg?style=flat)](https://cohere.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Serverless_Vector_DB-000000.svg?style=flat)](https://www.pinecone.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Async_SQLModel-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.4-DC382D.svg?style=flat&logo=redis)](https://redis.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python)](https://www.python.org/)

A high-performance, production-ready backend service powering conversational Retrieval-Augmented Generation (RAG). Built using **FastAPI**, **LangGraph**, **Cohere LLM & Embeddings**, **Pinecone Vector Database**, and **PostgreSQL**, this backend implements an adaptive **Corrective RAG (CRAG)** architecture with real-time Server-Sent Events (SSE) streaming, page-aware PDF processing, and enterprise-grade authentication.

---

## Architecture Overview

```
                                    +-----------------------+
                                    |     Client / UI       |
                                    +-----------+-----------+
                                                |
                                     HTTP / SSE (Streaming)
                                                v
                                    +-----------+-----------+
                                    |     FastAPI Service   |
                                    +-----------+-----------+
                                                |
                      +-------------------------+-------------------------+
                      |                                                   |
                      v                                                   v
       +--------------+--------------+                     +--------------+--------------+
       |   Document Ingestion Pipeline|                     |    LangGraph Agent (CRAG)    |
       +--------------+--------------+                     +--------------+--------------+
       | • PyMuPDF (fitz) page parse |                     | • Router Node (LLM + Tools)  |
       | • Recursive Text Splitter   |                     | • Pinecone Search Tool       |
       | • Cohere Batch Embeddings   |                     | • Doc Relevance Grader Node  |
       | • Async Vector Upsert       |                     | • Query Rewriter / Loop      |
       | • Supabase Cloud Storage    |                     | • Context-Bound Generator    |
       +--------------+--------------+                     +--------------+--------------+
                      |                                                   |
                      +-------------------------+-------------------------+
                                                |
                                                v
                            +-------------------+--------------------+
                            |    Persistence & Storage Infrastructure|
                            | • PostgreSQL (SQLModel + AsyncPool)|
                            | • AsyncPostgresSaver (Checkpoints) |
                            | • Redis (OTP TTL & User Blacklist) |
                            | • Pinecone (Vector Index + Meta)   |
                            +----------------------------------------+
```

### The Corrective RAG (CRAG) Workflow

```
[START] --> [agent] --(tool call?)--> [tools] --> [sync_artifacts_node] --> [grade_docs]
             |                                                                   |
          (no tool)                                                       (relevant or loop>=2?)
             |                                                                  /    \
             v                                                                YES     NO
           [END]                                                              /        \
                                                                     [generator]  [query_transformer]
                                                                          |              |
                                                                        [END] <----------+
```

1. **Routing (`agent`)**: Evaluates user input and conditionally invokes the Pinecone retriever tool if contextual lookup is required.
2. **Retrieval (`tools` & `sync_artifacts_node`)**: Fetches vector embeddings filtered by `conversation_id` and attaches chunk metadata (filename, page number, score).
3. **Document Relevance Grading (`grade_docs`)**: Employs Cohere with structured output (`GradeDocuments`) to audit whether retrieved chunks semantically answer the query.
4. **Query Rewriting Loop (`query_transformer`)**: If context is graded irrelevant, the system optimizes search keywords (prohibiting previous failed phrases) and re-executes retrieval. Includes a maximum loop cap (`loop_count >= 2`) to prevent infinite execution.
5. **Answer Generation (`generator`)**: Synthesizes a factual response bounded strictly to validated context, attaching full source citations.

---

## Features

- **Adaptive CRAG Architecture**: Intelligent state graph orchestrating document grading, search rewriting, and strict context-bound generation.
- **Real-Time Streaming (SSE)**: Asynchronous Server-Sent Events delivering token-by-token LLM output, tool execution status updates, document citations, and live upload progress bars.
- **Page-Aware Ingestion Pipeline**: Extracts text per page using PyMuPDF (`fitz`), recursively splits chunks (500 chars / 15 overlap), generates automatic thread titles, and performs async batch vector upserts into Pinecone.
- **Multi-Tenant Data Isolation**: Strict user-level and conversation-level authorization enforced across PostgreSQL queries and Pinecone metadata filters (`conversation_id`).
- **Dual Authentication**:
  - Email/Password authentication with 6-digit OTP verification backed by Redis TTL cache.
  - Native Google OAuth 2.0 token exchange flow.
- **Fault-Tolerant Task Cleanup**: Automatic coroutines clean up partially uploaded Supabase files, database metadata, and Pinecone vectors if a client cancels an ongoing upload mid-process.
- **Stateful Conversation Memory**: Powered by LangGraph's `AsyncPostgresSaver` checkpointing backed by `psycopg_pool` connection pooling.

---

## Tech Stack

| Domain | Technology | Role |
| :--- | :--- | :--- |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Asynchronous web framework & SSE endpoint provider |
| **Agent Orchestration** | [LangGraph](https://python.langchain.com/docs/langgraph) | Stateful graph engine managing CRAG execution & checkpointing |
| **LLM & Embeddings** | [Cohere](https://cohere.com/) | `Command-R7B` chat model & `embed-english-v3.0` embeddings |
| **Vector Database** | [Pinecone](https://www.pinecone.io/) | Serverless vector index with metadata filtering |
| **Database & ORM** | [PostgreSQL](https://www.postgresql.org/) + [SQLModel](https://sqlmodel.tiangolo.com/) | Asynchronous relational data modeling & checkpoint persistence |
| **Caching & OTP** | [Redis](https://redis.io/) | Temporary registration cache, OTP storage with TTL, user blacklist |
| **File Storage** | [Supabase Storage](https://supabase.com/storage) | Cloud object storage for uploaded PDF documents |
| **PDF Processing** | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) | Page-by-page PDF parsing and layout extraction |

---

## Project Structure

```
Rag_Backend/
├── app/
│   ├── api/                  # API routes and dependencies
│   │   ├── deps.py           # Dependency injection (Auth, Services, DB)
│   │   └── v1/               # Version 1 route endpoints
│   │       ├── auth_routes.py
│   │       ├── conversation_routes.py
│   │       ├── document_routes.py
│   │       ├── router.py
│   │       └── user_routes.py
│   ├── core/                 # App configuration, security & client factories
│   │   ├── config.py         # Pydantic Settings configuration
│   │   ├── embeddings.py     # Cohere Embeddings client
│   │   ├── lifespan.py       # App lifespan setup (pools, DB init, LangGraph)
│   │   ├── llm.py            # Cohere LLM client setup
│   │   ├── pinecone_client.py# Pinecone index initialization
│   │   ├── redis_client.py   # Redis connection factory
│   │   └── security.py       # JWT creation & password hashing
│   ├── db/                   # Database session and connection pooling
│   │   ├── conv_checkpoint_pool.py # AsyncConnectionPool for LangGraph
│   │   ├── init_db.py        # Table initialization
│   │   └── session.py        # Async engine factory
│   ├── enums/                # User roles and system enums
│   ├── exceptions/           # Custom exception models & HTTP exception handlers
│   ├── llm_prompts/          # System prompts for grading, transform & generation
│   ├── models/               # SQLModel table definitions (User, Conversation, Document)
│   ├── render_messages/      # SSE streaming event transformers & handlers
│   ├── repository/           # Data access layer (User, Conversation, Document)
│   ├── schema/               # Pydantic schemas (AgentState, Chat, Events, User)
│   ├── services/             # Business logic layer
│   │   ├── agent_service.py  # LangGraph CRAG workflow & chat streaming
│   │   ├── auth_service.py   # Auth, OTP via Redis, Google OAuth
│   │   ├── conversation_service.py # Chat history & checkpoint deletion
│   │   ├── document_service.py # PDF processing, chunking & Pinecone upsert
│   │   ├── email_service.py  # SMTP OTP dispatch
│   │   └── user_service.py   # Profile & user management
│   ├── tools/                # LangChain tools (Retriever tool for Pinecone)
│   └── main.py               # FastAPI application entrypoint
├── tests/                    # Pytest test suite & notebooks
├── docker-compose.yml        # Docker compose service setup
├── dockerfile                # App containerization image file
├── pytest.ini                # Pytest configuration
└── requirements.txt          # Python dependencies
```

---

## Environment Configuration

Create a `.env` file in the project root:

```env
# Application Setup
ENV=development
DEBUG=True
API_VERSION=v1
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# PostgreSQL Configuration
DB=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Cohere LLM & Embedding Key
COHERE_API_KEY=your_cohere_api_key

# Pinecone Vector DB Configuration
PINECONE_DB_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=rag-index
EMBEDDING_DIMENSION=1024

# Redis Configuration
REDIS_URI=redis://localhost:6379/0
REDIS_MEMORY_TIME=3600

# JWT Security
JWT_SECRET_KEY=your_super_secret_jwt_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=2000

# Supabase Storage Setup
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

# Google OAuth 2.0 Credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Email Service Credentials (Gmail SMTP)
GMAIL_SENDER=your_email@gmail.com
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token
```

---

## Quick Start

### 1. Prerequisites

- **Python**: `v3.11+`
- **PostgreSQL**: `v14+`
- **Redis**: `v7+`
- **Docker & Docker Compose** *(Optional)*

### 2. Local Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/Rag_Backend.git
cd Rag_Backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running Services locally

Ensure PostgreSQL and Redis are running locally, then start the FastAPI application server using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`. You can inspect the interactive OpenAPI swagger documentation at `http://localhost:8000/docs`.

### 4. Running via Docker Compose

```bash
# Build and run containers
docker-compose up --build -d
```

---

## API Endpoints Reference

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Initiates email registration & sends OTP code via Redis | No |
| `POST` | `/auth/verify-email` | Verifies OTP code and creates user account | No |
| `POST` | `/auth/login` | Authenticates user credentials & returns JWT access token | No |
| `GET` | `/auth/google` | Initiates Google OAuth 2.0 authorization redirect | No |
| `GET` | `/auth/google/callback` | Handles OAuth code exchange and issues backend JWT | No |

### Document Management (`/api/v1/documents`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/documents/upload` | Uploads PDF, parses text, embeds, & streams processing progress via SSE | Yes |
| `GET` | `/documents/conversation/{conversation_id}` | Retrieves metadata for all documents linked to a conversation | Yes |
| `GET` | `/documents/{document_id}/stream` | Streams raw file content from Supabase storage | Yes |
| `DELETE` | `/documents/{document_id}` | Removes document metadata, Supabase file, and Pinecone vectors | Yes |

### Conversation & Agent Streaming (`/api/v1/conversations`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/conversations/chat` | Executes CRAG agent graph and streams response via SSE | Yes |
| `GET` | `/conversations` | Lists all conversation threads for the authenticated user | Yes |
| `GET` | `/conversations/{thread_id}/messages` | Fetches historical chat messages from LangGraph checkpointer | Yes |
| `DELETE` | `/conversations/{conversation_id}` | Deletes conversation thread, checkpoints, storage, & vectors | Yes |

---

## Testing

Run the test suite using `pytest`:

```bash
pytest tests/
```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
