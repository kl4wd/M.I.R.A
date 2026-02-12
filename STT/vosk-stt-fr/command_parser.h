#ifndef COMMAND_PARSER_H
#define COMMAND_PARSER_H

typedef enum {
  CMD_UNKNOWN = 0,
  CMD_DROITE_45,
  CMD_GAUCHE_45,
  CMD_STOP,
  CMD_AVANCE,
  CMD_RECULE,
  CMD_POSITION,
  CMD_SCANNE,
  CMD_AUTOPILOT
} CommandType;

// Normalizes text (lowercase, removes punctuation)
void normalize_text(char *dest, const char *src);

// Parses text to find a command
CommandType parse_command(const char *text);

// Returns a string representation of the command action
const char *get_command_action(CommandType cmd);

#endif
