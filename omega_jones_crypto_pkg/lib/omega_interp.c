/* lib/omega_interp.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/omega_crypto.h"

extern int derive_key_from_diagram(const char*, unsigned char[32]);
extern int aes256gcm_encrypt_file(const unsigned char[32], const char*, const char*, const unsigned char*, size_t);
extern int aes256gcm_decrypt_file(const unsigned char[32], const char*, const char*, const unsigned char*, size_t);

int omega_interp(const char *script){ if(!script) return -1; char cmd[64], dfile[512], in[512], out[512], aad[512]; int args = sscanf(script, "%63s %511s %511s %511s %511s", cmd, dfile, in, out, aad);
    if(strcmp(cmd, "encrypt")==0 && args>=4){ unsigned char key[32]; if(derive_key_from_diagram(dfile, key)!=0){ printf("key derivation failed\n"); return 2; } const unsigned char *aadptr = (args>=5)?(unsigned char*)aad:NULL; size_t aadlen = (args>=5)?strlen(aad):0; if(aes256gcm_encrypt_file(key, in, out, aadptr, aadlen)==0){ printf("encrypted -> %s\n", out); return 0; } else { printf("encryption failed\n"); return 3; } }
    if(strcmp(cmd, "decrypt")==0 && args>=4){ unsigned char key[32]; if(derive_key_from_diagram(dfile, key)!=0){ printf("key derivation failed\n"); return 2; } const unsigned char *aadptr = (args>=5)?(unsigned char*)aad:NULL; size_t aadlen = (args>=5)?strlen(aad):0; if(aes256gcm_decrypt_file(key, in, out, aadptr, aadlen)==0){ printf("decrypted -> %s\n", out); return 0; } else { printf("decryption failed\n"); return 3; } }
    printf("Usage: encrypt <diagram> <in> <out> [aad]\n       decrypt <diagram> <in> <out> [aad]\n"); return -1; }
