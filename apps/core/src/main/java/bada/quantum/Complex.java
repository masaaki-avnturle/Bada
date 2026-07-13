package bada.quantum;

/** Minimal immutable complex number (no external deps) for the Bada telegraph. */
public final class Complex {
    public final double re, im;

    public Complex(double re, double im) { this.re = re; this.im = im; }

    public static Complex of(double re, double im) { return new Complex(re, im); }
    public static Complex real(double re) { return new Complex(re, 0); }

    public Complex add(Complex o) { return new Complex(re + o.re, im + o.im); }
    public Complex sub(Complex o) { return new Complex(re - o.re, im - o.im); }
    public Complex mul(Complex o) {
        return new Complex(re * o.re - im * o.im, re * o.im + im * o.re);
    }
    public Complex scale(double s) { return new Complex(re * s, im * s); }

    public Complex div(Complex o) {
        double d = o.re * o.re + o.im * o.im;
        return new Complex((re * o.re + im * o.im) / d, (im * o.re - re * o.im) / d);
    }

    public double abs() { return Math.hypot(re, im); }
    public double abs2() { return re * re + im * im; }

    /** Integer power (supports negative exponents). */
    public Complex pow(int n) {
        if (n == 0) return new Complex(1, 0);
        Complex base = (n < 0) ? new Complex(1, 0).div(this) : this;
        int k = Math.abs(n);
        Complex acc = new Complex(1, 0);
        for (int i = 0; i < k; i++) acc = acc.mul(base);
        return acc;
    }

    @Override public String toString() {
        return String.format("%+.4f%+.4fi", re, im);
    }
}
