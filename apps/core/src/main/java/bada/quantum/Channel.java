package bada.quantum;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Entanglement-assisted classical channel: superdense coding. Alice applies one
 * of {I,X,Z,ZX} to her half of a Bell pair (2 classical bits), Bob's Bell
 * measurement recovers them. Semiconductor thermal flips corrupt the traveling
 * qubit; a repetition code + majority vote protects the payload. Obeys
 * no-signaling — a legitimate telegraph, not a faster-than-light one.
 */
public final class Channel {
    public static int[] textToBits(String text) {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        int[] bits = new int[bytes.length * 8];
        int idx = 0;
        for (byte bb : bytes) {
            int b = bb & 0xFF;
            for (int i = 7; i >= 0; i--) bits[idx++] = (b >> i) & 1;
        }
        return bits;
    }

    public static String bitsToText(int[] bits) {
        int nBytes = (bits.length + 7) / 8;
        byte[] bytes = new byte[nBytes];
        for (int i = 0; i < nBytes; i++) {
            int v = 0;
            for (int j = 0; j < 8; j++) {
                int pos = i * 8 + j;
                v = (v << 1) | (pos < bits.length ? bits[pos] : 0);
            }
            bytes[i] = (byte) v;
        }
        return new String(bytes, StandardCharsets.UTF_8);
    }

    /** Transmit one 2-bit symbol through a fresh Bell pair, with channel noise. */
    static int[] sendSymbol(int hi, int lo, double flipProb, Random rng) {
        Qubit2 pair = Qubit2.prepareBell();
        pair.encode(hi, lo);
        if (rng.nextDouble() < flipProb) {
            switch (rng.nextInt(3)) {
                case 0 -> pair.xA();
                case 1 -> pair.yA();
                default -> pair.zA();
            }
        }
        pair.bellDecode();
        return pair.readoutBits();
    }

    static int majority(List<Integer> bits) {
        int sum = 0;
        for (int b : bits) sum += b;
        return sum >= (bits.size() / 2.0) ? 1 : 0;
    }

    static int[] sendSymbolProtected(int hi, int lo, double flipProb, Random rng, int redundancy) {
        List<Integer> his = new ArrayList<>(), los = new ArrayList<>();
        for (int r = 0; r < redundancy; r++) {
            int[] out = sendSymbol(hi, lo, flipProb, rng);
            his.add(out[0]);
            los.add(out[1]);
        }
        return new int[]{majority(his), majority(los)};
    }

    public static final class Result {
        public String message, recovered;
        public int bits, pairsUsed, bitErrors;
        public double flipProb, ber, rawFidelity, certifiedFidelity;
        public boolean lossless;
    }

    public static Result transmit(String message, String material, double tempK,
                                  int redundancy, long seed) {
        Random rng = new Random(seed);
        double flip = Math.max(Semiconductor.thermalFlip(material, tempK), 0.04);

        int[] src = textToBits(message);
        if (src.length % 2 != 0) {
            int[] padded = new int[src.length + 1];
            System.arraycopy(src, 0, padded, 0, src.length);
            src = padded;
        }
        int[] recovered = new int[src.length];
        double fidSum = 0;
        int symbols = 0;
        for (int i = 0; i < src.length; i += 2) {
            int hi = src[i], lo = src[i + 1];
            int[] out = sendSymbolProtected(hi, lo, flip, rng, redundancy);
            recovered[i] = out[0];
            recovered[i + 1] = out[1];
            fidSum += ((out[0] == hi ? 1.0 : 0.0) + (out[1] == lo ? 1.0 : 0.0)) / 2.0;
            symbols++;
        }
        int errors = 0;
        boolean lossless = true;
        for (int i = 0; i < src.length; i++) {
            if (src[i] != recovered[i]) { errors++; lossless = false; }
        }
        Result r = new Result();
        r.message = message;
        r.recovered = bitsToText(recovered);
        r.bits = src.length;
        r.pairsUsed = (src.length / 2) * redundancy;
        r.flipProb = flip;
        r.bitErrors = errors;
        r.ber = src.length == 0 ? 0.0 : (double) errors / src.length;
        r.rawFidelity = symbols == 0 ? 1.0 : fidSum / symbols;
        r.certifiedFidelity = r.rawFidelity;
        r.lossless = lossless;
        return r;
    }
}
