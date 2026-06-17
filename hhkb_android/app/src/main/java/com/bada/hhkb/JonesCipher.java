package com.bada.hhkb;

import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * Jones-manifold text encryption for the keyboard's "security guard" feature.
 *
 * <p>The key is derived from the Kauffman bracket of a knot diagram (a trefoil),
 * the same Jones-polynomial construction used by {@code omega_jones_crypto} and
 * grounded in the global-partial-integral / Jones-manifold theory. The bracket
 * is sampled at several values of A, the IEEE-754 samples are hashed with
 * SHA-256 to a 32-byte master key, and text is protected with an
 * encrypt-then-MAC stream cipher (HMAC-SHA256 keystream + HMAC-SHA256 tag).
 *
 * Pure Java standard library — no external dependencies, fully on-device.
 */
final class JonesCipher {

    private JonesCipher() {}

    // Trefoil (3-crossing) diagram: each crossing's four edge labels.
    private static final int[][] CROSSINGS = {
            {1, 2, 3, 4},
            {3, 4, 5, 6},
            {5, 6, 1, 2},
    };
    private static final double[] A_SAMPLES = {0.8, 1.0, 1.2, 1.5, 2.0};

    // -- public API --------------------------------------------------------
    static String encrypt(String plain) {
        try {
            byte[] master = jonesKey();
            byte[] enc = tagged(master, "enc");
            byte[] mk = tagged(master, "mac");
            byte[] nonce = new byte[8];
            new java.security.SecureRandom().nextBytes(nonce);
            byte[] pt = plain.getBytes(StandardCharsets.UTF_8);
            byte[] ks = keystream(enc, nonce, pt.length);
            byte[] ct = xor(pt, ks);
            byte[] mac = hmac(mk, concat(nonce, ct));
            byte[] out = concat(concat(nonce, copy(mac, 8)), ct);
            return Base64.encodeToString(out, Base64.NO_WRAP);
        } catch (Exception e) {
            return null;
        }
    }

    /** Returns the plaintext, or null if the data is not valid / tampered. */
    static String decrypt(String b64) {
        try {
            byte[] in = Base64.decode(b64.trim(), Base64.NO_WRAP);
            if (in.length < 16) return null;
            byte[] master = jonesKey();
            byte[] enc = tagged(master, "enc");
            byte[] mk = tagged(master, "mac");
            byte[] nonce = slice(in, 0, 8);
            byte[] mac = slice(in, 8, 16);
            byte[] ct = slice(in, 16, in.length);
            byte[] expect = copy(hmac(mk, concat(nonce, ct)), 8);
            if (!constantEquals(mac, expect)) return null;
            byte[] pt = xor(ct, keystream(enc, nonce, ct.length));
            return new String(pt, StandardCharsets.UTF_8);
        } catch (Exception e) {
            return null;
        }
    }

    // -- Jones / Kauffman key derivation -----------------------------------
    private static byte[] jonesKey() throws Exception {
        byte[] buf = new byte[5 * 32];          // matches the C tool's layout
        for (int i = 0; i < A_SAMPLES.length; i++) {
            double v = kauffmanBracket(A_SAMPLES[i]);
            long bits = Double.doubleToLongBits(v);
            for (int b = 0; b < 8; b++) buf[i * 8 + b] = (byte) (bits >>> (8 * b)); // little-endian
        }
        return MessageDigest.getInstance("SHA-256").digest(buf);
    }

    private static double kauffmanBracket(double A) {
        int n = CROSSINGS.length;
        int maxlbl = 0;
        for (int[] c : CROSSINGS) for (int e : c) maxlbl = Math.max(maxlbl, e);
        int U = maxlbl + 1;
        double d = -(A * A) - 1.0 / (A * A);
        double total = 0.0;
        for (int s = 0; s < (1 << n); s++) {
            int[] parent = new int[U];
            for (int i = 0; i < U; i++) parent[i] = i;
            int aCnt = 0, bCnt = 0;
            for (int i = 0; i < n; i++) {
                int[] e = CROSSINGS[i];
                if (((s >> i) & 1) == 0) { union(parent, e[0], e[1]); union(parent, e[2], e[3]); aCnt++; }
                else { union(parent, e[1], e[2]); union(parent, e[3], e[0]); bCnt++; }
            }
            boolean[] seen = new boolean[U];
            int loops = 0;
            for (int lbl = 0; lbl < U; lbl++) {
                int r = find(parent, lbl);
                if (!seen[r]) { seen[r] = true; loops++; }
            }
            total += Math.pow(A, aCnt - bCnt) * Math.pow(d, loops > 0 ? loops - 1 : 0);
        }
        return total;
    }

    private static int find(int[] p, int a) { while (p[a] != a) { p[a] = p[p[a]]; a = p[a]; } return a; }
    private static void union(int[] p, int a, int b) { p[find(p, a)] = find(p, b); }

    // -- crypto primitives -------------------------------------------------
    private static byte[] tagged(byte[] key, String tag) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        md.update(key);
        md.update(tag.getBytes(StandardCharsets.US_ASCII));
        return md.digest();
    }

    private static byte[] keystream(byte[] key, byte[] nonce, int n) throws Exception {
        byte[] out = new byte[n];
        int off = 0, ctr = 0;
        while (off < n) {
            byte[] block = hmac(key, concat(nonce, intBytes(ctr)));
            int len = Math.min(block.length, n - off);
            System.arraycopy(block, 0, out, off, len);
            off += len; ctr++;
        }
        return out;
    }

    private static byte[] hmac(byte[] key, byte[] data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(key, "HmacSHA256"));
        return mac.doFinal(data);
    }

    // -- helpers -----------------------------------------------------------
    private static byte[] xor(byte[] a, byte[] b) {
        byte[] o = new byte[a.length];
        for (int i = 0; i < a.length; i++) o[i] = (byte) (a[i] ^ b[i]);
        return o;
    }
    private static byte[] concat(byte[] a, byte[] b) {
        byte[] o = new byte[a.length + b.length];
        System.arraycopy(a, 0, o, 0, a.length);
        System.arraycopy(b, 0, o, a.length, b.length);
        return o;
    }
    private static byte[] copy(byte[] a, int n) { byte[] o = new byte[n]; System.arraycopy(a, 0, o, 0, n); return o; }
    private static byte[] slice(byte[] a, int from, int to) {
        byte[] o = new byte[to - from]; System.arraycopy(a, from, o, 0, to - from); return o;
    }
    private static byte[] intBytes(int v) {
        return new byte[]{(byte) (v >>> 24), (byte) (v >>> 16), (byte) (v >>> 8), (byte) v};
    }
    private static boolean constantEquals(byte[] a, byte[] b) {
        if (a.length != b.length) return false;
        int r = 0;
        for (int i = 0; i < a.length; i++) r |= a[i] ^ b[i];
        return r == 0;
    }
}
