// omega_script/include/manifold.h
#ifndef MANIFOLD_H
#define MANIFOLD_H

#include "omega_types.h"

typedef struct Manifold {
  int dimension;
  OmegaArray* points;
} Manifold;

Manifold* Manifold_create(int dimension);
void Manifold_add_point(Manifold* manifold, OmegaType* point);
void Manifold_remove_point(Manifold* manifold, OmegaType* point);
double Manifold_integrate(Manifold* manifold, double (*f)(double));
double Manifold_differentiate(Manifold* manifold, double (*f)(double), OmegaType* point);
void Manifold_plot(Manifold* manifold, double (*f)(double), double a, double b, int n);

#endif // MANIFOLD_H
