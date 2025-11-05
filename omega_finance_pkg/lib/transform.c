/* lib/transform.c */
#include <math.h>
#include "../include/omega_finance.h"

double zeta_like_transform(double x){
    if(x<=0.0) return 0.0; /* undefined log; treat as 0 */
    double y = x * log(x);
    double s = sinh(y);
    return -s; /* as derived */
}
