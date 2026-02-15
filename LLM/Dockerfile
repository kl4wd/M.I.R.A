FROM ollama/ollama:latest

# Installation des outils nécessaires
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Copie des scripts
COPY entrypoint.sh /entrypoint.sh
COPY benchmark.sh /benchmark.sh

# Permissions d'exécution
RUN chmod +x /entrypoint.sh /benchmark.sh

# Variables d'environnement pour performance
ENV OLLAMA_KEEP_ALIVE=-1
ENV OLLAMA_NUM_PARALLEL=1

# Point d'entrée
ENTRYPOINT ["/entrypoint.sh"]
