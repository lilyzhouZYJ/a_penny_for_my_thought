# A Penny For My Thought - AI-Powered Journaling Web App

An LLM-powered journaling web application with conversational interface, built with FastAPI and Next.js.

## 🌟 Features

- **Conversational AI Journaling**: Chat with an AI assistant for journaling
- **Persistent Storage**: Conversations saved as Markdown files
- **Semantic Search**: RAG-powered context from past conversations
- **Real-time Streaming**: ChatGPT-like streaming responses
- **Mobile Responsive**: Works perfectly on mobile and desktop
- **Auto-save**: Conversations automatically saved after each message
- **Shareable URLs**: Bookmark and share specific conversations

## 🏗️ Architecture

```
├── backend/          # FastAPI Python backend
│   ├── app/         # Application code
│   ├── journals/    # Markdown conversation storage
│   └── chroma_db/   # Vector database for RAG
├── frontend/         # Next.js React frontend
│   ├── app/         # Next.js App Router pages
│   ├── components/  # React components
│   └── lib/         # Utilities and API clients
└── .spec-workflow/  # Specification and design docs
```

## 🚀 Quick Start

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
```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional (defaults provided)
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
JOURNALS_DIRECTORY=./journals
VECTOR_DB_DIRECTORY=./chroma_db
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

**Frontend** (`frontend/.env.local`):
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

## 📖 Usage

1. **Start a New Conversation**: Click "New Conversation" or visit `/`
2. **Chat**: Type your thoughts and get AI responses
3. **View Past Conversations**: Use the sidebar to browse and load previous chats
4. **Share**: Copy the URL to bookmark or share specific conversations

## 🛠️ Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run tests
pytest

# Run with auto-reload
uvicorn app.main:app --reload

# Check API docs
open http://localhost:8000/docs
```

### Frontend Development

```bash
cd frontend

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Key Technologies

**Backend**:
- FastAPI (Python web framework)
- OpenAI API (GPT-4o, text-embedding-3-small)
- ChromaDB (vector database)
- Pydantic (data validation)
- Uvicorn (ASGI server)

**Frontend**:
- Next.js 14 (React framework)
- TypeScript (type safety)
- Tailwind CSS (styling)
- shadcn/ui (component library)
- React Context (state management)

## 📁 Project Structure

### Backend (`/backend`)
- `app/main.py` - FastAPI application entry point
- `app/models/` - Pydantic data models
- `app/services/` - Business logic (LLM, RAG, Chat, Journal)
- `app/storage/` - File and vector storage
- `app/api/v1/` - REST API endpoints
- `app/utils/` - Utility functions

### Frontend (`/frontend`)
- `app/` - Next.js App Router pages
- `components/` - React components
  - `chat/` - Chat interface components
  - `conversations/` - Conversation list components
  - `layout/` - Layout components
  - `shared/` - Shared UI components
- `lib/` - Utilities and API clients

## 🔧 Configuration

### Environment Variables

See `backend/env_template.txt` and `frontend/env_template.txt` for all available options.

### Key Settings

- **`OPENAI_API_KEY`**: Required for AI functionality
- **`NEXT_PUBLIC_API_URL`**: Backend API URL for frontend
- **`RAG_TOP_K`**: Number of context chunks to retrieve
- **`STREAMING_ENABLED`**: Enable/disable real-time streaming

## 🧪 Testing

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

## 📚 API Documentation

The backend provides comprehensive API documentation:

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints

- `POST /api/v1/chat` - Send chat message
- `POST /api/v1/chat/stream` - Stream chat response
- `GET /api/v1/journals` - List conversations
- `GET /api/v1/journals/{id}` - Get specific conversation
- `POST /api/v1/journals` - Save conversation
- `DELETE /api/v1/journals/{id}` - Delete conversation

## 🚀 Deployment

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the [API documentation](http://localhost:8000/docs)
2. Review the environment setup
3. Check the logs for error messages
4. Ensure your OpenAI API key is valid

## 🎯 Roadmap

- [ ] User authentication and multi-user support
- [ ] Export conversations to PDF
- [ ] Advanced search and filtering
- [ ] Conversation categories and tags
- [ ] Offline mode support
- [ ] Mobile app (React Native)