#ifndef USB_DECRYPTER_H
#define USB_DECRYPTER_H

#include <stdint.h>

unsigned char* decrypt_data(unsigned char* encrypted_data, size_t data_size, double exchange_rate, double virtual_currency_price);

#endif
