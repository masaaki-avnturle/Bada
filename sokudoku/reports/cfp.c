了解しました。エスケープが多くて可読性・コンパイル性を損なっていた問題を解消した、修正版の `pkginstallgen.c` を下に示します。各出力ファイルの内容は「行の配列」を使って書き出す方式に変更しているため、長い文字列リテラルでの大量のエスケープが無くなり、コンパイル時のエラーや可読性の問題を避けられます。

使い方:
1. このファイルを保存（例: `pkginstallgen.c`）。
2. コンパイル: `gcc pkginstallgen.c -o pkginstallgen`
3. 実行: `./pkginstallgen` — カレントに `package/` 以下のツリーを生成します。
4. `cd package && make` でビルド（libsodium-dev と libm が必要）。

pkginstallgen.c（全文）
```c
	    /* pkginstallgen.c
   出力: ./package 以下にソースツリーを生成する。
   作成方法: gcc pkginstallgen.c -o pkginstallgen
              ./pkginstallgen
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

static int write_lines(const char *path, const char *lines[], size_t nlines, mode_t mode) {
    FILE *f = fopen(path, "wb");
    if (!f) {
        fprintf(stderr, "fopen %s: %s\n", path, strerror(errno));
		return -1;
		}
		for (size_t i = 0; i < nlines; ++i) {
		  if (fputs(lines[i], f) == EOF || fputc('\n', f) == EOF) {
		    fprintf(stderr, "write %s failed\n", path);
		    fclose(f);
		    return -1;
		  }
		}
fclose(f);
if (mode) chmod(path, mode);
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

  const char *makefile_lines[] = {
    "# package/Makefile",
    "CC = gcc",
    "CFLAGS = -Wall -Wextra -O2 -I$(INC_DIR)",
    "LDFLAGS = -lsodium -lm",
    "",
    "SRC_DIR = src",
    "INC_DIR = include",
    "BIN_DIR = bin",
    "OBJ_DIR = build",
    "",
    "SRCS = $(wildcard $(SRC_DIR)/*.c)",
    "OBJS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRCS))",
    "TARGET = $(BIN_DIR)/usb-decrypter",
    "",
    ".PHONY: all clean dirs",
    "",
    "all: dirs $(TARGET)",
    "",
    "dirs:",
    "\t@mkdir -p $(BIN_DIR) $(OBJ_DIR)",
    "",
    "$(TARGET): $(OBJS)",
    "\t$(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS)",
    "",
    "$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c $(INC_DIR)/usb-decrypter.h",
    "\t$(CC) $(CFLAGS) -c $< -o $@",
    "",
    "clean:",
        "\trm -rf $(OBJ_DIR) $(BIN_DIR)/usb-decrypter"
  };

  const char *header_lines[] = {
    "#ifndef USB_DECRYPTER_H",
    "#define USB_DECRYPTER_H",
    "",
    "#include <stddef.h>",
    "#include <stdint.h>",
    "",
    "/* decrypt_file_with_libsodium:",
    "   inpath: 暗号化ファイル（nonce(24) + ciphertext+mac）",
    "   outpath: 復号出力ファイル",
    "   key: 32 バイトの対称鍵",
    "   戻り値: 0=成功, 非0=エラー */",
    "int decrypt_file_with_libsodium(const char *inpath, const char *outpath, const unsigned char key[32]);",
    "",
    "/* Toy codec (教育目的) */",
    "int toy_encode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen);",
    "int toy_decode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen);",
    "",
    "#endif /* USB_DECRYPTER_H */"
  };

  const char *main_lines[] = {
    "/* package/src/main.c */",
    "#include \"usb-decrypter.h\"",
    "#include <stdio.h>",
    "#include <stdlib.h>",
    "#include <string.h>",
    "#include <stdint.h>",
    "",
    "static int hex2bin(const char *hex, unsigned char *out, size_t outlen) {",
    "    size_t hlen = strlen(hex);",
    "    if (hlen != outlen * 2) return -1;",
    "    for (size_t i = 0; i < outlen; ++i) {",
    "        int hi = -1, lo = -1;",
    "        char c1 = hex[2*i], c2 = hex[2*i+1];",
    "        if (c1 >= '0' && c1 <= '9') hi = c1 - '0';",
    "        else if (c1 >= 'a' && c1 <= 'f') hi = c1 - 'a' + 10;",
    "        else if (c1 >= 'A' && c1 <= 'F') hi = c1 - 'A' + 10;",
    "        if (c2 >= '0' && c2 <= '9') lo = c2 - '0';",
    "        else if (c2 >= 'a' && c2 <= 'f') lo = c2 - 'a' + 10;",
    "        else if (c2 >= 'A' && c2 <= 'F') lo = c2 - 'A' + 10;",
    "        if (hi < 0 || lo < 0) return -2;",
    "        out[i] = (unsigned char)((hi << 4) | lo);",
    "    }",
    "    return 0;",
    "}",
    "",
    "int main(int argc, char **argv) {",
    "    if (argc != 4) {",
    "        fprintf(stderr, \"Usage: %s <infile> <outfile> <hex-key-32bytes>\\n\", argv[0]);",
    "        return 2;",
    "    }",
    "    const char *in = argv[1];",
    "    const char *out = argv[2];",
    "    const char *keyhex = argv[3];",
    "    unsigned char key[32];",
    "    if (hex2bin(keyhex, key, sizeof(key)) != 0) {",
    "        fprintf(stderr, \"Invalid key hex (must be 64 hex chars)\\n\");",
    "        return 3;",
    "    }",
    "    int r = decrypt_file_with_libsodium(in, out, key);",
    "    if (r != 0) {",
    "        fprintf(stderr, \"decrypt_file_with_libsodium failed: %d\\n\", r);",
    "        return 4;",
    "    }",
    "    printf(\"Decryption succeeded: %s -> %s\\n\", in, out);",
    "    return 0;",
        "}"
  };

  const char *libsodium_lines[] = {
    "/* package/src/libsodium_decrypt.c */",
    "#include \"usb-decrypter.h\"",
    "#include <sodium.h>",
    "#include <stdio.h>",
    "#include <stdlib.h>",
    "#include <string.h>",
    "",
    "int decrypt_file_with_libsodium(const char *inpath, const char *outpath, const unsigned char key[32]) {",
    "    if (sodium_init() < 0) return -1; /* 初期化失敗 */",
    "    FILE *f = fopen(inpath, \"rb\");",
    "    if (!f) return -2;",
    "    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return -3; }",
    "    long flen = ftell(f);",
    "    rewind(f);",
    "    if (flen <= 24) { fclose(f); return -4; }",
    "    unsigned char nonce[24];",
    "    if (fread(nonce, 1, 24, f) != 24) { fclose(f); return -5; }",
    "    size_t clen = (size_t)flen - 24;",
    "    unsigned char *cipher = malloc(clen);",
    "    if (!cipher) { fclose(f); return -6; }",
    "    if (fread(cipher, 1, clen, f) != clen) { free(cipher); fclose(f); return -7; }",
    "    fclose(f);",
    "    unsigned char *plain = malloc(clen);",
    "    if (!plain) { free(cipher); return -8; }",
    "    if (crypto_secretbox_open_easy(plain, cipher, clen, nonce, key) != 0) {",
      "        free(cipher); free(plain); return -9; /* 復号失敗 */",
        "    }",
        "    FILE *out = fopen(outpath, \"wb\");",
        "    if (!out) { free(cipher); free(plain); return -10; }",
        "    size_t plen = clen - crypto_secretbox_MACBYTES;",
        "    if (fwrite(plain, 1, plen, out) != plen) { fclose(out); free(cipher); free(plain); return -11; }",
        "    fclose(out);",
        "    free(cipher); free(plain);",
        "    return 0;",
        "}"
      };

  const char *toy_lines[] = {
  "/* package/src/toy_polynomial_codec.c */",
    "#include \"usb-decrypter.h\"",
    "#include <stdlib.h>",
    "#include <string.h>",
    "#include <stdint.h>",
    "",
    "int toy_encode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen) {",
    "    if (!in || !out || !outlen) return -1;",
      "    if (*outlen < inlen) return -2;",
      "    memcpy(out, in, inlen);",
      "    *outlen = inlen;",
      "    return 0;",
      "}",
    "",
    "int toy_decode(const uint8_t *in, size_t inlen, uint8_t *out, size_t *outlen) {",
    "    return toy_encode(in, inlen, out, outlen);",
        "}"
    };

  const char *math_example_lines[] = {
  "/* package/src/math_example.c */",
    "#include \"usb-decrypter.h\"",
    "#include <math.h>",
    "#include <stdio.h>",
    "",
    "double compute_example(double x) {",
    "    return pow(x, 2.0) + log(x);",
      "}",
    "",
    "void math_example_dummy(void) {",
    "    printf(\"math_example loaded\\n\");",
        "}"
    };

  if (write_lines("package/Makefile", makefile_lines, sizeof(makefile_lines)/sizeof(makefile_lines[0]), 0) != 0) return 2;
  if (write_lines("package/include/usb-decrypter.h", header_lines, sizeof(header_lines)/sizeof(header_lines[0]), 0) != 0) return 3;
  if (write_lines("package/src/main.c", main_lines, sizeof(main_lines)/sizeof(main_lines[0]), 0) != 0) return 4;
  if (write_lines("package/src/libsodium_decrypt.c", libsodium_lines, sizeof(libsodium_lines)/sizeof(libsodium_lines[0]), 0) != 0) return 5;
  if (write_lines("package/src/toy_polynomial_codec.c", toy_lines, sizeof(toy_lines)/sizeof(toy_lines[0]), 0) != 0) return 6;
  if (write_lines("package/src/math_example.c", math_example_lines, sizeof(math_example_lines)/sizeof(math_example_lines[0]), 0) != 0) return 7;

  const char *runsh_lines[] = {
  "#!/bin/sh",
        "echo \"Usage: ./bin/usb-decrypter <infile> <outfile> <hex-key-32bytes>\""
    };
  if (write_lines("package/bin/run_decrypt.sh", runsh_lines, sizeof(runsh_lines)/sizeof(runsh_lines[0]), 0755) != 0) return 8;

  printf("package skeleton generated at ./package\n");
  printf("Build: cd package && make\n");
  return 0;
}
```

補足（簡潔）
  - 数学関数 (pow/log) を使うファイルには `#include <math.h>` を追加しています。
- Makefile の LDFLAGS に `-lm` を追加して libm をリンクします。
- 大きなエスケープ文字列を避け、行配列で書き出すためエスケープによるエラーは発生しません。
