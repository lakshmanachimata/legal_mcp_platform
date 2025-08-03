#!/bin/bash

# Legal AI Case Management System - Quick Start Script
# This script automates the setup and startup of the backend application

set -e  # Exit on any error

echo "🚀 Legal AI Case Management System - Backend Quick Start"
echo "========================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        print_success "Docker and Docker Compose found"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found. Will use manual setup for database."
        DOCKER_AVAILABLE=false
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Create .env file if it doesn't exist
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=mistral
LLM_TEMPERATURE=0.0

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI Configuration (uncomment and set if using OpenAI)
# OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legal_ai

# ChromaDB Configuration
CHROMA_DIR=rag_store

# Document Storage
PDF_DIR=sample_docs

# Embeddings Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EOF
        print_success ".env file created with default configuration"
    else
        print_status ".env file already exists"
    fi
}

# Start database services
start_database() {
    if [ "$DOCKER_AVAILABLE" = true ]; then
        print_status "Starting database services with Docker Compose..."
        docker-compose up -d
        print_success "Database services started"
        
        # Wait for services to be ready
        print_status "Waiting for services to be ready..."
        sleep 10
    else
        print_warning "Docker not available. Please ensure PostgreSQL is running manually."
        print_status "You can install PostgreSQL and start it manually, or install Docker."
    fi
}

# Check if Ollama is running
check_ollama() {
    print_status "Checking Ollama installation and status..."
    
    if command -v ollama &> /dev/null; then
        print_success "Ollama found"
        
        # Check if Ollama is running
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            print_success "Ollama is running"
        else
            print_warning "Ollama is not running. Starting Ollama..."
            ollama serve &
            sleep 5
        fi
        
        # Check if mistral model is available
        if ollama list | grep -q mistral; then
            print_success "Mistral model is available"
        else
            print_status "Downloading Mistral model (this may take a while)..."
            ollama pull mistral
            print_success "Mistral model downloaded"
        fi
    else
        print_warning "Ollama not found. Please install Ollama manually:"
        echo "  curl -fsSL https://ollama.ai/install.sh | sh"
        echo "  ollama serve"
        echo "  ollama pull mistral"
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    if [ -f "scripts/setup_database.py" ]; then
        $PYTHON_CMD scripts/setup_database.py
        print_success "Database initialized"
    else
        print_warning "Database setup script not found. Skipping database initialization."
    fi
}

# Process sample documents
process_documents() {
    print_status "Processing sample documents..."
    
    if [ -f "scripts/process_docs_with_env.py" ]; then
        $PYTHON_CMD scripts/process_docs_with_env.py
        print_success "Sample documents processed"
    else
        print_warning "Document processing script not found. Skipping document processing."
    fi
}

# Test the setup
test_setup() {
    print_status "Testing the setup..."
    
    # Test if the application can start
    timeout 10s $PYTHON_CMD -c "
import sys
sys.path.append('.')
try:
    from app.main import app
    print('✅ Application imports successfully')
except Exception as e:
    print(f'❌ Application import failed: {e}')
    sys.exit(1)
" || {
        print_error "Application test failed"
        exit 1
    }
    
    print_success "Setup test passed"
}

# Start the application
start_application() {
    print_status "Starting the FastAPI application..."
    echo ""
    echo "🌐 The application will be available at:"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - ReDoc Documentation: http://localhost:8000/redoc"
    echo ""
    echo "Press Ctrl+C to stop the application"
    echo ""
    
    $PYTHON_CMD -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Main execution
main() {
    echo ""
    print_status "Starting backend setup..."
    echo ""
    
    # Run setup steps
    check_python
    check_docker
    setup_venv
    install_dependencies
    setup_env
    start_database
    check_ollama
    init_database
    process_documents
    test_setup
    
    echo ""
    print_success "Backend setup completed successfully!"
    echo ""
    print_status "Starting the application..."
    echo ""
    
    # Start the application
    start_application
}

# Handle script interruption
trap 'echo ""; print_warning "Setup interrupted. You can restart with: ./scripts/quick_start.sh"; exit 1' INT

# Run main function
main "$@" 