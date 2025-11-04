CC = gcc
CFLAGS = -Iinclude -O2
SRCDIR = src
all: omega-bin bnf_codegen
$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c -o $@ $<
omega-bin: $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o
	$(CC) -o $@ $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o
bnf_codegen: $(SRCDIR)/bnf_codegen.c
	$(CC) -o bnf_codegen $(SRCDIR)/bnf_codegen.c
clean:
	rm -f $(SRCDIR)/*.o omega-bin bnf_codegen __omega_embedded.c compiled_omega_exec
