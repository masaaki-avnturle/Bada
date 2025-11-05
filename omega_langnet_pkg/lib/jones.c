/* lib/jones.c - prototype Jones polynomial numeric evaluator */
#include <stdlib.h>
#include <string.h>
#include "../include/omega_langnet.h"

static void complex_mul(double ax,double ay,double bx,double by,double *rx,double *ry){*rx=ax*bx-ay*by;*ry=ax*by+ay*bx;}

jones_poly_t *jones_create(int degree){
  if (degree<0) return NULL;
  jones_poly_t *p = (jones_poly_t*)malloc(sizeof(jones_poly_t));
  if(!p) return NULL;
  p->degree=degree;
  p->coeffs=(double*)calloc(degree+1,sizeof(double));
  if(!p->coeffs){free(p);return NULL;}
  return p;
}
void jones_free(jones_poly_t *p){ if(!p) return; free(p->coeffs); free(p); }

double jones_eval_real(const jones_poly_t *p,double x,double y){
  if(!p||!p->coeffs) return 0.0;
  double rx=0.0, ry=0.0;
  double zx=1.0, zy=0.0;
  for(int k=0;k<=p->degree;++k){
    rx += p->coeffs[k]*zx; ry += p->coeffs[k]*zy;
    double nx,ny; complex_mul(zx,zy,x,y,&nx,&ny); zx=nx; zy=ny;
  }
  (void)ry; return rx;
}
