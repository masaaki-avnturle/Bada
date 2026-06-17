package com.bada.hhkb;

import android.util.JsonReader;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.BufferedReader;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Downloads and queries two FREE, openly-licensed dictionaries from the web:
 *
 * <ul>
 *   <li><b>Kanji (漢字)</b> — KANJIDIC2-derived data (readings, meanings, strokes).
 *       Substitutes for the commercial 漢語林, which is not freely distributable.
 *       Source: davidluzgouveia/kanji-data (CC, KANJIDIC2 © EDRDG).</li>
 *   <li><b>English–English (英英)</b> — Webster's 1913 (public domain / GCIDE).
 *       Source: adambom/dictionary.</li>
 * </ul>
 *
 * Both are fetched once over HTTPS from raw.githubusercontent.com to the app's
 * private files dir, then queried by streaming ({@link JsonReader}) so the full
 * multi-MB files never need to live in memory at once.
 */
final class DictionaryRepository {

    static final String KANJI_URL =
            "https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji.json";
    static final String EN_URL =
            "https://raw.githubusercontent.com/adambom/dictionary/master/dictionary.json";
    /** SKK dictionary (reading→kanji candidates), GPL, EUC-JP — the free converter. */
    static final String SKK_URL =
            "https://raw.githubusercontent.com/skk-dev/dict/master/SKK-JISYO.ML";

    private final File kanjiFile;
    private final File enFile;
    private final File skkFile;
    private volatile boolean downloading = false;

    /** Simple error callback (avoids java.util.function.Consumer so minSdk can be 21). */
    interface ErrCallback {
        void onError(String message);
    }

    DictionaryRepository(File filesDir) {
        kanjiFile = new File(filesDir, "kanji.json");
        enFile = new File(filesDir, "dictionary_en.json");
        skkFile = new File(filesDir, "skk_conv.euc");
    }

    boolean isReady() {
        return kanjiFile.length() > 1024 && enFile.length() > 1024;
    }

    boolean isDownloading() {
        return downloading;
    }

    /** Download both dictionaries on a background thread; runs onDone on completion. */
    void ensureDownloaded(final Runnable onDone, final ErrCallback onError) {
        if (isReady() || downloading) return;
        downloading = true;
        new Thread(() -> {
            try {
                if (kanjiFile.length() <= 1024) download(KANJI_URL, kanjiFile);
                if (enFile.length() <= 1024) download(EN_URL, enFile);
                downloading = false;
                if (onDone != null) onDone.run();
            } catch (Exception e) {
                downloading = false;
                if (onError != null) onError.onError(String.valueOf(e.getMessage()));
            }
        }, "dict-download").start();
    }

    private void download(String urlStr, File dest) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) new URL(urlStr).openConnection();
        conn.setConnectTimeout(20000);
        conn.setReadTimeout(60000);
        conn.setInstanceFollowRedirects(true);
        conn.connect();
        if (conn.getResponseCode() / 100 != 2) {
            throw new RuntimeException("HTTP " + conn.getResponseCode());
        }
        File tmp = new File(dest.getParentFile(), dest.getName() + ".part");
        try (InputStream in = new BufferedInputStream(conn.getInputStream());
             OutputStream out = new FileOutputStream(tmp)) {
            byte[] buf = new byte[16384];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
        } finally {
            conn.disconnect();
        }
        if (!tmp.renameTo(dest)) throw new RuntimeException("save failed");
    }

    // -- lookups (streaming) ----------------------------------------------

    /** Look up a single kanji character; returns a formatted line or null. */
    String lookupKanji(String ch) {
        if (!kanjiFile.exists()) return null;
        try (JsonReader r = new JsonReader(new InputStreamReader(
                new FileInputStream(kanjiFile), StandardCharsets.UTF_8))) {
            r.beginObject();
            while (r.hasNext()) {
                String name = r.nextName();
                if (name.equals(ch)) {
                    return formatKanji(ch, r);
                }
                r.skipValue();
            }
        } catch (Exception ignored) { }
        return null;
    }

    private String formatKanji(String ch, JsonReader r) throws Exception {
        int strokes = 0;
        StringBuilder meanings = new StringBuilder();
        StringBuilder on = new StringBuilder();
        StringBuilder kun = new StringBuilder();
        r.beginObject();
        while (r.hasNext()) {
            String f = r.nextName();
            switch (f) {
                case "strokes": strokes = r.nextInt(); break;
                case "meanings": readArray(r, meanings); break;
                case "readings_on": readArray(r, on); break;
                case "readings_kun": readArray(r, kun); break;
                default: r.skipValue();
            }
        }
        r.endObject();
        return ch + "  [" + strokes + "画]\n"
                + "  意味: " + (meanings.length() > 0 ? meanings : "—") + "\n"
                + "  音: " + (on.length() > 0 ? on : "—")
                + "   訓: " + (kun.length() > 0 ? kun : "—");
    }

    private void readArray(JsonReader r, StringBuilder out) throws Exception {
        r.beginArray();
        boolean first = true;
        while (r.hasNext()) {
            if (!first) out.append("、");
            out.append(r.nextString());
            first = false;
        }
        r.endArray();
    }

    /** Look up an English word (case-insensitive); returns its definition or null. */
    String lookupEnglish(String word) {
        if (!enFile.exists()) return null;
        try (JsonReader r = new JsonReader(new InputStreamReader(
                new FileInputStream(enFile), StandardCharsets.UTF_8))) {
            r.beginObject();
            while (r.hasNext()) {
                String name = r.nextName();
                if (name.equalsIgnoreCase(word)) {
                    return r.nextString();
                }
                r.skipValue();
            }
        } catch (Exception ignored) { }
        return null;
    }

    // =====================================================================
    //  SKK conversion dictionary (reading → kanji candidates)
    // =====================================================================
    boolean isConvReady() {
        return skkFile.length() > 1024;
    }

    /** Download the SKK dictionary if not present (call on a background thread). */
    void downloadConvIfNeeded() throws Exception {
        if (skkFile.length() <= 1024) download(SKK_URL, skkFile);
    }

    /**
     * Parse the SKK dictionary into a reading→candidates map (okuri-nasi entries
     * with pure-hiragana readings). EUC-JP encoded. Returns an empty map if absent.
     */
    Map<String, List<String>> loadConvDictionary() {
        Map<String, List<String>> m = new HashMap<>();
        if (!skkFile.exists()) return m;
        try (BufferedReader r = new BufferedReader(new InputStreamReader(
                new FileInputStream(skkFile), Charset.forName("EUC-JP")))) {
            String line;
            while ((line = r.readLine()) != null) {
                if (line.isEmpty() || line.charAt(0) == ';') continue;
                int sp = line.indexOf(' ');
                if (sp <= 0) continue;
                String reading = line.substring(0, sp);
                if (!isHiragana(reading)) continue;        // skip okuri-ari / latin
                List<String> cands = new ArrayList<>();
                for (String part : line.substring(sp + 1).split("/")) {
                    if (part.isEmpty()) continue;
                    int semi = part.indexOf(';');           // drop ;annotation
                    String cand = semi >= 0 ? part.substring(0, semi) : part;
                    if (!cand.isEmpty()) cands.add(cand);
                    if (cands.size() >= 12) break;
                }
                if (!cands.isEmpty()) m.put(reading, cands);
            }
        } catch (Exception ignored) { }
        return m;
    }

    private static boolean isHiragana(String s) {
        if (s.isEmpty()) return false;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!((c >= 0x3041 && c <= 0x3096) || c == 0x30FC)) return false;
        }
        return true;
    }
}
