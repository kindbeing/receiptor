#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Log function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Success function
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Warning function
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Error function
error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if brew is installed
check_brew() {
    if ! command_exists brew; then
        error "Homebrew is not installed. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    success "Homebrew is installed"
}

# Install Python 3.12 if not present
setup_python() {
    if command_exists python3.12; then
        success "Python 3.12 is already installed"
        return
    fi

    log "Installing Python 3.12..."
    brew install python@3.12

    # Add to PATH if not already there
    if ! grep -q "python@3.12" ~/.zshrc 2>/dev/null; then
        echo 'export PATH="/usr/local/opt/python@3.12/bin:$PATH"' >> ~/.zshrc
        warning "Added Python 3.12 to PATH in ~/.zshrc. Please restart your terminal or run: source ~/.zshrc"
    fi

    success "Python 3.12 installed"
}

# Setup PostgreSQL
setup_postgresql() {
    if command_exists pg_isready && pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        success "PostgreSQL is running on port 5432"
        return
    fi

    log "Setting up PostgreSQL..."
    brew install postgresql@16

    # Start PostgreSQL service
    brew services start postgresql@16

    # Wait for PostgreSQL to start
    local retries=30
    while [ $retries -gt 0 ]; do
        if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            success "PostgreSQL is now running on port 5432"
            return
        fi
        sleep 1
        retries=$((retries - 1))
    done

    error "PostgreSQL failed to start"
    exit 1
}

# Setup database and user
setup_database() {
    log "Setting up receiptor_db database..."

    # Check if database already exists
    if psql -h localhost -p 5432 -U postgres -lqt | cut -d \| -f 1 | grep -qw receiptor_db; then
        success "Database receiptor_db already exists"
        return
    fi

    # Create database and user
    psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE receiptor_db;" 2>/dev/null || true
    psql -h localhost -p 5432 -U postgres -c "CREATE USER root WITH PASSWORD 'password';" 2>/dev/null || true
    psql -h localhost -p 5432 -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE receiptor_db TO root;" 2>/dev/null || true

    success "Database receiptor_db created with user root"
}

# Setup Ollama
setup_ollama() {
    if command_exists ollama; then
        success "Ollama is already installed"
    else
        log "Installing Ollama..."
        brew install ollama
        success "Ollama installed"
    fi

    # Check if Ollama service is running
    if pgrep -f "ollama serve" >/dev/null; then
        success "Ollama service is running"
    else
        log "Starting Ollama service..."
        brew services start ollama

        # Wait for Ollama to start
        local retries=30
        while [ $retries -gt 0 ]; do
            if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
                success "Ollama service is now running on port 11434"
                break
            fi
            sleep 1
            retries=$((retries - 1))
        done

        if [ $retries -eq 0 ]; then
            error "Ollama service failed to start"
            exit 1
        fi
    fi

    # Check if Qwen2.5vl:7b model is available
    if ollama list | grep -q "qwen2.5vl:7b"; then
        success "Qwen2.5vl:7b model is available"
    else
        log "Pulling Qwen2.5vl:7b model (this may take a while)..."
        ollama pull qwen2.5vl:7b
        success "Qwen2.5vl:7b model downloaded"
    fi
}

# Setup OCR dependencies
setup_ocr_deps() {
    if command_exists tesseract; then
        success "Tesseract OCR is already installed"
    else
        log "Installing Tesseract OCR..."
        brew install tesseract
        success "Tesseract OCR installed"
    fi

    # Check for poppler (required by pdf2image)
    if brew list poppler >/dev/null 2>&1; then
        success "Poppler (for PDF processing) is already installed"
    else
        log "Installing Poppler for PDF processing..."
        brew install poppler
        success "Poppler installed"
    fi
}

# Setup backend dependencies
setup_backend_deps() {
    cd "$PROJECT_ROOT/backend"

    if [ -d ".venv" ]; then
        success "Backend virtual environment already exists"
    else
        log "Creating backend virtual environment..."
        python3.12 -m venv .venv
        success "Backend virtual environment created"
    fi

    log "Installing backend dependencies..."
    source .venv/bin/activate
    pip install -e .
    success "Backend dependencies installed"

    # Run database migrations
    log "Running database migrations..."
    alembic upgrade head
    success "Database migrations completed"
}

# Setup frontend dependencies
setup_frontend_deps() {
    if ! command_exists bun; then
        error "Bun is not installed. Please install Bun first:"
        echo "  curl -fsSL https://bun.sh/install | bash"
        exit 1
    fi

    cd "$PROJECT_ROOT/frontend"

    if [ -d "node_modules" ]; then
        success "Frontend dependencies already installed"
    else
        log "Installing frontend dependencies..."
        bun install
        success "Frontend dependencies installed"
    fi
}

# Main setup function
main() {
    log "🚀 Starting Receiptor application bootstrap..."

    check_brew
    setup_python
    setup_postgresql
    setup_database
    setup_ollama
    setup_ocr_deps
    setup_backend_deps
    setup_frontend_deps

    success "🎉 Bootstrap completed successfully!"
    echo ""
    echo "To start the application:"
    echo "  Backend: cd backend && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    echo "  Frontend: cd frontend && bun run dev"
    echo ""
    echo "Database: PostgreSQL running on localhost:5432"
    echo "Ollama: Running on localhost:11434 with Qwen2.5vl:7b model"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
