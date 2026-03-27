#!/usr/bin/env bash
# ============================================================
# start_server.sh — запуск всей инфраструктуры на Ubuntu
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/infra"

echo "=== LLM Security Server ==="
echo ""

# Load .env for display
source .env 2>/dev/null || true
TARGET_IP="${TARGET_IP:-$(hostname -I | awk '{print $1}')}"

echo "[1/4] Pulling Docker images..."
docker compose pull

echo ""
echo "[2/4] Building API and UI containers..."
docker compose build

echo ""
echo "[3/4] Starting all services..."
docker compose up -d

echo ""
echo "[4/4] Waiting for services..."

# Wait for API
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${API_PORT:-8000}/health" > /dev/null 2>&1; then
        echo "  API:      http://${TARGET_IP}:${API_PORT:-8000}/docs"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  API:      TIMEOUT (check: docker compose logs api)"
    fi
    sleep 2
done

# Wait for Langfuse
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${LANGFUSE_PORT:-3000}" > /dev/null 2>&1; then
        echo "  Langfuse: http://${TARGET_IP}:${LANGFUSE_PORT:-3000}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  Langfuse: TIMEOUT (check: docker compose logs langfuse)"
    fi
    sleep 2
done

echo "  UI:       http://${TARGET_IP}:${UI_PORT:-8501}"
echo ""
echo "=== Server is ready ==="
echo ""
echo "Red Team (Kali) command:"
echo "  TARGET_IP=${TARGET_IP} npx promptfoo eval --no-cache"
echo ""
echo "View logs:"
echo "  docker compose -f infra/docker-compose.yml logs -f api"
echo ""
echo "Stop:"
echo "  docker compose -f infra/docker-compose.yml down"
