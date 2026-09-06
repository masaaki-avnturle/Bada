エラー "undefined reference to 'main'" は、リンク時に `main` 関数を含むオブジェクトが無いため発生します。対処として、実行ファイルのエントリポイントを提供する `main.c`（または既存のソースに `main` を追加）を作成し、Makefile を修正してビルド対象に含めます。

以下は修正版の追加ファイル（`package/src/main.c`）と、先に示した package/Makefile をこの main を使うように変更した内容です。

1) ファイル: package/src/main.c
```c
	     /* simple main for usb-decrypter
   Usage: usb-decrypter <infile> <outfile> <hex-key-32bytes>
	     */
#include "../include/usb-decrypter.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

	     /* helper: parse hex (expects lowercase/uppercase hex without 0x) */
static int hex2bin(const char *hex, unsigned char *out, size_t outlen) {
  size_t hlen = strlen(hex);
  if (hlen != outlen * 2) return -1;
  for (size_t i = 0; i < outlen; i++) {
    char hi = hex[2*i], lo = hex[2*i+1];
    int vhi = (hi >= '0' && hi <= '9') ? hi - '0' :
      (hi >= 'a' && hi <= 'f') ? hi - 'a' + 10 :
      (hi >= 'A' && hi <= 'F') ? hi - 'A' + 10 : -1;
    int vlo = (lo >= '0' && lo <= '9') ? lo - '0' :
      (lo >= 'a' && lo <= 'f') ? lo - 'a' + 10 :
      (lo >= 'A' && lo <= 'F') ? lo - 'A' + 10 : -1;
    if (vhi < 0 || vlo < 0) return -2;
    out[i] = (unsigned char)((vhi << 4) | vlo);
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

2) 修正版 Makefile（package/Makefile）
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
1. package/src に上の `main.c` を保存する。既にある `libsodium_decrypt.c` と `toy_polynomial_codec.c` はそのままで良いです。
2. package ディレクトリに上の Makefile を保存（上書き）。
3. 依存パッケージを用意（例: Debian/Ubuntu: `sudo apt install libsodium-dev`）。
4. ビルド:
   - cd package
   - make

これでリンクエラー "undefined reference to 'main'" は解消され、実行ファイル `package/bin/usb-decrypter` が生成されます。
