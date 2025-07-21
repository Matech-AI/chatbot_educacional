# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "DNA da Força" - an educational AI system for physical training using RAG (Retrieval-Augmented Generation). The system consists of a React/TypeScript frontend and a FastAPI backend with Google Drive integration, ChromaDB vector storage, and LangGraph-based chat agent.

## Development Commands

### Frontend (React + Vite)
- **Development server**: `npm run dev` (runs on port 3000)
- **Build**: `npm run build` (TypeScript compilation + Vite build)
- **Lint**: `npm run lint` (ESLint with TypeScript support)
- **Preview**: `npm run preview`
- **Start**: `npm run start` (development with host binding)

### Backend (FastAPI + Python)
- **Start backend**: `cd backend && uvicorn main_simple:app --host 0.0.0.0 --port 8000 --reload`
- **Alternative start**: `cd backend && python start_backend.py`
- **Install dependencies**: `cd backend && pip install -r requirements.txt`
- **Activate virtual environment**: 
  - Windows: `.venv\Scripts\activate`
  - Linux/Mac: `source .venv/bin/activate`

### Testing and Debug
- **Test Google Drive connection**: `python backend/test_drive_connection.py`
- **Health check**: `curl http://localhost:8000/health`
- **API documentation**: http://localhost:8000/docs

## Architecture

### Frontend Architecture
- **Framework**: React 18 + TypeScript + Vite
- **State Management**: Zustand stores (`src/store/`)
  - `auth-store.ts`: Authentication and user management
  - `chat-store.ts`: Chat sessions and messages
  - `materials-store.ts`: Material management
  - `assistant-store.ts`: AI assistant configuration
- **Routing**: React Router with protected routes
- **Styling**: Tailwind CSS + Radix UI components
- **API Layer**: Centralized in `src/lib/api.ts` with proxy to backend

### Backend Architecture
- **Main API**: `backend/main_simple.py` (FastAPI application)
- **Authentication**: JWT-based auth in `backend/auth.py`
- **RAG System**: `backend/rag_handler.py` (ChromaDB + OpenAI embeddings)
- **Chat Agent**: `backend/chat_agent.py` (LangGraph + Google Gemini)
- **Google Drive**: `backend/drive_handler_recursive.py` for file synchronization
- **Data Storage**: 
  - Vector DB: ChromaDB (`.chromadb/` directory)
  - Materials: `backend/data/materials/`
  - Users: `users.json` file

### Key Integration Points
- **API Proxy**: Frontend `/api/*` routes proxy to `localhost:8000`
- **Authentication**: JWT tokens stored in Zustand auth store
- **File Upload**: Supports manual upload and Google Drive sync
- **Chat System**: Supports multiple sessions with source citations

## Configuration Files

### Environment Variables
- **Backend**: Requires `OPENAI_API_KEY`, optional `GOOGLE_DRIVE_API_KEY`
- **Google OAuth**: `backend/credentials.json` for private Drive access
- **Frontend**: Uses `env.example` as template

### Important Config Files
- `vite.config.ts`: Frontend dev server and API proxy configuration
- `backend/requirements.txt`: Python dependencies including LangGraph, OpenAI, Google APIs
- `tsconfig.json`: TypeScript configuration with path aliases (`@/` → `./src/`)

## User Roles and Authentication
- **Admin**: Full system access
- **Instructor**: Material management and chat access  
- **Student**: Chat access only
- Default users defined in `users.json`

## Google Drive Integration
- Supports both public (API key) and private (OAuth2) folder access
- Recursive folder scanning with file type filtering
- Automatic material indexing into vector database
- Debug interface available at `/materials` page

## Development Workflow
1. Start backend: `cd backend && uvicorn main_simple:app --reload`
2. Start frontend: `npm run dev`
3. Access frontend at http://localhost:3000
4. API docs at http://localhost:8000/docs
5. Use `/materials` debug tab for system diagnostics