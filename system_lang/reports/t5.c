エラーはリンク時に `main` を含むオブジェクトがリンク対象になっていないため発生しています。確実に `main.c` をコンパイルしてリンクするように、以下を修正してください。

1) 修正済みソース：`package/src/main.c`
（ヘッダはインクルードパスを使う形に変更）

```c
   /* package/src/main.c */
#include "usb-decrypter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

   /* hex -> binary (expects exactly outlen*2 hex chars) */
static int hex2bin(const char *hex, unsigned char *out, size_t outlen) {
  size_t hlen = strlen(hex);
  if (hlen != outlen * 2) return -1;
  for (size_t i = 0; i < outlen; ++i) {
    int hi = -1, lo = -1;
    char c1 = hex[2*i], c2 = hex[2*i+1];
    if (c1 >= '0' && c1 <= '9') hi = c1 - '0';
    else if (c1 >= 'a' && c1 <= 'f') hi = c1 - 'a' + 10;
    else if (c1 >= 'A' && c1 <= 'F') hi = c1 - 'A' + 10;
    if (c2 >= '0' && c2 <= '9') lo = c2 - '0';
    else if (c2 >= 'a' && c2 <= 'f') lo = c2 - 'a' + 10;
    else if (c2 >= 'A' && c2 <= 'F') lo = c2 - 'A' + 10;
    if (hi < 0 || lo < 0) return -2;
    out[i] = (unsigned char)((hi << 4) | lo);
  }
  return 0;
   }

int main(int argc, char **argv) {
  if (argc != 4) {
    fprintf(stderr, "Usage: %s <infile> <outfile> <hex-key-32bytes>\n", argv[0]);
    return 2;
  }
  const char *in = argv[1];
  const char *out = argv[2];
  const char *keyhex = argv[3];
  unsigned char key[32];
  if (hex2bin(keyhex, key, sizeof(key)) != 0) {
    fprintf(stderr, "Invalid key hex (must be 64 hex chars)\n");
    return 3;
  }
  int r = decrypt_file_with_libsodium(in, out, key);
  if (r != 0) {
    fprintf(stderr, "decrypt_file_with_libsodium failed: %d\n", r);
    return 4;
  }
  printf("Decryption succeeded: %s -> %s\n", in, out);
  return 0;
}
```

2) 修正済み Makefile：`package/Makefile`
- `SRC_DIR = src` 配下の全 .c をコンパイルし、必ず main をリンクするようにする。
    - ヘッダ検索パスは `-I$(INC_DIR)` とする（src 内の `#include "usb-decrypter.h"` に対応）。

```
# package/Makefile
CC = gcc
  CFLAGS = -Wall -Wextra -O2 -I$(INC_DIR)
LDFLAGS = -lsodium

SRC_DIR = src
INC_DIR = include
BIN_DIR = bin
OBJ_DIR = build

  SRCS = $(wildcard $(SRC_DIR)/*.c)
OBJS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRCS))
TARGET = $(BIN_DIR)/usb-decrypter

.PHONY: all clean dirs

all: dirs $(TARGET)

dirs:
mkdir -p $(BIN_DIR) $(OBJ_DIR)

$(TARGET): $(OBJS)
$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c $(INC_DIR)/usb-decrypter.h
$(CC) $(CFLAGS) -c $< -o $@

clean:
rm -rf $(OBJ_DIR) $(BIN_DIR)/usb-decrypter
```

手順
- `package/src/` に上の `main.c` を置く（既存の `libsodium_decrypt.c` と `toy_polynomial_codec.c` はそのまま）。
- `package/Makefile` を上書き。
- package ディレクトリで `make` を実行。

これで main を含むオブジェクトが確実に作られ、リンクエラー（undefined reference to main）は解消されるはずです。
