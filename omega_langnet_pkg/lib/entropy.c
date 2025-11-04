/* lib/entropy.c */
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/omega_langnet.h"

double compute_entropy_from_text(const char *text){
  if(!text) return 0.0;
  size_t len=strlen(text);
  if(len==0) return 0.0;
  unsigned long counts[256]={0};
  for(size_t i=0;i<len;++i) counts[(unsigned char)text[i]]++;
  double H=0.0;
  for(int i=0;i<256;++i) if(counts[i]){ double p=(double)counts[i]/(double)len; H -= p * log2(p); }
  return H;
}
