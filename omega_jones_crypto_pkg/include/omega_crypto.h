/* include/omega_crypto.h */
#ifndef OMEGA_CRYPTO_H
#define OMEGA_CRYPTO_H

/* Derive 32-byte key from a diagram file (Jones-based derivation) */
int derive_key_from_diagram(const char *diagram_path, unsigned char key_out[32]);

/* AES-256-GCM encrypt/decrypt
   encrypt: returns 0 on success, outputs (iv_len=12) + tag_len=16 and ciphertext
*/
int aes256gcm_encrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len);
int aes256gcm_decrypt_file(const unsigned char key[32], const char *in_path, const char *out_path, const unsigned char *aad, size_t aad_len);

#endif
