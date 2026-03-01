<<<<<<< HEAD
# Codebase Aware Developer Assistant

A custom RAG-based code analysis assistant that indexes local repositories and answers questions using retrieved code context. The project combines a FastAPI backend, SQLite storage, local embeddings, and a lightweight React frontend to let users register a codebase, build an index, and ask grounded questions with citations.

## Project Overview

This project is designed to help developers explore and understand a local codebase through retrieval-augmented question answering.

Instead of sending an entire repository directly to a model, the backend:

- scans supported files from a selected project directory
- splits file content into manageable chunks
- converts those chunks into embeddings
- stores chunks and embeddings in SQLite
- retrieves the most relevant chunks for a user question
- generates a grounded answer and returns citations with file paths and line ranges

The backend is a custom RAG pipeline. It does not use LangChain or a vector database. Retrieval, chunking, embedding storage, and scoring are implemented directly in the application code.

## Features

- Register a local project path for indexing
- Scan source and config files from the selected repository
- Chunk file contents with tracked line ranges
- Generate embeddings for code and questions using `sentence-transformers`
- Store project metadata, chunks, and embeddings in `SQLite`
- Retrieve the most relevant chunks with similarity scoring
- Return answers with file and line citations
- Provide a simple browser-based UI for project registration, indexing, and querying
- Include automated tests for core API flows

## Architecture

### High-Level Flow

1. A user registers a project path.
2. The backend scans the project and collects supported files.
3. Each file is split into chunks.
4. Each chunk is converted into an embedding.
5. Chunks and embeddings are stored in SQLite.
6. When the user asks a question, the backend embeds the question.
7. The backend compares the question embedding with stored chunk embeddings.
8. The top matching chunks are selected as context.
9. The system generates or assembles an answer using the retrieved context.
10. The response is returned with citations.

### Backend Components

- `app/main.py`
  Creates the FastAPI application, registers middleware, mounts the frontend, and wires up API routes.

- `app/api/routes/projects.py`
  Handles project registration, indexing, and question-answer endpoints.

- `app/api/routes/filesystem.py`
  Exposes directory browsing for selecting a local project folder.

- `app/api/routes/health.py`
  Provides a basic health/status endpoint.

- `app/services/indexing.py`
  Handles file discovery, text reading, chunking, timestamp generation, and embedding serialization helpers.

- `app/services/llm.py`
  Loads the embedding model and optional Hugging Face text-generation model.

- `app/services/qa.py`
  Implements answer-generation logic, retrieval-based answer construction, and heuristic fallbacks.

- `app/db/database.py`
  Initializes the SQLite database and manages connections.

- `app/db/repositories.py`
  Encapsulates project and chunk persistence operations.

- `frontend/`
  Contains the static React frontend used to register projects, trigger indexing, and submit questions.

### Tech Stack

- Backend: `FastAPI`
- Database: `SQLite`
- Retrieval math: `NumPy`
- Embeddings: `sentence-transformers`
- Text generation: `transformers`
- Frontend: `React`

## Setup Instructions

### Prerequisites

- Python 3.11+ recommended
- `pip`
- Enough disk and memory for model downloads

### 1. Clone the project

```bash
git clone <your-repo-url>
cd "Codebase Aware Developer Assistant"
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Optional for running tests with `pytest`:

```bash
pip install pytest
```

### 4. Start the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- `http://127.0.0.1:8000/`

The frontend will be available at:

- `http://127.0.0.1:8000/app`

### 5. Use the app

1. Open the frontend in your browser.
2. Select or enter a local project path.
3. Register the project.
4. Run indexing.
5. Ask questions about the indexed codebase.

### Environment Variables

These settings can be configured through environment variables:

- `RAG_DB_PATH`: path to the SQLite database file
- `EMBED_MODEL_ID`: embedding model identifier
- `LLM_MODEL_ID`: text-generation model identifier
- `MAX_FILE_BYTES`: max file size to index
- `CHUNK_SIZE`: chunk size for indexed content
- `CHUNK_OVERLAP`: chunk overlap size
- `DEFAULT_TOP_K`: default retrieval count
- `MAX_TOP_K`: max retrieval count
- `DEFAULT_MAX_CONTEXT_CHARS`: default context budget
- `AUTH_ENABLED`: enable or disable API key auth
- `RAG_API_KEYS`: comma-separated valid API keys
- `RATE_LIMIT_ENABLED`: enable or disable rate limiting
- `RATE_LIMIT_PER_MINUTE`: request limit per minute
- `TEST_MODE`: enables deterministic fake models for tests

## API Endpoints

### `GET /`

Returns service health and current configuration details.

Example response:

```json
{
  "status": "running",
  "app": "Codebase Aware Developer Assistant",
  "embed_model": "sentence-transformers/all-MiniLM-L6-v2",
  "llm_model": "distilgpt2",
  "db_path": "./rag_index.db"
}
```

### `GET /filesystem/dirs`

Lists directories for folder selection.

Query params:

- `path` optional directory path to inspect

### `POST /projects/register`

Registers a project path.

Request body:

```json
{
  "project_path": "D:\\Projects\\my-repo",
  "name": "My Project"
}
```

Response body:

```json
{
  "project_id": "uuid-value",
  "name": "My Project",
  "path": "D:\\Projects\\my-repo"
}
```

### `POST /projects/{project_id}/index`

Indexes the selected project by scanning files, chunking text, and storing embeddings.

Response body:

```json
{
  "project_id": "uuid-value",
  "scanned_files": 12,
  "changed_files": 0,
  "deleted_files": 0,
  "chunks_indexed": 84,
  "last_indexed_at": "2026-03-01T00:00:00+00:00"
}
```

### `POST /projects/{project_id}/ask`

Asks a grounded question against the indexed project.

Request body:

```json
{
  "question": "What is the architecture of this code?",
  "top_k": 5,
  "max_context_chars": 2000
}
```

Response body:

```json
{
  "answer": "Architecture summary...",
  "citations": [
    {
      "file": "D:\\Projects\\my-repo\\app\\main.py",
      "start_line": 1,
      "end_line": 36,
      "score": 0.91
    }
  ]
}
```

## Running Tests

Standard library test runner:

```bash
python -m unittest discover -s tests -v
```

If `pytest` is installed:

```bash
pytest -q
```

## Screenshots

Add screenshots here to make the repository easier to evaluate.

Suggested screenshots:

- Main dashboard
- Project registration flow
- Indexing status/result
- Question and answer view
- Citation list/output

Example markdown:

```md
![Dashboard](docs/screenshots/dashboard.png)
![Indexed Project](docs/screenshots/indexed-project.png)
![Answer With Citations](docs/screenshots/answer.png)
```

## Notes

- This project uses a custom RAG pipeline rather than LangChain.
- Embeddings are stored locally in SQLite as blobs.
- The answer-generation path mixes retrieval with heuristic answer construction and optional Hugging Face text generation.

## Future Improvements

- Add a production-ready frontend build pipeline
- Add a proper README demo section with screenshots or GIFs
- Improve authentication and route protection
- Replace local similarity search with a dedicated vector index
- Add more robust evaluation and test coverage
- Support incremental indexing and change detection
=======
# Codebase-Aware-Developer-Assistant
Custom RAG-based codebase assistant built with FastAPI, SQLite, sentence-transformers, and Hugging Face transformers.
>>>>>>> b5734fa2c9faac74cf2fb3b904fe0e77d5f50aa1
