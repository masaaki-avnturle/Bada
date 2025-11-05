CC = gcc
CFLAGS = -Iinclude -O2
SRCDIR = src
all: omega-bin
$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c -o $@ $<
omega-bin: $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o
	$(CC) -o $@ $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o
clean:
	rm -f $(SRCDIR)/*.o omega-bin
