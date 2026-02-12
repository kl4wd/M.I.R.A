#ifndef LLM_CLIENT_H
#define LLM_CLIENT_H

// Helper function to send text to local Ollama instance
// Returns 0 on success, -1 on failure.
// The response is printed directly to stdout for now.
int send_to_llm(const char *prompt);

#endif
