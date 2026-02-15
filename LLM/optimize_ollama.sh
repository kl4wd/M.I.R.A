#!/bin/bash

# ==================================================================================
# Script d'Optimisation Ollama pour Raspberry Pi 5 & WSL2
# Modèle cible : Ministral-3b
# Objectif : Performance maximale (Tokens/Sec)
# ==================================================================================

MODEL_NAME="ministral-turbo"
BASE_MODEL="ministral:3b-instruct-v0.1-q4_K_M"
MODELFILE="Modelfile"

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Démarrage de l'optimisation Ollama ===${NC}"

# 1. DÉTECTION DE L'ARCHITECTURE
ARCH=$(uname -m)
IS_WSL=$(grep -qi microsoft /proc/version && echo "true" || echo "false")

echo -e "${YELLOW}[INFO] Architecture détectée : $ARCH${NC}"
if [ "$IS_WSL" == "true" ]; then
    echo -e "${YELLOW}[INFO] Environnement : WSL2${NC}"
else
    echo -e "${YELLOW}[INFO] Environnement : Linux Natif (Probablement Pi 5)${NC}"
fi

# 2. CALCUL DES THREADS ET CONFIGURATION
if [[ "$ARCH" == "aarch64" ]]; then
    # Configuration Raspberry Pi 5
    echo -e "${GREEN}[CONFIG] Application des paramètres pour Raspberry Pi 5${NC}"
    NUM_THREAD=4
    echo -e "${YELLOW}[OPTIM] Force num_thread = $NUM_THREAD (Cœurs physiques Pi 5)${NC}"
    
    # Optimisation OS - Swap
    echo -e "${YELLOW}[OS] Configuration de vm.swappiness à 1 (nécessite sudo)...${NC}"
    if sudo sysctl -w vm.swappiness=1; then
        echo -e "${GREEN}[OK] Swappiness réduit.${NC}"
    else
        echo -e "${RED}[ERREUR] Échec de la modification de vm.swappiness${NC}"
    fi

elif [ "$IS_WSL" == "true" ]; then
    # Configuration WSL2
    echo -e "${GREEN}[CONFIG] Application des paramètres pour WSL2${NC}"
    # Utiliser nproc mais garder une marge si besoin, ou utiliser tout. 
    # Souvent pour les LLM, threads = physical cores est mieux.
    # Dans WSL, nproc donne souvent les threads logiques. On va essayer d'être conservateur ou utiliser nproc.
    # Pour ministral 3b, nproc est généralement ok sur PC.
    NUM_THREAD=$(nproc)
    echo -e "${YELLOW}[OPTIM] Utilisation de num_thread = $NUM_THREAD (détecté via nproc)${NC}"
    
    echo -e "${YELLOW}[NOTE IMPORTANTE WSL2]${NC}"
    echo "Assurez-vous que votre fichier .wslconfig (dans C:\Users\VOTRE_USER\) est optimisé :"
    echo "  [wsl2]"
    echo "  memory=12GB  # (Ajustez selon votre RAM PC)"
    echo "  processors=$(nproc)"
else
    # Fallback x86 Linux natif
    NUM_THREAD=$(nproc)
    echo -e "${YELLOW}[CONFIG] Linux Générique détecté. Threads: $NUM_THREAD${NC}"
fi

# 3. VARIABLES D'ENVIRONNEMENT CRITIQUES
echo -e "${GREEN}[ENV] Configuration des variables d'environnement Ollama${NC}"
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_KEEP_ALIVE=-1

echo "export OLLAMA_NUM_PARALLEL=1"
echo "export OLLAMA_KEEP_ALIVE=-1"
echo -e "${YELLOW}Note : Ces variables sont exportées pour ce script. Pour persister, ajoutez-les à votre systemd service ou .bashrc.${NC}"

# 4. PRÉPARATION DU MODÈLE DE BASE
echo -e "${GREEN}[OLLAMA] Vérification du modèle de base '$BASE_MODEL'...${NC}"
if ! ollama list | grep -q "$BASE_MODEL"; then
    echo -e "${YELLOW}[INFO] Modèle non trouvé localement. Téléchargement en cours...${NC}"
    if ! ollama pull $BASE_MODEL; then
        echo -e "${RED}[ERREUR] Impossible de télécharger '$BASE_MODEL'. Vérifiez le nom du modèle ou votre connexion.${NC}"
        # Tentative de fallback sur un nom plus court si l'utilisateur a fait une typo ou si le tag est spécifique
        EXISTING_MINISTRAL=$(ollama list | grep "ministral" | head -n 1 | awk '{print $1}')
        if [ -n "$EXISTING_MINISTRAL" ]; then
             echo -e "${YELLOW}[INFO] Tentative d'utilisation du modèle local trouvé : $EXISTING_MINISTRAL${NC}"
             BASE_MODEL=$EXISTING_MINISTRAL
        else
             exit 1
        fi
    fi
fi

# 5. GÉNÉRATION DU MODELFILE
echo -e "${GREEN}[OLLAMA] Génération du Modelfile optimisé...${NC}"

cat <<EOF > $MODELFILE
FROM $BASE_MODEL

# Paramètres de performance
PARAMETER num_thread $NUM_THREAD
PARAMETER num_ctx 2048
PARAMETER num_batch 256
# PARAMETER use_mlock true # Deprecated in newer Ollama versions

TEMPLATE """{{ if .System }}<|system|>
{{ .System }}</s>
{{ end }}{{ if .User }}<|user|>
{{ .User }}</s>
{{ end }}{{ if .Assistant }}<|assistant|>
{{ .Assistant }}</s>
{{ end }}"""
EOF

echo -e "${GREEN}[OK] Modelfile créé :${NC}"
cat $MODELFILE

# 6. CRÉATION DU MODÈLE OLLAMA
echo -e "${GREEN}[OLLAMA] Création du modèle '$MODEL_NAME'...${NC}"
if ollama create $MODEL_NAME -f $MODELFILE; then
    echo -e "${GREEN}[OK] Modèle '$MODEL_NAME' créé avec succès.${NC}"
else
    echo -e "${RED}[ERREUR] Échec de la création du modèle. Vérifiez qu'Ollama tourne (systemctl status ollama) et que le modèle de base est pullé.${NC}"
    exit 1
fi

# 6. BENCHMARKING
PROMPT="Explique la thermodynamique en 20 mots."
echo -e "${GREEN}=== Lancement du Benchmark ===${NC}"
echo -e "Prompt de test : \"$PROMPT\""
echo -e "En attente de la réponse..."

# Appel API via curl
# On utilise time pour la durée totale brute, mais on va parser le JSON pour les stats précises
echo -e "${YELLOW}[INFO] Envoi de la requête... (Le premier run peut prendre du temps pour charger le modèle en RAM)${NC}"

# Timeout de 300s (5min) pour éviter le blocage infini, mode verbeux en cas d'erreur
RESPONSE=$(curl -s --max-time 300 -X POST http://localhost:11434/api/generate -d "{
  \"model\": \"$MODEL_NAME\",
  \"prompt\": \"$PROMPT\",
  \"stream\": false
}")

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERREUR] Le curl a échoué ou a timed out.${NC}"
    exit 1
fi


# Extraction des métriques avec grep/awk (pour éviter dépendance jq)
EVAL_COUNT=$(echo "$RESPONSE" | grep -o '"eval_count":[0-9]*' | cut -d':' -f2)
EVAL_DURATION=$(echo "$RESPONSE" | grep -o '"eval_duration":[0-9]*' | cut -d':' -f2)

echo -e "${YELLOW}[RÉSULTAT BRUT]${NC}"
# Afficher un extrait de la réponse pour confirmer
echo "$RESPONSE" | grep -o '"response":"[^"]*"' | cut -d'"' -f4

if [[ -n "$EVAL_COUNT" && -n "$EVAL_DURATION" && "$EVAL_DURATION" -gt 0 ]]; then
    # Calcul T/s : (eval_count / eval_duration) * 10^9
    # Bash ne gère pas les flottants, on utilise awk
    TS=$(awk -v count="$EVAL_COUNT" -v dur="$EVAL_DURATION" 'BEGIN {Kv = 1000000000; printf "%.2f", (count * Kv / dur)}')
    
    echo -e "\n${GREEN}=== PERFORMANCE ===${NC}"
    echo -e "Tokens générés : $EVAL_COUNT"
    echo -e "Durée éval (ns): $EVAL_DURATION"
    echo -e "${RED}Vitesse        : $TS Tokens/Sec${NC}"
    echo -e "${GREEN}===================${NC}"
else
    echo -e "${RED}[ERREUR] Impossible de récupérer les métriques de performance.${NC}"
    echo "Réponse API: $RESPONSE"
fi

echo -e "${GREEN}Optimisation terminée.${NC}"
