#!/usr/bin/env bash
# ============================================================
# ingest.sh — загрузка документов в RAG (ChromaDB)
# Запускать ПОСЛЕ start_server.sh
# ============================================================
set -euo pipefail

echo "=== RAG Document Ingestion ==="
echo ""

# Check ChromaDB is reachable
echo "[1/3] Checking ChromaDB..."
if ! curl -sf http://127.0.0.1:8200/api/v2/heartbeat > /dev/null 2>&1; then
    echo "ERROR: ChromaDB is not running. Run ./start_server.sh first."
    exit 1
fi
echo "  ChromaDB is UP"

# Check Ollama has models
echo ""
echo "[2/3] Checking Ollama models..."
if ! docker exec llm-ollama ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    echo "  Downloading embedding model (nomic-embed-text)..."
    docker exec llm-ollama ollama pull nomic-embed-text
fi
echo "  Embedding model: OK"

if ! docker exec llm-ollama ollama list 2>/dev/null | grep -q "llama3"; then
    echo "  Downloading chat model (llama3)..."
    docker exec llm-ollama ollama pull llama3
fi
echo "  Chat model: OK"

# Ingest documents
echo ""
echo "[3/3] Ingesting documents into ChromaDB..."
docker exec llm-api python -c "from src.ai_core.rag.ingest import ingest_documents; ingest_documents()"

echo ""
echo "=== Done! Documents loaded into RAG ==="
echo "Test: curl -s http://localhost:8000/api/v1/chat -H 'Content-Type: application/json' -d '{\"query\": \"Покажи данные Петрова\"}' | python3 -m json.tool"
