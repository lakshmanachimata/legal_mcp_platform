# Legal AI Case Management System

A comprehensive legal case management system with AI-powered document processing, RAG (Retrieval-Augmented Generation), and demand letter generation capabilities.

## Quick Start

### Backend Setup

The fastest way to get the backend running:

**Linux/macOS:**
```bash
./scripts/quick_start.sh
```

**Windows:**
```cmd
scripts\quick_start.bat
```

### Manual Setup

For detailed setup instructions, see [BACKEND_SETUP.md](BACKEND_SETUP.md).

## Features

- **Document Processing**: Upload and analyze legal documents with AI
- **RAG Queries**: Intelligent document retrieval and question answering
- **Demand Letter Generation**: AI-powered legal document creation
- **Case Management**: Complete case tracking and management
- **PDF Generation**: Professional document output
- **Multiple LLM Support**: OpenAI and Ollama integration

## Architecture

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## LLM Provider Support

For information about supported LLM providers, see [LLM_PROVIDER_SUPPORT.md](LLM_PROVIDER_SUPPORT.md).

## Sample Output

For examples of generated demand letters, see [SAMPLE_OUTPUT.md](SAMPLE_OUTPUT.md).

## API Documentation

Once the backend is running, access the interactive API documentation at:
- http://localhost:8000/docs
- http://localhost:8000/redoc

## Development

### Prerequisites

- Python 3.8+
- PostgreSQL 15+
- Docker (optional, for containerized database)
- Ollama or OpenAI API key

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see BACKEND_SETUP.md)
4. Initialize database and process documents
5. Start the application: `uvicorn app.main:app --reload`
