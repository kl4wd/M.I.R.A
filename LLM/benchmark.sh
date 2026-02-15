#!/bin/bash

MODEL_NAME="ministral-turbo"
PROMPT="Explique la thermodynamique en 20 mots."

echo "=== Benchmark Rapide : $MODEL_NAME ==="
echo "Prompt: $PROMPT"

# Timeout 60s
RESPONSE=$(curl -s --max-time 60 -X POST http://localhost:11434/api/generate -d "{
  \"model\": \"$MODEL_NAME\",
  \"prompt\": \"$PROMPT\",
  \"stream\": false
}")

if [ -z "$RESPONSE" ]; then
    echo "[ERREUR] Pas de réponse du serveur."
    exit 1
fi

EVAL_COUNT=$(echo "$RESPONSE" | jq -r '.eval_count // 0')
EVAL_DURATION=$(echo "$RESPONSE" | jq -r '.eval_duration // 0')

if [ "$EVAL_DURATION" -gt 0 ]; then
    # Calcul T/s : (eval_count / eval_duration) * 10^9
    TS=$(awk -v count="$EVAL_COUNT" -v dur="$EVAL_DURATION" 'BEGIN {Kv = 1000000000; printf "%.2f", (count * Kv / dur)}')
    echo "-----------------------------------"
    echo "Tokens: $EVAL_COUNT"
    echo "Durée : $EVAL_DURATION ns"
    echo "Vitesse: $TS Tokens/sec"
    echo "-----------------------------------"
else
    echo "[ERREUR] Métriques manquantes."
    echo "$RESPONSE" | jq .
fi
