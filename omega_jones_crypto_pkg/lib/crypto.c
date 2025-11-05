/* lib/crypto.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
#include "../include/omega_crypto.h"

int aes256gcm_encrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len){ FILE *in=fopen(in_path,"rb"); if(!in) return -1; fseek(in,0,SEEK_END); long inlen=ftell(in); fseek(in,0,SEEK_SET); unsigned char *inbuf=malloc(inlen); if(!inbuf){ fclose(in); return -1; } fread(inbuf,1,inlen,in); fclose(in);
    unsigned char iv[12]; if(RAND_bytes(iv, sizeof(iv))!=1){ free(inbuf); return -1; }
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new(); int len; int ciphertext_len; unsigned char *cipher = malloc(inlen + 16);
    if(!ctx || !cipher){ free(inbuf); if(ctx) EVP_CIPHER_CTX_free(ctx); return -1; }
    if(1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL)){ free; resources:; }
    if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, sizeof(iv), NULL)) { goto err; }
    if(1 != EVP_EncryptInit_ex(ctx, NULL, NULL, key, iv)) goto err;
    if(aad && aad_len){ if(1 != EVP_EncryptUpdate(ctx, NULL, &len, aad, (int)aad_len)) goto err; }
    if(1 != EVP_EncryptUpdate(ctx, cipher, &len, inbuf, (int)inlen)) goto err; ciphertext_len = len;
    if(1 != EVP_EncryptFinal_ex(ctx, cipher + len, &len)) goto err; ciphertext_len += len;
    unsigned char tag[16]; if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag)) goto err;
    /* write out: IV || ciphertext || tag */
    FILE *out = fopen(out_path, "wb"); if(!out) goto err;
    fwrite(iv,1,sizeof(iv),out); fwrite(cipher,1,ciphertext_len,out); fwrite(tag,1,16,out); fclose(out);
    EVP_CIPHER_CTX_free(ctx); free(inbuf); free(cipher); return 0;
err:
    EVP_CIPHER_CTX_free(ctx); free(inbuf); free(cipher); return -1;
}

int aes256gcm_decrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len){ FILE *in = fopen(in_path,"rb"); if(!in) return -1; fseek(in,0,SEEK_END); long sz=ftell(in); if(sz< (12+16)){ fclose(in); return -1; } fseek(in,0,SEEK_SET);
    unsigned char iv[12]; fread(iv,1,12,in); long ciph_len = sz - 12 - 16; unsigned char *cipher = malloc(ciph_len); if(!cipher){ fclose(in); return -1; } fread(cipher,1,ciph_len,in); unsigned char tag[16]; fread(tag,1,16,in); fclose(in);
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new(); if(!ctx){ free(cipher); return -1; }
    unsigned char *outbuf = malloc(ciph_len);
    int len; int outlen;
    if(1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), NULL, NULL, NULL)) goto derr;
    if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, sizeof(iv), NULL)) goto derr;
    if(1 != EVP_DecryptInit_ex(ctx, NULL, NULL, key, iv)) goto derr;
    if(aad && aad_len){ if(1 != EVP_DecryptUpdate(ctx, NULL, &len, aad, (int)aad_len)) goto derr; }
    if(1 != EVP_DecryptUpdate(ctx, outbuf, &len, cipher, (int)ciph_len)) goto derr; outlen = len;
    if(1 != EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, tag)) goto derr;
    if(1 != EVP_DecryptFinal_ex(ctx, outbuf + len, &len)) goto derr; outlen += len;
    FILE *out = fopen(out_path, "wb"); if(!out) goto derr; fwrite(outbuf,1,outlen,out); fclose(out);
    EVP_CIPHER_CTX_free(ctx); free(cipher); free(outbuf); return 0;
derr:
    EVP_CIPHER_CTX_free(ctx); free(cipher); if(outbuf) free(outbuf); return -1;
}
