package com.bada.hhkb;

import android.view.inputmethod.InputConnection;

import java.util.HashMap;
import java.util.Map;

/**
 * Minimal, dictionary-free Japanese input engine for the HHKB soft keyboard.
 *
 * <p>It converts typed romaji into hiragana live (shown as composing text), and
 * offers two confirmation behaviours that mirror a real JIS keyboard:
 * <ul>
 *   <li><b>変換 (henkan)</b> — cycles the current reading through candidate forms:
 *       hiragana → katakana → full-width latin → (back to hiragana).
 *       Without a kanji dictionary this is the meaningful, self-contained set of
 *       conversions.</li>
 *   <li><b>無変換 (muhenkan)</b> — commits the reading as-is in hiragana.</li>
 * </ul>
 *
 * The engine never touches the network or storage; it only drives the
 * {@link InputConnection} composing region of whatever field has focus.
 */
final class JapaneseInputEngine {

    private final StringBuilder raw = new StringBuilder();  // pending romaji
    private int candIndex = -1;                             // -1 => showing hiragana
    private static final Map<String, String> M = buildTable();

    boolean isComposing() {
        return raw.length() > 0;
    }

    void reset() {
        raw.setLength(0);
        candIndex = -1;
    }

    /** A letter was typed in Japanese mode. */
    void inputLetter(InputConnection ic, char c) {
        if (candIndex >= 0) {
            // The reading was already converted; confirm it and start anew.
            commit(ic);
        }
        raw.append(Character.toLowerCase(c));
        render(ic);
    }

    private void render(InputConnection ic) {
        candIndex = -1;
        ic.setComposingText(toHiragana(raw.toString()), 1);
    }

    /** 変換: cycle hiragana → katakana → full-width latin. */
    boolean henkan(InputConnection ic) {
        if (raw.length() == 0) return false;
        String[] cands = candidates();
        candIndex = (candIndex + 1) % cands.length;
        ic.setComposingText(cands[candIndex], 1);
        return true;
    }

    /** 無変換: commit the reading as hiragana. */
    boolean muhenkan(InputConnection ic) {
        if (raw.length() == 0) return false;
        ic.setComposingText(toHiragana(raw.toString()), 1);
        commit(ic);
        return true;
    }

    /** Backspace inside a composition. Returns true if it was handled. */
    boolean backspace(InputConnection ic) {
        if (raw.length() == 0) return false;
        if (candIndex >= 0) {            // revert conversion first
            render(ic);
            return true;
        }
        raw.deleteCharAt(raw.length() - 1);
        if (raw.length() == 0) {
            ic.setComposingText("", 1);
            ic.finishComposingText();
        } else {
            render(ic);
        }
        return true;
    }

    /** Confirm whatever is currently composed. */
    void commit(InputConnection ic) {
        ic.finishComposingText();
        raw.setLength(0);
        candIndex = -1;
    }

    void commitIfComposing(InputConnection ic) {
        if (raw.length() > 0) commit(ic);
    }

    private String[] candidates() {
        String hira = toHiragana(raw.toString());
        return new String[]{hira, toKatakana(hira), toFullWidth(raw.toString())};
    }

    // -- conversions -------------------------------------------------------
    static String toHiragana(String s) {
        StringBuilder out = new StringBuilder();
        int i = 0, n = s.length();
        while (i < n) {
            char c = s.charAt(i);
            // small tsu (sokuon): doubled consonant, e.g. "kk" -> っk...
            if (c != 'n' && isConsonant(c) && i + 1 < n && s.charAt(i + 1) == c) {
                out.append('っ');
                i++;
                continue;
            }
            if (c == 'n') {
                if (i + 1 < n && s.charAt(i + 1) == 'n') {
                    // "nn" disambiguation via the char that follows it.
                    if (i + 2 < n && (isVowel(s.charAt(i + 2)) || s.charAt(i + 2) == 'y')) {
                        out.append('ん');   // e.g. "nna" -> んな (consume one n)
                        i++;
                    } else {
                        out.append('ん');   // "nn" before consonant/end -> ん
                        i += 2;
                    }
                    continue;
                }
                if (i + 1 < n && s.charAt(i + 1) == '\'') {  // explicit n'
                    out.append('ん');
                    i += 2;
                    continue;
                }
                if (i + 1 < n) {
                    char nx = s.charAt(i + 1);
                    if (!isVowel(nx) && nx != 'y') {  // n before a consonant
                        out.append('ん');
                        i++;
                        continue;
                    }
                    // otherwise fall through (na, ni, nya, ...)
                } else {
                    out.append('ん');  // lone trailing n (safe: raw is re-converted each key)
                    i++;
                    continue;
                }
            }
            boolean matched = false;
            for (int L = 3; L >= 1; L--) {
                if (i + L <= n) {
                    String kana = M.get(s.substring(i, i + L));
                    if (kana != null) {
                        out.append(kana);
                        i += L;
                        matched = true;
                        break;
                    }
                }
            }
            if (!matched) {
                out.append(c);   // unconvertible (incomplete) romaji: show as-is
                i++;
            }
        }
        return out.toString();
    }

    static String toKatakana(String hira) {
        StringBuilder out = new StringBuilder(hira.length());
        for (int i = 0; i < hira.length(); i++) {
            char c = hira.charAt(i);
            if (c >= 0x3041 && c <= 0x3096) c += 0x60;  // hiragana -> katakana block
            out.append(c);
        }
        return out.toString();
    }

    static String toFullWidth(String ascii) {
        StringBuilder out = new StringBuilder(ascii.length());
        for (int i = 0; i < ascii.length(); i++) {
            char c = ascii.charAt(i);
            if (c == ' ') out.append('　');
            else if (c >= 0x21 && c <= 0x7E) out.append((char) (c + 0xFEE0));
            else out.append(c);
        }
        return out.toString();
    }

    private static boolean isVowel(char c) {
        return c == 'a' || c == 'i' || c == 'u' || c == 'e' || c == 'o';
    }

    private static boolean isConsonant(char c) {
        return c >= 'a' && c <= 'z' && !isVowel(c);
    }

    // -- romaji table ------------------------------------------------------
    private static void p(Map<String, String> m, String k, String v) {
        m.put(k, v);
    }

    private static Map<String, String> buildTable() {
        Map<String, String> m = new HashMap<>();
        p(m, "a", "あ"); p(m, "i", "い"); p(m, "u", "う"); p(m, "e", "え"); p(m, "o", "お");
        p(m, "ka", "か"); p(m, "ki", "き"); p(m, "ku", "く"); p(m, "ke", "け"); p(m, "ko", "こ");
        p(m, "sa", "さ"); p(m, "shi", "し"); p(m, "si", "し"); p(m, "su", "す"); p(m, "se", "せ"); p(m, "so", "そ");
        p(m, "ta", "た"); p(m, "chi", "ち"); p(m, "ti", "ち"); p(m, "tsu", "つ"); p(m, "tu", "つ"); p(m, "te", "て"); p(m, "to", "と");
        p(m, "na", "な"); p(m, "ni", "に"); p(m, "nu", "ぬ"); p(m, "ne", "ね"); p(m, "no", "の");
        p(m, "ha", "は"); p(m, "hi", "ひ"); p(m, "fu", "ふ"); p(m, "hu", "ふ"); p(m, "he", "へ"); p(m, "ho", "ほ");
        p(m, "ma", "ま"); p(m, "mi", "み"); p(m, "mu", "む"); p(m, "me", "め"); p(m, "mo", "も");
        p(m, "ya", "や"); p(m, "yu", "ゆ"); p(m, "yo", "よ");
        p(m, "ra", "ら"); p(m, "ri", "り"); p(m, "ru", "る"); p(m, "re", "れ"); p(m, "ro", "ろ");
        p(m, "wa", "わ"); p(m, "wo", "を");
        p(m, "ga", "が"); p(m, "gi", "ぎ"); p(m, "gu", "ぐ"); p(m, "ge", "げ"); p(m, "go", "ご");
        p(m, "za", "ざ"); p(m, "ji", "じ"); p(m, "zi", "じ"); p(m, "zu", "ず"); p(m, "ze", "ぜ"); p(m, "zo", "ぞ");
        p(m, "da", "だ"); p(m, "di", "ぢ"); p(m, "du", "づ"); p(m, "de", "で"); p(m, "do", "ど");
        p(m, "ba", "ば"); p(m, "bi", "び"); p(m, "bu", "ぶ"); p(m, "be", "べ"); p(m, "bo", "ぼ");
        p(m, "pa", "ぱ"); p(m, "pi", "ぴ"); p(m, "pu", "ぷ"); p(m, "pe", "ぺ"); p(m, "po", "ぽ");
        // youon (拗音)
        p(m, "kya", "きゃ"); p(m, "kyu", "きゅ"); p(m, "kyo", "きょ");
        p(m, "sha", "しゃ"); p(m, "shu", "しゅ"); p(m, "sho", "しょ");
        p(m, "sya", "しゃ"); p(m, "syu", "しゅ"); p(m, "syo", "しょ");
        p(m, "cha", "ちゃ"); p(m, "chu", "ちゅ"); p(m, "cho", "ちょ");
        p(m, "cya", "ちゃ"); p(m, "cyu", "ちゅ"); p(m, "cyo", "ちょ");
        p(m, "nya", "にゃ"); p(m, "nyu", "にゅ"); p(m, "nyo", "にょ");
        p(m, "hya", "ひゃ"); p(m, "hyu", "ひゅ"); p(m, "hyo", "ひょ");
        p(m, "mya", "みゃ"); p(m, "myu", "みゅ"); p(m, "myo", "みょ");
        p(m, "rya", "りゃ"); p(m, "ryu", "りゅ"); p(m, "ryo", "りょ");
        p(m, "gya", "ぎゃ"); p(m, "gyu", "ぎゅ"); p(m, "gyo", "ぎょ");
        p(m, "ja", "じゃ"); p(m, "ju", "じゅ"); p(m, "jo", "じょ");
        p(m, "jya", "じゃ"); p(m, "jyu", "じゅ"); p(m, "jyo", "じょ");
        p(m, "zya", "じゃ"); p(m, "zyu", "じゅ"); p(m, "zyo", "じょ");
        p(m, "bya", "びゃ"); p(m, "byu", "びゅ"); p(m, "byo", "びょ");
        p(m, "pya", "ぴゃ"); p(m, "pyu", "ぴゅ"); p(m, "pyo", "ぴょ");
        // small vowels / common extras
        p(m, "fa", "ふぁ"); p(m, "fi", "ふぃ"); p(m, "fe", "ふぇ"); p(m, "fo", "ふぉ");
        p(m, "-", "ー");
        return m;
    }
}
