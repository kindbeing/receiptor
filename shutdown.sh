#!/bin/bash

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

# Info function
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Kill process on specific port
kill_port() {
    local port=$1
    local name=$2

    # Find process using the port
    local pid=$(lsof -ti :$port 2>/dev/null)

    if [ -n "$pid" ]; then
        log "Killing $name process on port $port (PID: $pid)..."
        kill -TERM $pid 2>/dev/null || kill -KILL $pid 2>/dev/null || true

        # Wait a bit for graceful shutdown
        sleep 2

        # Check if still running
        if lsof -ti :$port >/dev/null 2>&1; then
            warning "$name process still running on port $port"
        else
            success "$name process stopped on port $port"
        fi
    else
        info "No $name process found on port $port"
    fi
}

# Check PostgreSQL status
check_postgresql() {
    log "Checking PostgreSQL status..."

    if command -v pg_isready >/dev/null 2>&1; then
        if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            success "PostgreSQL is running on port 5432"

            # Try to connect to the database
            if psql -h localhost -p 5432 -U root -d receiptor_db -c "SELECT 1;" >/dev/null 2>&1; then
                success "Database 'receiptor_db' is accessible"
            else
                warning "Cannot connect to database 'receiptor_db' (may need authentication)"
            fi
        else
            error "PostgreSQL is not responding on port 5432"
        fi
    else
        warning "pg_isready command not found - cannot check PostgreSQL status"
    fi
}

# Check Ollama status
check_ollama() {
    log "Checking Ollama status..."

    # Check if Ollama service is running
    if pgrep -f "ollama serve" >/dev/null; then
        success "Ollama service is running"

        # Check API connectivity
        if curl -s --max-time 5 http://localhost:11434/api/tags >/dev/null 2>&1; then
            success "Ollama API is accessible on port 11434"

            # Check available models
            local models=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")
            if echo "$models" | grep -q "qwen2.5"; then
                success "Qwen2.5vl:7b model is available"
            else
                warning "Qwen2.5vl:7b model not found in available models: $models"
            fi
        else
            warning "Ollama API is not accessible on port 11434"
        fi
    else
        warning "Ollama service is not running"
        info "Ollama will remain available for future sessions"
    fi
}

# Kill FastAPI backend (typically port 8000)
kill_backend() {
    kill_port 8000 "FastAPI Backend"
}

# Kill Vite frontend (typically port 5173)
kill_frontend() {
    kill_port 5173 "Vite Frontend"
}

# Kill any other common development ports
kill_dev_ports() {
    # Common development ports that might be used
    local ports=(3000 3001 8080 4000 5000)

    for port in "${ports[@]}"; do
        if lsof -ti :$port >/dev/null 2>&1; then
            kill_port $port "Development server"
        fi
    done
}

# Main shutdown function
main() {
    log "🛑 Starting Receiptor application shutdown..."

    # Kill application processes
    kill_backend
    kill_frontend
    kill_dev_ports

    echo ""

    # Report on persistent services
    check_postgresql
    check_ollama

    echo ""
    success "🧹 Application shutdown completed!"
    echo ""
    info "Database and Ollama services remain active for data persistence."
    echo "To stop these services completely, run:"
    echo "  PostgreSQL: brew services stop postgresql@16"
    echo "  Ollama: brew services stop ollama"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
