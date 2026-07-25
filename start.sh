#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Thinkora — One-Command Development Setup
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${BLUE}[thinkora]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }

# ─── Track background PIDs for cleanup ──────────────────────
WORKER_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    log "Shutting down all services..."
    [ -n "$WORKER_PID" ]   && kill "$WORKER_PID"   2>/dev/null && ok "Celery worker stopped"
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID"  2>/dev/null && ok "Frontend dev server stopped"
    wait 2>/dev/null
    ok "All services stopped. Goodbye!"
}
trap cleanup EXIT INT TERM

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🧠 Thinkora — Development Environment Setup${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ─── 1. Check Docker ────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    err "Docker is not installed."
    echo "   Install: https://docs.docker.com/get-docker/"
    exit 1
fi
ok "Docker installed"

if ! docker info &>/dev/null 2>&1; then
    err "Docker daemon is not running."
    echo "   Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
fi
ok "Docker daemon running"

# ─── 2. Check Docker Compose ────────────────────────────────
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    err "Docker Compose not found."
    echo "   Install: https://docs.docker.com/compose/install/"
    exit 1
fi
ok "Docker Compose available ($COMPOSE_CMD)"

# ─── 3. Check backend/.env ──────────────────────────────────
if [ ! -f "backend/.env" ]; then
    warn "backend/.env not found — copying from .env.example"
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        ok "Created backend/.env from .env.example"
    else
        err "backend/.env.example not found"
        exit 1
    fi
fi
ok "backend/.env exists"

# ─── 3.1 Check frontend/.env ──────────────────────────────────
if [ ! -f "frontend/.env" ]; then
    warn "frontend/.env not found — copying from .env.example"
    if [ -f "frontend/.env.example" ]; then
        cp frontend/.env.example frontend/.env
        ok "Created frontend/.env from .env.example"
    else
        err "frontend/.env.example not found"
        exit 1
    fi
fi
ok "frontend/.env exists"

# ─── 4. Check Python venv ───────────────────────────────────
if [ ! -d "backend/.venv" ] || ! backend/.venv/bin/python -c "import sys, os; assert os.path.realpath(sys.prefix) == os.path.realpath('$SCRIPT_DIR/backend/.venv')" 2>/dev/null; then
    warn "Python venv not found or invalid (e.g. moved) — recreating..."
    rm -rf backend/.venv
    python3 -m venv backend/.venv
    ok "Created Python virtual environment"
fi

# Activate venv
source backend/.venv/bin/activate
ok "Python venv activated"

# ─── 5. Install Python dependencies ─────────────────────────
log "Checking Python dependencies..."
python -m pip install -q -r backend/requirements.txt 2>/dev/null || {
    warn "Installing Python dependencies..."
    python -m pip install -r backend/requirements.txt
}
ok "Python dependencies installed"

# ─── 6. Check Node.js & frontend deps ───────────────────────
if [ -d "frontend" ]; then
    if ! command -v node &>/dev/null; then
        warn "Node.js not found — frontend dev server will not start"
    else
        ok "Node.js available ($(node --version))"
        if [ ! -d "frontend/node_modules" ]; then
            log "Installing frontend dependencies..."
            (cd frontend && npm install)
        fi
        ok "Frontend dependencies ready"
    fi
fi

# ─── 7. Start infrastructure (Docker Compose) ───────────────
log "Starting infrastructure services..."
$COMPOSE_CMD -f docker-compose.dev.yml up -d
ok "Infrastructure services started (Postgres, Redis, Qdrant)"

# ─── 8. Wait for Redis to be ready (worker needs it) ────────
log "Waiting for Redis to accept connections..."
for i in $(seq 1 30); do
    if docker exec thinkora-redis redis-cli ping 2>/dev/null | grep -q PONG; then
        ok "Redis is ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        err "Redis did not become ready in time"
        exit 1
    fi
    sleep 1
done

# ─── 9. Start Celery worker (background) ────────────────────
log "Starting Celery worker..."
mkdir -p backend/logs
cd backend
python -m celery -A app.workers.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    >> logs/worker.log 2>&1 &
WORKER_PID=$!
cd "$SCRIPT_DIR"

# Brief pause to catch immediate crashes
sleep 2
if kill -0 "$WORKER_PID" 2>/dev/null; then
    ok "Celery worker started (PID: $WORKER_PID, log: backend/logs/worker.log)"
else
    err "Celery worker failed to start — check backend/logs/worker.log"
    WORKER_PID=""
fi

# ─── 10. Start Frontend dev server (background) ─────────────
if [ -d "frontend" ] && command -v node &>/dev/null; then
    log "Starting frontend dev server..."
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!
    ok "Frontend dev server starting on http://localhost:5173"
fi

# ─── 11. Start Backend (foreground) ─────────────────────────
# THINKORA_WORKER_EXTERNAL=true tells the bootstrap orchestrator
# that the worker is already managed by this script — don't spawn a duplicate.
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 All services running! Press Ctrl+C to stop.${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "  API:      http://localhost:8000"
echo -e "  Frontend: http://localhost:5173"
echo -e "  Worker:   PID ${WORKER_PID:-N/A} → backend/logs/worker.log"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

log "Starting backend server..."
cd backend
THINKORA_WORKER_EXTERNAL=true exec python -m uvicorn app.main:app --reload --port 8000
