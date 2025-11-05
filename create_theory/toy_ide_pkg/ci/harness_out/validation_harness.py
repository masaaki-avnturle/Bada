# Experimental validation harness. Replace toy components.
import numpy as np, math
def toy_kernel(x,s): return np.exp(-x*(s+1))
def compute_G(s,xs):
    K=toy_kernel(xs,s)
    Gamma=np.vectorize(lambda a: math.gamma(a))
    return np.trapz(K*Gamma(1.0+0*xs), xs)
if __name__=="__main__":
    xs=np.linspace(0,10,200)
    print([compute_G(s,xs) for s in [0.5,1.0,2.0]])
