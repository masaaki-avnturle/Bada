CC = gcc
CFLAGS = -Iinclude -O2
SRCDIR = src
all: omega-bin omega_compiler
$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c -o $@ $<
omega-bin: $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o
	$(CC) -o $@ $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o
omega_compiler: $(SRCDIR)/omega_compiler.c $(SRCDIR)/runtime.o
	$(CC) $(CFLAGS) -o $@ $(SRCDIR)/omega_compiler.c $(SRCDIR)/runtime.o
clean:
	rm -f $(SRCDIR)/*.o omega-bin omega_compiler __omega_embedded.c compiled_omega_exec
