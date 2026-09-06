  /* gen_omega_jones_crypto_pkg.c
   *
   * Generates 'omega_jones_crypto_pkg' with:
   *  - lib/jones_key.c  : Jones numeric eval -> SHA256 -> AES-256 key
   *  - lib/crypto.c     : AES-256-GCM encrypt/decrypt using OpenSSL
   *  - lib/omega_interp.c : minimal Omega interpreter exposing encrypt/decrypt
   *  - include/omega_crypto.h
   *  - bin/launcher.c, bin/run.sh, Makefile, examples/
   *
   * Educational template. Requires OpenSSL (libcrypto).
   */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
# include <direct.h>
# define MKDIR(p) _mkdir(p)
# define PATH_SEP '\\'
#else
# include <sys/stat.h>
# include <unistd.h>
# define MKDIR(p) mkdir((p), 0755)
# define PATH_SEP '/'
#endif

  static int ensure_dir(const char *p){
  int r = MKDIR(p);
  if(r==0) return 0;
  if(errno==EEXIST) return 0;
  return -1;
}
static int write_file(const char *path, const char *data){
  FILE *f = fopen(path, "wb");
  if(!f) return -1;
  size_t n = strlen(data);
  if(fwrite(data,1,n,f) != n){ fclose(f); return -1; }
  fclose(f);
  return 0;
}

int main(void){
  const char *root = "omega_jones_crypto_pkg";
  char path[1024];
  const char *dirs[] = {"bin","lib","include","examples"};
  for(size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(path, sizeof path, "%s%c%s", root, PATH_SEP, dirs[i]);
    if(ensure_dir(path) != 0){ fprintf(stderr, "mkdir failed: %s (%s)\n", path, strerror(errno)); return 1; }
  }

  /* include/omega_crypto.h */
    const char *hdr =
      "/* include/omega_crypto.h */\n#ifndef OMEGA_CRYPTO_H\n#define OMEGA_CRYPTO_H\n\n/* Derive 32-byte key from a diagram file (Jones-based derivation) */\nint derive_key_from_diagram(const char *diagram_path, unsigned char key_out[32]);\n\n/* AES-256-GCM encrypt/decrypt\n   encrypt: returns 0 on success, outputs (iv_len=12) + tag_len=16 and ciphertext\n*/\nint aes256gcm_encrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len);\nint aes256gcm_decrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len);\n\n#endif\n";
    snprintf(path, sizeof path, "%s%cinclude%comega_crypto.h", root, PATH_SEP, PATH_SEP);
    if(write_file(path, hdr) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/jones_key.c
       Minimal Kauffman-bracket numeric evaluator from diagram file (same simple format as before).
       Then hash numeric outputs to produce 32-byte key (SHA-256 via OpenSSL).
    */
    const char *jones_key =
      "/* lib/jones_key.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n#include <openssl/sha.h>\n\ntypedef struct { int id; int e[4]; int sign; } Crossing;\nstatic int load_diagram(const char *path, Crossing **out, int *n){ FILE *f=fopen(path,\"r\"); if(!f) return -1; Crossing *a=NULL; int cap=0,cnt=0; char buf[256]; while(fgets(buf,sizeof buf,f)){ char *s=buf; while(*s==' '||*s=='\\t') s++; if(*s=='#'||*s=='\\n'||*s=='\\0') continue; int id,a0,a1,a2,a3,sg; if(sscanf(s,\"%d %d %d %d %d %d\",&id,&a0,&a1,&a2,&a3,&sg)<6) continue; if(cnt>=cap){ cap=cap?cap*2:16; a=realloc(a,sizeof(Crossing)*cap); } a[cnt].id=id; a[cnt].e[0]=a0; a[cnt].e[1]=a1; a[cnt].e[2]=a2; a[cnt].e[3]=a3; a[cnt].sign=(sg>=0)?1:-1; cnt++; } fclose(f); *out=a; *n=cnt; return 0; }\n\n/* union-find */\ntypedef struct { int p; } UF;\nstatic void uf_init(UF*u,int N){ for(int i=0;i<N;i++) u[i].p=-1; }\nstatic int uf_find(UF*u,int a){ if(u[a].p<0) return a; u[a].p=uf_find(u,u[a].p); return u[a].p; }\nstatic void uf_union(UF*u,int a,int b){ a=uf_find(u,a); b=uf_find(u,b); if(a==b) return; if(u[a].p < u[b].p){ u[a].p += u[b].p; u[b].p = a; } else { u[b].p += u[a].p; u[a].p = b; } }\n\nstatic double compute_kauffman_bracket(Crossing *cross, int n, double A){ if(n==0) return 1.0; unsigned long long states = 1ULL<<n; double sum=0.0; int maxlbl=0; for(int i=0;i<n;i++) for(int k=0;k<4;k++) if(cross[i].e[k]>maxlbl) maxlbl=cross[i].e[k]; int U = maxlbl+1; UF *uf = malloc(sizeof(UF)*(U>0?U:1)); for(unsigned long long s=0;s<states;s++){ uf_init(uf,U); int a_cnt=0,b_cnt=0; for(int i=0;i<n;i++){ int bit=(s>>i)&1ULL; if(bit==0){ uf_union(uf,cross[i].e[0],cross[i].e[1]); uf_union(uf,cross[i].e[2],cross[i].e[3]); a_cnt++; } else { uf_union(uf,cross[i].e[1],cross[i].e[2]); uf_union(uf,cross[i].e[3],cross[i].e[0]); b_cnt++; } }\n    int *seen = calloc(U,sizeof(int)); int loops=0; for(int lbl=0; lbl<U; ++lbl){ int r=uf_find(uf,lbl); if(!seen[r]){ seen[r]=1; loops++; } } free(seen);\n    int exp = a_cnt - b_cnt; double weight = pow(A, exp); double d = -(A*A) - 1.0/(A*A); double loops_factor = pow(d, (loops>0?loops-1:0)); sum += weight * loops_factor; }\n free(uf); return sum; }\n\nint derive_key_from_diagram(const char *diagram_path, unsigned char key_out[32]){\n    Crossing *cs=NULL; int n=0; if(load_diagram(diagram_path,&cs,&n)!=0) return -1;\n    /* Sample: evaluate bracket at several A values, collect numeric results */\n    double samples[5]; double As[5] = {0.8, 1.0, 1.2, 1.5, 2.0}; for(int i=0;i<5;i++) samples[i] = compute_kauffman_bracket(cs, n, As[i]);\n    free(cs);\n    /* serialize doubles into buffer */\n    unsigned char buf[5*32]; memset(buf,0,sizeof(buf)); for(int i=0;i<5;i++){ /* copy IEEE754 bytes */ double v = samples[i]; memcpy(buf + i*8, &v, sizeof(double)); }\n    /* hash to 32 bytes */\n    SHA256(buf, sizeof(buf), key_out);\n    return 0; }\n";
    snprintf(path, sizeof path, "%s%clib%cjones_key.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, jones_key) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/crypto.c - AES-256-GCM encrypt/decrypt file format:
       [12-byte IV][ciphertext][16-byte tag]
       Encrypt reads input file, generates random IV (12 bytes), writes IV || ciphertext || tag to out file.
       Decrypt reads IV (12), ciphertext, tag (last 16 bytes), performs decryption.
    */
    const char *crypto =
      "/* lib/crypto.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <openssl/evp.h>\n#include <openssl/rand.h>\n#include \"../include/omega_crypto.h\"\n\nint aes256gcm_encrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len){ FILE *in=fopen(in_path,\"rb\"); if(!in) return -1; fseek(in,0,SEEK_END); long inlen=ftell(in); fseek(in,0,SEEK_SET); unsigned char *inbuf=malloc(inlen); if(!inbuf){ fclose(in); return -1; } fread(inbuf,1,inlen,in); fclose(in);\n    unsigned char iv[12]; if(RAND_bytes(iv, sizeof(iv))!=1){ free(inbuf); return -1; }\n    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new(); int len; int ciphertext_len; unsigned char *cipher = malloc(inlen + 16);\n    if(!ctx || !cipher){ free(inbuf); if(ctx) EVP_CIPHER_CTX_free(ctx); return -1; }\n    if(1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL)){ free resources:; }\n    if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, sizeof(iv), NULL)) { goto err; }\n    if(1 != EVP_EncryptInit_ex(ctx, NULL, NULL, key, iv)) goto err;\n    if(aad && aad_len){ if(1 != EVP_EncryptUpdate(ctx, NULL, &len, aad, (int)aad_len)) goto err; }\n    if(1 != EVP_EncryptUpdate(ctx, cipher, &len, inbuf, (int)inlen)) goto err; ciphertext_len = len;\n    if(1 != EVP_EncryptFinal_ex(ctx, cipher + len, &len)) goto err; ciphertext_len += len;\n    unsigned char tag[16]; if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag)) goto err;\n    /* write out: IV || ciphertext || tag */\n    FILE *out = fopen(out_path, \"wb\"); if(!out) goto err;\n    fwrite(iv,1,sizeof(iv),out); fwrite(cipher,1,ciphertext_len,out); fwrite(tag,1,16,out); fclose(out);\n    EVP_CIPHER_CTX_free(ctx); free(inbuf); free(cipher); return 0;\nerr:\n    EVP_CIPHER_CTX_free(ctx); free(inbuf); free(cipher); return -1;\n}\n\nint aes256gcm_decrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len){ FILE *in = fopen(in_path,\"rb\"); if(!in) return -1; fseek(in,0,SEEK_END); long sz=ftell(in); if(sz< (12+16)){ fclose(in); return -1; } fseek(in,0,SEEK_SET);\n    unsigned char iv[12]; fread(iv,1,12,in); long ciph_len = sz - 12 - 16; unsigned char *cipher = malloc(ciph_len); if(!cipher){ fclose(in); return -1; } fread(cipher,1,ciph_len,in); unsigned char tag[16]; fread(tag,1,16,in); fclose(in);\n    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new(); if(!ctx){ free(cipher); return -1; }\n    unsigned char *outbuf = malloc(ciph_len);\n    int len; int outlen;\n    if(1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL)) goto derr;\n    if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, sizeof(iv), NULL)) goto derr;\n    if(1 != EVP_DecryptInit_ex(ctx, NULL, NULL, key, iv)) goto derr;\n    if(aad && aad_len){ if(1 != EVP_DecryptUpdate(ctx, NULL, &len, aad, (int)aad_len)) goto derr; }\n    if(1 != EVP_DecryptUpdate(ctx, outbuf, &len, cipher, (int)ciph_len)) goto derr; outlen = len;\n    if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, tag)) goto derr;\n    if(1 != EVP_DecryptFinal_ex(ctx, outbuf + len, &len)) goto derr; outlen += len;\n    FILE *out = fopen(out_path, \"wb\"); if(!out) goto derr; fwrite(outbuf,1,outlen,out); fclose(out);\n    EVP_CIPHER_CTX_free(ctx); free(cipher); free(outbuf); return 0;\nderr:\n    EVP_CIPHER_CTX_free(ctx); free(cipher); if(outbuf) free(outbuf); return -1;\n}\n";
    snprintf(path, sizeof path, "%s%clib%ccrypto.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, crypto) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/omega_interp.c : interpreter that exposes encrypt/decrypt commands */
    const char *interp =
      "/* lib/omega_interp.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_crypto.h\"\n\nextern int derive_key_from_diagram(const char*, unsigned char[32]);\nextern int aes256gcm_encrypt_file(const unsigned char[32], const char*, const char*, const unsigned char*, size_t);\nextern int aes256gcm_decrypt_file(const unsigned char[32], const char*, const char*, const unsigned char*, size_t);\n\nint omega_interp(const char *script){ if(!script) return -1; char cmd[64], dfile[512], in[512], out[512], aad[512]; int args = sscanf(script, \"%63s %511s %511s %511s %511s\", cmd, dfile, in, out, aad);\n    if(strcmp(cmd, \"encrypt\")==0 && args>=4){ unsigned char key[32]; if(derive_key_from_diagram(dfile, key)!=0){ printf(\"key derivation failed\\n\"); return 2; } const unsigned char *aadptr = (args>=5)?(unsigned char*)aad:NULL; size_t aadlen = (args>=5)?strlen(aad):0; if(aes256gcm_encrypt_file(key, in, out, aadptr, aadlen)==0){ printf(\"encrypted -> %s\\n\", out); return 0; } else { printf(\"encryption failed\\n\"); return 3; } }\n    if(strcmp(cmd, \"decrypt\")==0 && args>=4){ unsigned char key[32]; if(derive_key_from_diagram(dfile, key)!=0){ printf(\"key derivation failed\\n\"); return 2; } const unsigned char *aadptr = (args>=5)?(unsigned char*)aad:NULL; size_t aadlen = (args>=5)?strlen(aad):0; if(aes256gcm_decrypt_file(key, in, out, aadptr, aadlen)==0){ printf(\"decrypted -> %s\\n\", out); return 0; } else { printf(\"decryption failed\\n\"); return 3; } }\n    printf(\"Usage: encrypt <diagram> <in> <out> [aad]\\n       decrypt <diagram> <in> <out> [aad]\\n\"); return -1; }\n";
    snprintf(path, sizeof path, "%s%clib%comega_interp.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, interp) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/launcher.c */
    const char *launcher =
      "#include <stdio.h>\n#include <stdlib.h>\nint omega_interp(const char*);\nint main(int argc, char **argv){ if(argc<2){ fprintf(stderr, \"Usage: %s <script...>\\nExample: %s \\\"encrypt examples/trefoil.txt secret.txt secret.enc\\\"\\n\", argv[0], argv[0]); return 1; } char script[1024]; script[0]=0; for(int i=1;i<argc;i++){ if(i>1) strcat(script, \" \"); strcat(script, argv[i]); } return omega_interp(script); }\n";
    snprintf(path, sizeof path, "%s%cbin%clauncher.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, launcher) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* examples/trefoil.txt (sample 3-crossing) */
    const char *example =
      "# sample 3-crossing diagram\n0 1 2 3 4 1\n1 3 4 5 6 1\n2 5 6 1 2 1\n";
    snprintf(path, sizeof path, "%s%cexamples%ctrefoil.txt", root, PATH_SEP, PATH_SEP);
    if(write_file(path, example) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* Makefile */
    const char *makefile =
      "CC=gcc\nCFLAGS=-O2 -Iinclude\nLDFLAGS=-lcrypto -lm\n\nall: bin/launcher\n\nlib: lib/jones_key.c lib/crypto.c lib/omega_interp.c\n\t$(CC) $(CFLAGS) -c lib/jones_key.c lib/crypto.c lib/omega_interp.c\n\t$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c lib/jones_key.o lib/crypto.o lib/omega_interp.o $(LDFLAGS)\n\nbin/launcher: bin/launcher.c lib/jones_key.c lib/crypto.c lib/omega_interp.c\n\t$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c lib/jones_key.c lib/crypto.c lib/omega_interp.c $(LDFLAGS)\n\nclean:\n\trm -f lib/*.o bin/launcher\n";
    snprintf(path, sizeof path, "%s%cMakefile", root, PATH_SEP);
    if(write_file(path, makefile) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* run.sh */
    const char *runsh =
      "#!/bin/sh\nset -e\nROOT=$(cd \"$(dirname \"$0\")/..\" && pwd)\ncd \"$ROOT\"\nmake\necho \"Example: encrypt examples/trefoil.txt plain.txt cipher.bin\"\n";
    snprintf(path, sizeof path, "%s%cbin%crun.sh", root, PATH_SEP, PATH_SEP);
    if(write_file(path, runsh) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }
#if !defined(_WIN32) && !defined(_WIN64)
    chmod(path, 0755);
#endif

    printf("Package '%s' created.\n", root);
    printf("Build & example:\n  cd %s\n  make\n  ./bin/launcher encrypt examples/trefoil.txt plain.txt secret.enc\n  ./bin/launcher decrypt examples/trefoil.txt secret.enc recovered.txt\n\n", root);
    return 0;
}
