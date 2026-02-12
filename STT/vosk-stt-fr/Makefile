CC = gcc
CFLAGS = -I./vosk-api/src -Wall
LDFLAGS = -L./vosk-api/src -lvosk -lportaudio -Wl,-rpath=./vosk-api/src

all: stt_app

stt_app: main.o command_parser.o llm_client.o command_executor.o
	$(CC) -o $@ $^ $(LDFLAGS)

main.o: main.c
	$(CC) -c -o $@ $< $(CFLAGS)

command_parser.o: command_parser.c
	$(CC) -c -o $@ $< $(CFLAGS)

llm_client.o: llm_client.c
	$(CC) -c -o $@ $< $(CFLAGS)

command_executor.o: command_executor.c
	$(CC) -c -o $@ $< $(CFLAGS)

clean:
	rm -f *.o stt_app

run: stt_app
	./stt_app
