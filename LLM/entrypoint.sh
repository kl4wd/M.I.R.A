#!/bin/bash

# ==================================================================================
# Entrypoint Optimisé pour Ollama (Ministral 3B)
# Supporte : Raspberry Pi 5 (aarch64) & PC/WSL2 (x86_64)
# ==================================================================================

# 1. DÉMARRAGE DU SERVEUR OLLAMA EN ARRIÈRE-PLAN
export OLLAMA_DEBUG=1 # Activation des logs détaillés pour debug
echo "[ENTRYPOINT] Démarrage du serveur Ollama (Debug Mode)..."
ollama serve &
SERVER_PID=$!

# ... (skip wait loop - unchanged)

# ... (skip architecture detection strings)

# 4. GÉNÉRATION DU MODELFILE SIMPLIFIÉ (MODE STABILITÉ)
echo "[OLLAMA] Génération du Modelfile (Mode Safe)..."
cat <<EOF > $MODELFILE
FROM $BASE_MODEL

# On commente les optimisations agressives pour isoler le problème
# PARAMETER num_thread $NUM_THREAD
# PARAMETER num_ctx $NUM_CTX
# PARAMETER num_batch $NUM_BATCH

TEMPLATE """{{ if .System }}<|system|>
{{ .System }}</s>
{{ end }}{{ if .User }}<|user|>
{{ .User }}</s>
{{ end }}{{ if .Assistant }}<|assistant|>
{{ .Assistant }}</s>
{{ end }}"""
EOF

# 5. CRÉATION DU MODÈLE OPTIMISÉ
echo "[OLLAMA] Création du modèle '$MODEL_NAME'..."
ollama create "$MODEL_NAME" -f "$MODELFILE"
echo "[OK] Modèle prêt : $MODEL_NAME"

# 6. MAINTIEN DU CONTENEUR ACTIF
# On attend la fin du processus serveur
wait $SERVER_PID
