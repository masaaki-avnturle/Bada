#include "usb-decrypter.h"
#include <math.h>

double zeta(double s) {
    double sum = 0.0;
    for (int n = 1; n < 1000; n++) {
        sum += 1.0 / pow(n, s);
    }
    return 1.0 / sum;
}

double beta(double p, double q) {
    return zeta(p) * zeta(q) / zeta(p + q);
}

unsigned char* decrypt_data(unsigned char* encrypted_data, size_t data_size, double exchange_rate, double virtual_currency_price) {
    unsigned char* decrypted_data = (unsigned char*)malloc(data_size);

    for (size_t i = 0; i < data_size; i++) {
        double predicted_price = virtual_currency_price * (1.0 + beta(1.0, exchange_rate) / log(exchange_rate));
        if (predicted_price > virtual_currency_price) {
            decrypted_data[i] = encrypted_data[i];
        } else {
            decrypted_data[i] = ~encrypted_data[i];
        }
    }

    return decrypted_data;
}
