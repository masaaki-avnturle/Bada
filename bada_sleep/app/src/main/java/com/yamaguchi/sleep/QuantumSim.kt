package com.yamaguchi.sleep

import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * A small but genuine quantum state-vector simulator (runs on the classical CPU).
 *
 * It holds the full wave function |ψ⟩ of [n] qubits as 2^n complex amplitudes
 * (re/im arrays) and applies real quantum gates. The sleep app time-evolves the
 * state and reads observables from it (probabilities = |amplitude|²) to drive a
 * smooth, slowing breathing rhythm.
 *
 * This is a classical simulation of a quantum system — not quantum hardware.
 */
class QuantumSim(val n: Int) {
    val size = 1 shl n
    val re = DoubleArray(size)
    val im = DoubleArray(size)

    init { reset() }

    fun reset() {
        for (i in 0 until size) { re[i] = 0.0; im[i] = 0.0 }
        re[0] = 1.0   // |00…0⟩
    }

    /** Apply a single-qubit 2x2 complex gate [[a,b],[c,d]] to qubit [q]. */
    fun apply1(
        q: Int,
        aRe: Double, aIm: Double, bRe: Double, bIm: Double,
        cRe: Double, cIm: Double, dRe: Double, dIm: Double
    ) {
        val bit = 1 shl q
        var i = 0
        while (i < size) {
            if (i and bit == 0) {
                val j = i or bit
                val x0r = re[i]; val x0i = im[i]
                val x1r = re[j]; val x1i = im[j]
                // new0 = a*x0 + b*x1
                re[i] = aRe * x0r - aIm * x0i + bRe * x1r - bIm * x1i
                im[i] = aRe * x0i + aIm * x0r + bRe * x1i + bIm * x1r
                // new1 = c*x0 + d*x1
                re[j] = cRe * x0r - cIm * x0i + dRe * x1r - dIm * x1i
                im[j] = cRe * x0i + cIm * x0r + dRe * x1i + dIm * x1r
            }
            i++
        }
    }

    fun hadamard(q: Int) {
        val s = 1.0 / sqrt(2.0)
        apply1(q, s, 0.0, s, 0.0, s, 0.0, -s, 0.0)
    }

    /** RX(θ) = [[cos, -i·sin],[-i·sin, cos]] (θ/2 inside). */
    fun rx(q: Int, theta: Double) {
        val c = cos(theta / 2); val s = sin(theta / 2)
        apply1(q, c, 0.0, 0.0, -s, 0.0, -s, c, 0.0)
    }

    /** RZ(θ) = [[e^{-iθ/2},0],[0,e^{iθ/2}]]. */
    fun rz(q: Int, theta: Double) {
        val c = cos(theta / 2); val s = sin(theta / 2)
        apply1(q, c, -s, 0.0, 0.0, 0.0, 0.0, c, s)
    }

    /** Controlled-Z between qubits [a] and [b] (entangling). */
    fun cz(a: Int, b: Int) {
        val ba = 1 shl a; val bb = 1 shl b
        var i = 0
        while (i < size) {
            if ((i and ba) != 0 && (i and bb) != 0) { re[i] = -re[i]; im[i] = -im[i] }
            i++
        }
    }

    /** Probability that qubit [q] measures |1⟩. */
    fun probOne(q: Int): Double {
        val bit = 1 shl q
        var p = 0.0
        var i = 0
        while (i < size) {
            if (i and bit != 0) p += re[i] * re[i] + im[i] * im[i]
            i++
        }
        return p
    }

    /** |amplitude| of basis state [i]. */
    fun magnitude(i: Int): Double = sqrt(re[i] * re[i] + im[i] * im[i])

    /** Guard against slow numerical drift from many gate applications. */
    fun renormalize() {
        var s = 0.0
        for (k in 0 until size) s += re[k] * re[k] + im[k] * im[k]
        if (s > 0.0) {
            val f = 1.0 / sqrt(s)
            for (k in 0 until size) { re[k] *= f; im[k] *= f }
        }
    }
}
