こちらが package 一式を生成する `pkginstallgen.c` の完全なソースコードです。これをコンパイルして実行すると、カレントディレクトリに `package/` ディレクトリを作成し、修正済みの Makefile とソース群を配置します。

```c
/* pkginstallgen.c
   実行:
     gcc pkginstallgen.c -o pkginstallgen
     ./pkginstallgen
   すると ./package 以下にビルド可能なソースツリーが生成されます。
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

static int mkdir_p(const char *path) {
  char tmp[4096];
  size_t len = snprintf(tmp, sizeof(tmp), "%s", path);
  if (len == 0 || len >= sizeof(tmp)) return -1;
  for (size_t i = 1; i < len; ++i) {
    if (tmp[i] == '/') {
      tmp[i] = '\0';
      if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
      tmp[i] = '/';
    }
  }
  if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
  return 0;
}

static int write_file(const char *path, const char *data) {
  FILE *f = fopen(path, "wb");
  if (!f) {
    fprintf(stderr, "fopen %s: %s\n", path, strerror(errno));
    return -1;
  }
  if (fputs(data, f) == EOF) {
    fprintf(stderr, "write %s failed\n", path);
    fclose(f);
    return -1;
  }
  fclose(f);
  return 0;
}

int main(void) {
  const char *dirs[] = {
    "package",
    "package/include",
    "package/src",
    "package/bin",
        "package/build"
  };
  for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) {
    if (mkdir_p(dirs[i]) != 0) {
      fprintf(stderr, "mkdir_p %s failed: %s\n", dirs[i], strerror(errno));
      return 1;
    }
  }

    const char *makefile =
"# package/Makefile\n"
"CC = gcc\n"
"CFLAGS = -Wall -Wextra -O2 -I$(INC_DIR)\n"
"LDFLAGS = -lsodium\n"
"\n"
"SRC_DIR = src\n"
"INC_DIR = include\n"
"BIN_DIR = bin\n"
"OBJ_DIR = build\n"
"\n"
"SRCS = $(wildcard $(SRC_DIR)/*.c)\n"
"OBJS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRCS))\n"
"TARGET = $(BIN_DIR)/usb-decrypter\n"
"\n"
".PHONY: all clean dirs\n"
"\n"
"all: dirs $(TARGET)\n"
"\n"
"dirs:\n"
"\t@mkdir -p $(BIN_DIR) $(OBJ_DIR)\n"
"\n"
"$(TARGET): $(OBJS)\n"
"\t$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS)\n"
"\n"
"$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c $(INC_DIR)/usb-decrypter.h\n"
"\t$(CC) $(CFLAGS) -c $< -o $@\n"
"\n"
"clean:\n"
      "\trm -rf $(OBJ_DIR) $(BIN_DIR)/usb-decrypter\n";

    const char *header =
"#ifndef USB_DECRYPTER_H\n"
"#define USB_DECRYPTER_H\n"
"\n"
"#include <stddef.h>\n"
"#include <stdint.h>\n"
"\n"
"/*\n"
" * decrypt_file_with_libsodium:\n"
" * - inpath: 暗号化ファイル（nonce(24) + ciphertext+mac）\n"
" * - outpath: 復号出力ファイル\n"
" * - key: 32 バイトの対称鍵（呼び出し側で安全に管理）\n"
" * 戻り値: 0=成功, 非0=エラー\n"
      " */\n"
"int decrypt_file_with_libsodium(const char *inpath, const char *outpath, const unsigned char key[32]);\n"
"\n"
      "/* Toy polynomial codec (education): encode/decode reversible mapping */\n"
"int toy_encode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen);\n"
"int toy_decode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen);\n"
"\n"
      "#endif /* USB_DECRYPTER_H */\n";

    const char *main_c =
      "/* package/src/main.c */\n"
"#include \"usb-decrypter.h\"\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <stdint.h>\n"
"\n"
      "/* hex -> binary (expects exactly outlen*2 hex chars) */\n"
"static int hex2bin(const char *hex, unsigned char *out, size_t outlen) {\n"
"    size_t hlen = strlen(hex);\n"
"    if (hlen != outlen * 2) return -1;\n"
"    for (size_t i = 0; i < outlen; ++i) {\n"
"        int hi = -1, lo = -1;\n" 
"        char c1 = hex[2*i], c2 = hex[2*i+1];\n"
"        if (c1 >= '0' && c1 <= '9') hi = c1 - '0';\n"
"        else if (c1 >= 'a' && c1 <= 'f') hi = c1 - 'a' + 10;\n"
"        else if (c1 >= 'A' && c1 <= 'F') hi = c1 - 'A' + 10;\n"
"        if (c2 >= '0' && c2 <= '9') lo = c2 - '0';\n"
"        else if (c2 >= 'a' && c2 <= 'f') lo = c2 - 'a' + 10;\n"
"        else if (c2 >= 'A' && c2 <= 'F') lo = c2 - 'A' + 10;\n"
"        if (hi < 0 || lo < 0) return -2;\n"
"        out[i] = (unsigned char)((hi << 4) | lo);\n"
"    }\n"
"    return 0;\n"
"}\n"
"\n"
"int main(int argc, char **argv) {\n"
"    if (argc != 4) {\n"
"        fprintf(stderr, \"Usage: %s <infile> <outfile> <hex-key-32bytes>\\n\", argv[0]);\n"
"        return 2;\n"
"    }\n"
"    const char *in = argv[1];\n"
"    const char *out = argv[2];\n" 
"    const char *keyhex = argv[3];\n"
"    unsigned char key[32];\n"
"    if (hex2bin(keyhex, key, sizeof(key)) != 0) {\n"
"        fprintf(stderr, \"Invalid key hex (must be 64 hex chars)\\n\");\n"
"        return 3;\n"
"    }\n"
"    int r = decrypt_file_with_libsodium(in, out, key);\n"
"    if (r != 0) {\n"
"        fprintf(stderr, \"decrypt_file_with_libsodium failed: %d\\n\", r);\n"
"        return 4;\n"
"    }\n"
"    printf(\"Decryption succeeded: %s -> %s\\n\", in, out);\n"
"    return 0;\n"
      "}\n";

    const char *libsodium_c =
      "/* package/src/libsodium_decrypt.c */\n"
"#include \"usb-decrypter.h\"\n"
"#include <sodium.h>\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"\n"
"int decrypt_file_with_libsodium(const char *inpath, const char *outpath, const unsigned char key[32]) {\n"
      "    if (sodium_init() < 0) return -1; /* libsodium 初期化失敗 */\n"
"    FILE *f = fopen(inpath, \"rb\");\n"
"    if (!f) return -2;\n"
"    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return -3; }\n"
"    long flen = ftell(f);\n"
"    rewind(f);\n"
"    if (flen <= 24) { fclose(f); return -4; }\n"
"    unsigned char nonce[24];\n"
"    if (fread(nonce, 1, 24, f) != 24) { fclose(f); return -5; }\n"
"    size_t clen = (size_t)flen - 24;\n"
"    unsigned char *cipher = malloc(clen);\n"
"    if (!cipher) { fclose(f); return -6; }\n"
"    if (fread(cipher, 1, clen, f) != clen) { free(cipher); fclose(f); return -7; }\n"
"    fclose(f);\n"
"    unsigned char *plain = malloc(clen);\n"
"    if (!plain) { free(cipher); return -8; }\n"
"    if (crypto_secretbox_open_easy(plain, cipher, clen, nonce, key) != 0) {\n"
    "        free(cipher); free(plain); return -9; /* 復号失敗（認証エラー等）*/\n"
"    }\n"
"    FILE *out = fopen(outpath, \"wb\");\n"
"    if (!out) { free(cipher); free(plain); return -10; }\n"
"    size_t plen = clen - crypto_secretbox_MACBYTES;\n"
"    if (fwrite(plain, 1, plen, out) != plen) { fclose(out); free(cipher); free(plain); return -11; }\n"
"    fclose(out);\n"
"    free(cipher); free(plain);\n"
"    return 0;\n"
      "}\n";

    const char *toy_c =
      "/* package/src/toy_polynomial_codec.c */\n"
"#include \"usb-decrypter.h\"\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <stdint.h>\n"
"\n"
"/*\n"
" * toy_encode / toy_decode:\n"
" * - 教育目的: 入力バイト列をそのまま可逆にコピーする簡易実装\n"
" * - 実際の暗号ではない。\n"
      " */\n"
"int toy_encode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen) {\n"
"    if (!in || !out || !outlen) return -1;\n"
"    if (*outlen < inlen) return -2;\n"
"    memcpy(out, in, inlen);\n"
"    *outlen = inlen;\n"
"    return 0;\n"
"}\n"
"\n"
"int toy_decode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen) {\n"
"    return toy_encode(in, inlen, out, outlen);\n"
      "}\n";

    if (write_file("package/Makefile", makefile) != 0) return 2;
    if (write_file("package/include/usb-decrypter.h", header) != 0) return 3;
    if (write_file("package/src/main.c", main_c) != 0) return 4;
    if (write_file("package/src/libsodium_decrypt.c", libsodium_c) != 0) return 5;
    if (write_file("package/src/toy_polynomial_codec.c", toy_c) != 0) return 6;

    /* make run script in package/bin */
    const char *runsh =
"#!/bin/sh\n"
      "echo \"Usage: ./bin/usb-decrypter <infile> <outfile> <hex-key-32bytes>\"\n";
    if (write_file("package/bin/run_decrypt.sh", runsh) != 0) return 7;
    chmod("package/bin/run_decrypt.sh", 0755);

    printf("package skeleton generated at ./package\n");
    printf("Build: cd package && make\n");
    return 0;
}
```

使用手順（要約）
- gcc pkginstallgen.c -o pkginstallgen
- ./pkginstallgen
- cd package
- sudo apt install libsodium-dev   （必要時）
- make
- 実行: ./bin/usb-decrypter <infile> <outfile> <64-hex-key>

注意: 生成物は教育・合法的用途向けのテンプレートです。他者のデータを無断で扱わないでください。
