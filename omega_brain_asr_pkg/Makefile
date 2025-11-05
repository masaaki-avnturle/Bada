CC ?= gcc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra
TOOLS_DIR := usr/tools
LANG_DIR := usr/lang
ASR_SRC := $(TOOLS_DIR)/asr_engine.c
ASR_BIN := $(TOOLS_DIR)/asr_engine
OMEGA_SRC := $(LANG_DIR)/omegascript.c
OMEGA_BIN := $(LANG_DIR)/omegascript
.PHONY: all asr omega clean
all: asr omega
asr: $(ASR_BIN)
$(ASR_BIN): $(ASR_SRC)
	@mkdir -p $(TOOLS_DIR)
	$(CC) $(CFLAGS) -o $@ $<
omega: $(OMEGA_BIN)
$(OMEGA_BIN): $(OMEGA_SRC)
	@mkdir -p $(LANG_DIR)
	$(CC) $(CFLAGS) -o $@ $<
clean:
	-@rm -f $(ASR_BIN) $(OMEGA_BIN)
