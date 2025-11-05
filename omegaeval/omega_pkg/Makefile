CC = gcc
CFLAGS = -Iinclude -O2 -Wall
SRCDIR = src
SRCS = $(SRCDIR)/runtime.c $(SRCDIR)/parser.c $(SRCDIR)/omega_bin.c
OBJS = $(SRCS:.c=.o)
all: omega-bin
$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c -o $@ $<
omega-bin: $(OBJS)
	$(CC) -o $@ $(OBJS)
clean:
	rm -f $(SRCDIR)/*.o omega-bin
