#ifndef COMMAND_EXECUTOR_H
#define COMMAND_EXECUTOR_H

#include "command_parser.h"

// Initialize the executor (check scripts existence, etc.)
void init_executor();

// Execute the script corresponding to the command
void execute_command(CommandType cmd);

#endif
