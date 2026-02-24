#!/bin/bash
# Script to pull the default local LLM model
MODEL=${1:-gemma:2b}

echo "⬇️ Pulling model $MODEL in Ollama container..."
if docker exec -it tutorlti-ollama-1 ollama pull "$MODEL"; then
    echo "✅ Model $MODEL ready!"
    echo "To use it, ensure your .env has LLM_PROVIDER=ollama"
else
    echo "❌ Failed to pull model. key sure the stack is running:"
    echo "   docker compose up -d"
fi
