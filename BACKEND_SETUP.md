# Backend Setup Guide

## Legal AI Case Management System - Backend

This document provides comprehensive instructions for setting up and running the backend of the Legal AI Case Management System.

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [LLM Provider Setup](#llm-provider-setup)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Running the Application](#running-the-application)
9. [API Documentation](#api-documentation)
10. [Troubleshooting](#troubleshooting)

## System Overview

The backend is a FastAPI-based application that provides:

- **Legal Document Processing**: AI-powered document analysis and processing
- **RAG (Retrieval-Augmented Generation)**: Intelligent document querying and question answering
- **Case Management**: Complete case tracking with parties, events, and financials
- **Demand Letter Generation**: AI-powered legal document creation
- **PDF Generation**: Professional document output
- **Multiple LLM Support**: OpenAI and Ollama integration

### Key Components

- **FastAPI**: Web framework for API endpoints
- **SQLAlchemy**: Database ORM
- **ChromaDB**: Vector database for RAG
- **LangChain**: LLM integration framework
- **PostgreSQL**: Primary database
- **Ollama/OpenAI**: LLM providers

## Prerequisites

### System Requirements

- Python 3.8 or higher
- PostgreSQL 15 or higher
- Docker and Docker Compose (optional, for containerized setup)
- Git

### Software Dependencies

- Python packages (see `requirements.txt`)
- PostgreSQL database
- ChromaDB (vector database)
- LLM provider (Ollama or OpenAI)

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd legal_mcp_platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Database Setup

### Option 1: Using Docker Compose (Recommended)

```bash
# Start PostgreSQL and ChromaDB
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Option 2: Manual PostgreSQL Setup

1. Install PostgreSQL on your system
2. Create a database:
```sql
CREATE DATABASE legal_ai;
CREATE USER legal_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE legal_ai TO legal_user;
```

### Option 3: Using SQLite (Development Only)

Modify `app/config.py` to use SQLite:
```python
self.database_url = "sqlite:///./legal_ai.db"
```

## LLM Provider Setup

### Option 1: Ollama (Local LLM)

1. Install Ollama:
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

2. Start Ollama and pull a model:
```bash
ollama serve
ollama pull mistral
```

3. Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### Option 2: OpenAI (Cloud LLM)

1. Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Set the API key in your environment (see Configuration section)

## Installation

### 1. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# LLM Configuration
LLM_PROVIDER=ollama  # or openai
LLM_MODEL=mistral    # or gpt-4, gpt-3.5-turbo, etc.
LLM_TEMPERATURE=0.0

# Ollama Configuration (if using Ollama)
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legal_ai

# ChromaDB Configuration
CHROMA_DIR=rag_store

# Document Storage
PDF_DIR=sample_docs

# Embeddings Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 2. Initialize Database

```bash
# Run database setup script
python scripts/setup_database.py
```

### 3. Process Sample Documents

```bash
# Process sample documents for RAG
python scripts/process_docs_with_env.py
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | LLM provider (ollama/openai) | ollama | Yes |
| `LLM_MODEL` | Model name | mistral | Yes |
| `LLM_TEMPERATURE` | Generation temperature | 0.0 | No |
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 | If using Ollama |
| `OPENAI_API_KEY` | OpenAI API key | None | If using OpenAI |
| `DATABASE_URL` | Database connection string | postgresql://... | Yes |
| `CHROMA_DIR` | ChromaDB storage directory | rag_store | Yes |
| `PDF_DIR` | Document storage directory | sample_docs | Yes |
| `EMBEDDING_MODEL` | Embeddings model name | sentence-transformers/all-MiniLM-L6-v2 | Yes |

### Configuration File

The main configuration is in `app/config.py`. Key settings:

- **LLM Configuration**: Provider, model, API keys
- **Database Settings**: Connection strings and ORM setup
- **RAG Settings**: Vector database and embeddings configuration
- **Document Processing**: File storage and processing settings

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run the FastAPI application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn (recommended for production)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

```bash
# Build and run with Docker
docker build -t legal-ai-backend .
docker run -p 8000:8000 legal-ai-backend
```

## API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints

#### System Endpoints
- `GET /system/overview` - Get comprehensive system overview
- `GET /system/statistics` - Get system statistics
- `GET /system/timeline` - Get system timeline
- `GET /system/all` - Get all system information

#### RAG Endpoints
- `POST /rag/query` - Query RAG system with natural language
- `POST /rag/query-with-provider` - Query with custom LLM provider
- `POST /rag/process_document` - Process and analyze documents
- `POST /rag/process_document-with-provider` - Process with custom LLM

#### Case Management
- `GET /cases` - Get all cases
- `GET /parties` - Get all parties
- `GET /events` - Get all timeline events
- `GET /financials` - Get all financial records
- `GET /cases/{case_id}/comprehensive` - Get comprehensive case info

#### Document Generation
- `POST /mcp/generate_demand_letter` - Generate demand letter
- `POST /generate-pdf` - Generate PDF from letter content
- `POST /generate-pdf-json` - Generate PDF from JSON

#### LLM Management
- `GET /llm/providers` - Get available LLM providers
- `GET /mcp/tools` - Get available MCP tools

## Testing the Setup

### 1. Health Check

```bash
curl http://localhost:8000/docs
```

### 2. Test RAG Query

```bash
curl -X POST "http://localhost:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the total number of cases?",
    "case_id": "system"
  }'
```

### 3. Test Document Processing

```bash
curl -X POST "http://localhost:8000/rag/process_document" \
  -F "file=@sample_docs/2024-PI-001/medical_records_dr_jones.pdf" \
  -F "case_id=2024-PI-001"
```

### 4. Test Demand Letter Generation

```bash
curl -X POST "http://localhost:8000/mcp/generate_demand_letter?case_id=2024-PI-001"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

**Error**: `psycopg2.OperationalError: connection to server failed`

**Solution**:
- Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Check database URL in `.env` file
- Ensure database exists and user has permissions

#### 2. Ollama Connection Issues

**Error**: `Connection refused to Ollama server`

**Solution**:
- Verify Ollama is running: `ollama serve`
- Check Ollama URL: `curl http://localhost:11434/api/tags`
- Ensure model is downloaded: `ollama pull mistral`

#### 3. ChromaDB Issues

**Error**: `ChromaDB connection failed`

**Solution**:
- Verify ChromaDB is running: `docker-compose ps`
- Check ChromaDB logs: `docker-compose logs chromadb`
- Ensure `CHROMA_DIR` is writable

#### 4. Import Errors

**Error**: `ModuleNotFoundError`

**Solution**:
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path: `python -c "import sys; print(sys.path)"`

#### 5. LLM Provider Issues

**Error**: `OpenAI API key not found`

**Solution**:
- Set `OPENAI_API_KEY` in `.env` file
- Verify API key is valid
- Check provider configuration in `.env`

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
```

### Logs

Check application logs for detailed error information:

```bash
# If running with uvicorn
uvicorn app.main:app --reload --log-level debug

# If running with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --log-level debug
```

## Performance Optimization

### 1. Database Optimization

- Use connection pooling
- Add database indexes
- Optimize queries

### 2. RAG Optimization

- Use appropriate chunk sizes
- Optimize embedding model selection
- Implement caching

### 3. LLM Optimization

- Use appropriate model sizes
- Implement request batching
- Add response caching

## Security Considerations

### 1. Environment Variables

- Never commit `.env` files to version control
- Use strong, unique passwords
- Rotate API keys regularly

### 2. API Security

- Implement authentication and authorization
- Use HTTPS in production
- Add rate limiting

### 3. Database Security

- Use strong database passwords
- Limit database access
- Regular backups

## Deployment

### Production Checklist

- [ ] Set up production database
- [ ] Configure environment variables
- [ ] Set up reverse proxy (nginx)
- [ ] Configure SSL certificates
- [ ] Set up monitoring and logging
- [ ] Implement backup strategy
- [ ] Configure firewall rules
- [ ] Set up CI/CD pipeline

### Docker Production

```bash
# Build production image
docker build -t legal-ai-backend:latest .

# Run with production settings
docker run -d \
  --name legal-ai-backend \
  -p 8000:8000 \
  --env-file .env \
  legal-ai-backend:latest
```

## Support

For additional support:

1. Check the API documentation at `/docs`
2. Review the application logs
3. Check the project README.md
4. Review the architecture documentation in ARCHITECTURE.md

## Version Information

- **FastAPI Version**: Latest
- **Python Version**: 3.8+
- **Database**: PostgreSQL 15+
- **Vector Database**: ChromaDB
- **LLM Providers**: Ollama, OpenAI

---

*Last updated: January 2024* 