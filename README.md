# A Penny For My Thought - AI-powered journaling web app

Journaling is something I’ve tried over and over again during tough days, but I never quite learned how. As someone who's always been reserved and emotionally closed off (I'm working on it!), I struggle to talk about myself honestly and vulnerably, even to the blank pages of my own private journal.

So I thought, maybe turning it into a conversation would make it less daunting.

Hopefully, this becomes a safe and more open space for myself.

---

*Now onto the definitely AI-generated content :)*

## Overview

An LLM-powered journaling web app, built with FastAPI and Next.js. The application provides a conversational interface for journaling with AI assistance, featuring persistent storage, semantic search across past conversations, and real-time streaming responses.

## Features

- **Conversational AI Journaling**: Chat with an AI assistant for journaling
- **Persistent Storage**: Conversations automatically saved in SQLite database
- **Semantic Search**: RAG-powered context retrieval from past conversations using ChromaDB
- **Real-time Streaming**: ChatGPT-like streaming responses with Server-Sent Events
- **Mobile Responsive**: Works perfectly on mobile and desktop with responsive design
- **Error Handling**: Comprehensive error handling with retry mechanisms
- **Context Management**: Dynamic conversation summarization for context window management

## Key Technologies

**Backend**:
- FastAPI
- OpenAI API
- ChromaDB (vector database for RAG)
- SQLite (conversation storage)
- Pydantic (data validation)
- Uvicorn (ASGI server)
- Tenacity (retry logic)

**Frontend**:
- Next.js
- Tailwind
- shadcn/ui

## Architecture

```
├── backend/          # FastAPI Python backend
│   ├── app/         # Application code
│   │   ├── api/v1/  # REST API endpoints (chat, journals)
│   │   ├── services/ # Business logic (chat, journal, LLM, RAG)
│   │   ├── models/  # Pydantic data models
│   │   ├── storage/ # Database and vector storage
│   │   └── utils/   # Utility functions
│   ├── tests/       # Unit tests
│   ├── chat_history.db # SQLite database
│   └── chroma_db/   # ChromaDB vector database
├── frontend/         # Next.js React frontend
│   ├── app/         # Next.js App Router pages
│   ├── components/  # React components
│   │   ├── chat/    # Chat interface components
│   │   ├── journals/    # Journal management
│   │   ├── layout/ # Layout components
│   │   └── ui/      # shadcn/ui components
│   └── lib/         # Utilities, API clients, and context
└── doc/             # Documentation
```

## Quick Start

### Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **OpenAI API Key** (for AI functionality)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd a-penny-for-my-thought

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
```

### 2. Configure Environment

**Backend** (`backend/.env`):

Copy `backend/env_template.txt` to `backend/.env`.

Provide your OpenAI API key.

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional (defaults provided)
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DB_DIRECTORY=./chroma_db
DATABASE_PATH=./chat_history.db
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
STREAMING_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO
```

**Frontend** (`frontend/.env`):

Copy `frontend/env_template.txt` to `frontend/.env`.

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run the Application

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### 4. Access the App

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## API Documentation

The backend provides comprehensive API documentation:

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints

**Chat Endpoints**:
- `POST /api/v1/chat` - Send chat message (non-streaming)
- `POST /api/v1/chat/stream` - Stream chat response (Server-Sent Events)

**Journal Endpoints**:
- `GET /api/v1/journals` - List conversations with pagination
- `GET /api/v1/journals/{id}` - Get specific conversation
- `POST /api/v1/journals` - Save conversation
- `DELETE /api/v1/journals/{id}` - Delete conversation

**Health Check**:
- `GET /health` - Health check endpoint

## Deployment

### Backend Deployment
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment
```bash
cd frontend
npm run build
npm start
```