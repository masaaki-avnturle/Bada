package bada.qc;

import bada.quantum.Complex;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.io.UncheckedIOException;

/**
 * DiskMemory — the pseudo quantum computer's disk-backed (HDD) von-Neumann
 * memory. Program and the quantum state vector share one flat array of 64-bit
 * words stored in a real file, so every gate genuinely seeks/reads/writes the
 * disk. Java port of Bada::QC::DiskMemory.
 */
public final class DiskMemory implements AutoCloseable {
    public static final int WORD = 8; // bytes per double

    private final RandomAccessFile file;
    private final long words;

    public DiskMemory(String path, long words) {
        this.words = words;
        try {
            file = new RandomAccessFile(path, "rw");
            file.setLength(words * WORD);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public void write(long index, double value) {
        if (index < 0 || index >= words) throw new IndexOutOfBoundsException("addr " + index);
        try {
            file.seek(index * WORD);
            file.writeDouble(value);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public double read(long index) {
        if (index < 0 || index >= words) throw new IndexOutOfBoundsException("addr " + index);
        try {
            file.seek(index * WORD);
            return file.readDouble();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public void writeAmp(long base, long i, Complex c) {
        write(base + 2 * i, c.re);
        write(base + 2 * i + 1, c.im);
    }

    public Complex readAmp(long base, long i) {
        return new Complex(read(base + 2 * i), read(base + 2 * i + 1));
    }

    public long byteSize() {
        return words * WORD;
    }

    public void flush() {
        try {
            file.getFD().sync();
        } catch (IOException ignored) {
            // best-effort flush; not fatal for the simulation
        }
    }

    @Override
    public void close() {
        try {
            file.close();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
