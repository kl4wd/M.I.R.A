#include "command_parser.h"
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

// Minimum of three integers
int min3(int a, int b, int c) {
  int m = a;
  if (b < m)
    m = b;
  if (c < m)
    m = c;
  return m;
}

// Levenshtein distance calculation
int levenshtein_distance(const char *s1, const char *s2) {
  int len1 = strlen(s1);
  int len2 = strlen(s2);

  // Rows for dynamic programming (we only need two rows)
  int *v0 = malloc((len2 + 1) * sizeof(int));
  int *v1 = malloc((len2 + 1) * sizeof(int));

  if (!v0 || !v1)
    return -1; // Allocation error

  for (int i = 0; i <= len2; i++)
    v0[i] = i;

  for (int i = 0; i < len1; i++) {
    v1[0] = i + 1;
    for (int j = 0; j < len2; j++) {
      int cost = (s1[i] == s2[j]) ? 0 : 1;
      v1[j + 1] = min3(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost);
    }
    // Copy v1 to v0 for next iteration
    for (int j = 0; j <= len2; j++)
      v0[j] = v1[j];
  }

  int res = v0[len2];
  free(v0);
  free(v1);
  return res;
}

// Global struct for commands
typedef struct {
  const char *phrase;
  CommandType cmd;
} CommandEntry;

static CommandEntry commands[] = {
    {"droite", CMD_DROITE_45},    {"tourne droite", CMD_DROITE_45},
    {"gauche", CMD_GAUCHE_45},    {"tourne gauche", CMD_GAUCHE_45},
    {"stop", CMD_STOP},           {"arrete", CMD_STOP},
    {"avancer", CMD_AVANCE},      {"avance", CMD_AVANCE},
    {"reculer", CMD_RECULE},      {"recule", CMD_RECULE},
    {"position", CMD_POSITION},   {"ou es tu", CMD_POSITION},
    {"scanne", CMD_SCANNE},       {"scan", CMD_SCANNE},
    {"autopilot", CMD_AUTOPILOT}, {"pilote automatique", CMD_AUTOPILOT},
    {NULL, CMD_UNKNOWN}};

// Remove stop words and punctuation
void normalize_and_clean(char *dest, const char *src) {
  char temp[1024];
  int j = 0;

  // 1. Lowercase and keep only alphanumeric/space
  for (int i = 0; src[i] != '\0'; i++) {
    if (isalnum((unsigned char)src[i]) || isspace((unsigned char)src[i])) {
      temp[j++] = tolower((unsigned char)src[i]);
    }
  }
  temp[j] = '\0';

  // 2. Remove stop words
  const char *stop_words[] = {"le",   "la",  "un",   "une",  "des",   "fais",
                              "peux", "tu",  "il",   "elle", "ce",    "de",
                              "a",    "est", "s'il", "te",   "plait", NULL};

  dest[0] = '\0';
  char *token = strtok(temp, " ");
  int first = 1;

  while (token != NULL) {
    int is_stop = 0;
    for (int k = 0; stop_words[k] != NULL; k++) {
      if (strcmp(token, stop_words[k]) == 0) {
        is_stop = 1;
        break;
      }
    }

    if (!is_stop) {
      if (!first)
        strcat(dest, " ");
      strcat(dest, token);
      first = 0;
    }
    token = strtok(NULL, " ");
  }
}

// Kept for compatibility if header declares it
void normalize_text(char *dest, const char *src) {
  normalize_and_clean(dest, src);
}

CommandType parse_command(const char *text) {
  char cleaned[1024];
  normalize_and_clean(cleaned, text);

  // printf("Debug: Cleaned text: '%s'\n", cleaned);

  CommandType best_cmd = CMD_UNKNOWN;
  int best_dist = 1000;

  // Iterate over all target command phrases
  for (int i = 0; commands[i].phrase != NULL; i++) {
    int dist = levenshtein_distance(cleaned, commands[i].phrase);
    int len = strlen(commands[i].phrase);

    // Dynamic threshold: 1 error allowed for short words, 2 for longer phrases
    int threshold = (len <= 4) ? 1 : 2;

    if (dist <= threshold && dist < best_dist) {
      best_dist = dist;
      best_cmd = commands[i].cmd;
    }
  }

  return best_cmd;
}

const char *get_command_action(CommandType cmd) {
  switch (cmd) {
  case CMD_DROITE_45:
    return "DROITE_45";
  case CMD_GAUCHE_45:
    return "GAUCHE_45";
  case CMD_STOP:
    return "STOP";
  case CMD_AVANCE:
    return "AVANCER";
  case CMD_RECULE:
    return "RECULER";
  case CMD_POSITION:
    return "POSITION";
  case CMD_SCANNE:
    return "SCANNE";
  case CMD_AUTOPILOT:
    return "AUTOPILOT";
  default:
    return NULL;
  }
}
