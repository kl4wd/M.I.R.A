# Optimisation Ollama (Pi 5 & WSL2)

Ce script configure et optimise automatiquement Ollama pour maximiser les performances (tokens/seconde) sur Raspberry Pi 5 et WSL2, spécifiquement pour le modèle Ministral 3B.

## Prérequis

- **Ollama** installé et en cours d'exécution via `systemd` (Linux/Pi) ou application desktop (Windows/WSL).
- **Curl** (généralement préinstallé).
- **Sudo** (pour l'optimisation swap sur Pi 5).

## Installation

1. Téléchargez ou créez le script `optimize_ollama.sh` :

   ```bash
   nano optimize_ollama.sh
   # Collez le contenu du script
   # Sauvegardez (Ctrl+O, Entrée, Ctrl+X)
   ```

2. Rendez le script exécutable :
   ```bash
   chmod +x optimize_ollama.sh
   ```

## Utilisation

Exécutez simplement le script :

```bash
./optimize_ollama.sh
```

### Ce que fait le script :

1. **Détection Automatique** : Identifie si vous êtes sur un Raspberry Pi 5 (ARM64) ou WSL2 (x86_64).
2. **Optimisation Threads** :
   - **Pi 5** : Force à 4 threads (cœurs physiques) pour éviter la surcharge.
   - **WSL2** : Détecte les cœurs disponibles.
3. **Optimisation OS** :
   - **Pi 5** : Réduit l'utilisation du swap (`vm.swappiness=1`).
4. **Configuration Ollama** :
   - Désactive le parallélisme (`OLLAMA_NUM_PARALLEL=1`).
   - Maintient le modèle chargé (`OLLAMA_KEEP_ALIVE=-1`).
5. **Génération Modèle** : Crée une version optimisée `ministral-turbo` avec un contexte réduit (2048) et le verrouillage en RAM (`mlock`).
6. **Benchmark** : Lance un test via l'API et calcule précisément les tokens/seconde.

## Note pour les utilisateurs WSL2

Le script ne peut pas modifier directement la configuration de Windows. Pour des performances maximales :

1. Créez/Modifiez le fichier `C:\Users\VOTRE_UTILISATEUR\.wslconfig`.
2. Ajoutez :
   ```ini
   [wsl2]
   memory=12GB   # Ajustez selon votre RAM (laissez 4GB pour Windows)
   processors=8  # Ajustez selon vos cœurs CPU
   ```
3. Redémarrez WSL : `wsl --shutdown` dans PowerShell.
