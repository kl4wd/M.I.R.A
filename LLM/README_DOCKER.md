# Docker Optimisé pour Ollama (Pi 5 & Ryzen 9 WSL2)

Solution conteneurisée "Zero-Config" pour déployer `ministral:3b` avec des performances maximales sur Raspberry Pi 5 et PC (WSL2/Linux).

## Fonctionnalités

- **Image Unique Multi-Arch** : Fonctionne sur `linux/arm64` (Pi 5) et `linux/amd64` (Ryzen/Intel).
- **Auto-Optimisation** au démarrage :
  - **Pi 5** : 4 threads, économie mémoire.
  - **Ryzen/PC** : 8 threads, `f16_kv` activé pour la vitesse.
- **Outils Intégrés** : `curl`, `jq` et script de benchmark.

## Installation

### 1. Construction de l'image (Build)

Dans le dossier contenant `Dockerfile`, `entrypoint.sh` et `benchmark.sh` :

```bash
docker build -t ministral-optimized .
```

### 2. Démarrage (Run)

Lancez le conteneur en arrière-plan.
**Important** : Le premier lancement prendra du temps (téléchargement du modèle).

```bash
docker run -d \
  --name ministral-server \
  --restart unless-stopped \
  -v ollama_data:/root/.ollama \
  -p 11434:11434 \
  --memory-swappiness=0 \
  ministral-optimized
```

_Note : `--memory-swappiness=0` empêche le swap sur disque, crucial pour les perfs._
_Note : `-v ollama_data:/root/.ollama` persiste les modèles téléchargés._

### 3. Vérification des Logs

Suivez l'initialisation pour voir la détection de votre matériel :

```bash
docker logs -f ministral-server
```

Vous devriez voir `[CONFIG] ...` indiquant le profil choisi (RPi 5 ou Ryzen).

### 4. Benchmark de Performance

Une fois le serveur prêt (logs indiquant `[ENTRYPOINT] Serveur opérationnel`), lancez le benchmark intégré :

```bash
docker exec -it ministral-server /benchmark.sh
```

Cela affichera le nombre de tokens/seconde précis.

### 5. Utilisation avec vos apps

Le serveur est accessible sur `http://localhost:11434`.
Le modèle optimisé s'appelle `ministral-turbo`.

Exemple d'appel :

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "ministral-turbo",
  "prompt": "Bonjour !"
}'
```
