CC = gcc
CFLAGS = -O2 
SRC = src/remapper.c src/emacs_bindings.c src/vim_bindings.c
OUT = remapper.exe
all: check_compiler $(OUT)
$(OUT): $(SRC)	$(CC) $(CFLAGS) $(SRC) -o $(OUT) -luser32 -lpsapi
check_compiler:
	@command -v $(CC) >/dev/null 2>&1 || (echo "$(CC) not found. Install mingw-w64." && exit 1)
clean:
	rm -f remapper.exe
.PHONY: all clean check_compiler
