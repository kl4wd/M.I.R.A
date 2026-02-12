#include "command_executor.h"
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

// Helper to check if a file exists and is executable
static int check_script(const char *path) {
  struct stat sb;
  if (stat(path, &sb) == 0 && (sb.st_mode & S_IXUSR)) {
    return 1;
  }
  return 0;
}

void init_executor() {
  // Optional: We could check here if all scripts exist
  printf("[EXECUTOR] Initialized.\n");
}

void execute_command(CommandType cmd) {
  const char *script = NULL;

  switch (cmd) {
  case CMD_AVANCE:
    script = "./actions/avancer.sh";
    break;
  case CMD_RECULE:
    script = "./actions/reculer.sh";
    break;
  case CMD_STOP:
    script = "./actions/stop.sh";
    break;
  case CMD_POSITION:
    script = "./actions/position.sh";
    break;
  case CMD_AUTOPILOT:
    script = "./actions/autopilot.sh";
    break;
  case CMD_SCANNE:
    script = "./actions/scanne.sh";
    break;
  case CMD_DROITE_45:
    // TODO: Create script if needed, or map to existing
    printf("[EXECUTOR] Commande DROITE non implémentée en script.\n");
    return;
  case CMD_GAUCHE_45:
    // TODO
    printf("[EXECUTOR] Commande GAUCHE non implémentée en script.\n");
    return;
  default:
    printf("[EXECUTOR] Commande inconnue ou sans script.\n");
    return;
  }

  if (script) {
    if (check_script(script)) {
      printf("[EXECUTOR] Exécution de : %s\n", script);
      // Use system() to run the script.
      // We append " &" to run in background so it doesn't block the STT loop
      // BUT for some actions we might want it blocking.
      // For now, let's keep it blocking or simple system() call.
      // If we want non-blocking:
      char cmd_line[256];
      snprintf(cmd_line, sizeof(cmd_line), "%s &", script);
      int ret = system(cmd_line);
      if (ret == -1) {
        perror("[EXECUTOR] Erreur execution system()");
      }
    } else {
      printf("[EXECUTOR] ERREUR : Le script '%s' est introuvable ou non "
             "exécutable.\n",
             script);
    }
  }
}
