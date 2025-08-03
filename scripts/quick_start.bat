@echo off
REM Legal AI Case Management System - Quick Start Script (Windows)
REM This script automates the setup and startup of the backend application

echo 🚀 Legal AI Case Management System - Backend Quick Start
echo ========================================================

setlocal enabledelayedexpansion

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found

REM Check if Docker is installed
echo [INFO] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [SUCCESS] Docker and Docker Compose found
        set DOCKER_AVAILABLE=true
    ) else (
        echo [WARNING] Docker Compose not found
        set DOCKER_AVAILABLE=false
    )
) else (
    echo [WARNING] Docker not found. Will use manual setup for database.
    set DOCKER_AVAILABLE=false
)

REM Create virtual environment
echo [INFO] Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated

REM Install dependencies
echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo [SUCCESS] Dependencies installed

REM Create .env file if it doesn't exist
echo [INFO] Setting up environment configuration...
if not exist ".env" (
    (
        echo # LLM Configuration
        echo LLM_PROVIDER=ollama
        echo LLM_MODEL=mistral
        echo LLM_TEMPERATURE=0.0
        echo.
        echo # Ollama Configuration
        echo OLLAMA_BASE_URL=http://localhost:11434
        echo.
        echo # OpenAI Configuration (uncomment and set if using OpenAI)
        echo # OPENAI_API_KEY=your_openai_api_key_here
        echo.
        echo # Database Configuration
        echo DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legal_ai
        echo.
        echo # ChromaDB Configuration
        echo CHROMA_DIR=rag_store
        echo.
        echo # Document Storage
        echo PDF_DIR=sample_docs
        echo.
        echo # Embeddings Model
        echo EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
    ) > .env
    echo [SUCCESS] .env file created with default configuration
) else (
    echo [INFO] .env file already exists
)

REM Start database services
if "%DOCKER_AVAILABLE%"=="true" (
    echo [INFO] Starting database services with Docker Compose...
    docker-compose up -d
    echo [SUCCESS] Database services started
    
    REM Wait for services to be ready
    echo [INFO] Waiting for services to be ready...
    timeout /t 10 /nobreak >nul
) else (
    echo [WARNING] Docker not available. Please ensure PostgreSQL is running manually.
    echo [INFO] You can install PostgreSQL and start it manually, or install Docker.
)

REM Check if Ollama is running
echo [INFO] Checking Ollama installation and status...
ollama --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Ollama found
    
    REM Check if Ollama is running
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% equ 0 (
        echo [SUCCESS] Ollama is running
    ) else (
        echo [WARNING] Ollama is not running. Starting Ollama...
        start /b ollama serve
        timeout /t 5 /nobreak >nul
    )
    
    REM Check if mistral model is available
    ollama list | findstr mistral >nul 2>&1
    if %errorlevel% equ 0 (
        echo [SUCCESS] Mistral model is available
    ) else (
        echo [INFO] Downloading Mistral model (this may take a while)...
        ollama pull mistral
        echo [SUCCESS] Mistral model downloaded
    )
) else (
    echo [WARNING] Ollama not found. Please install Ollama manually:
    echo   Download from https://ollama.ai/download
    echo   ollama serve
    echo   ollama pull mistral
)

REM Initialize database
echo [INFO] Initializing database...
if exist "scripts\setup_database.py" (
    python scripts\setup_database.py
    echo [SUCCESS] Database initialized
) else (
    echo [WARNING] Database setup script not found. Skipping database initialization.
)

REM Process sample documents
echo [INFO] Processing sample documents...
if exist "scripts\process_docs_with_env.py" (
    python scripts\process_docs_with_env.py
    echo [SUCCESS] Sample documents processed
) else (
    echo [WARNING] Document processing script not found. Skipping document processing.
)

REM Test the setup
echo [INFO] Testing the setup...
python -c "import sys; sys.path.append('.'); from app.main import app; print('✅ Application imports successfully')" 2>nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Setup test passed
) else (
    echo [ERROR] Application test failed
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Backend setup completed successfully!
echo.
echo [INFO] Starting the application...
echo.

REM Start the application
echo 🌐 The application will be available at:
echo    - API Documentation: http://localhost:8000/docs
echo    - ReDoc Documentation: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the application
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause 