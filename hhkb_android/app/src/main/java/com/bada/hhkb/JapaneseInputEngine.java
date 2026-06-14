package com.bada.hhkb;

import android.view.inputmethod.InputConnection;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;

/**
 * Japanese input engine for the HHKB soft keyboard.
 *
 * <p>Pipeline:
 * <ol>
 *   <li><b>Romaji → hiragana</b> live conversion shown as composing text.</li>
 *   <li><b>変換 / Space</b> converts the reading to candidates and cycles through
 *       them: dictionary kanji (from {@code assets/jadict.tsv}) first, then
 *       hiragana, katakana and full-width latin.</li>
 *   <li><b>Enter / tap a candidate</b> confirms; <b>Backspace</b> cancels the
 *       conversion back to the reading; <b>無変換</b> commits as hiragana.</li>
 * </ol>
 *
 * The engine drives the focused field's composing region and notifies a
 * {@link Listener} so the keyboard can render a candidate bar.
 */
final class JapaneseInputEngine {

    /** UI callback for the candidate bar. */
    interface Listener {
        void onCandidates(List<String> candidates, int selected);
        void onHideCandidates();
    }

    private final StringBuilder raw = new StringBuilder();   // pending romaji
    private boolean converting = false;
    private final List<String> cands = new ArrayList<>();
    private int candIndex = -1;

    private Map<String, List<String>> dict = new HashMap<>();
    private Listener listener;
    private boolean preferFullWidth = false;   // 全角(true) / 半角(false) preference

    private static final Map<String, String> M = buildTable();
    private static final Map<Character, String> HALF_KATA = buildHalfKatakana();

    void setDictionary(Map<String, List<String>> d) {
        if (d != null) dict = d;
    }

    void setPreferFullWidth(boolean full) {
        preferFullWidth = full;
    }

    void setListener(Listener l) {
        listener = l;
    }

    boolean isComposing() {
        return raw.length() > 0;
    }

    void reset() {
        raw.setLength(0);
        converting = false;
        candIndex = -1;
        cands.clear();
    }

    // -- typing ------------------------------------------------------------
    void inputLetter(InputConnection ic, char c) {
        if (converting) {
            commit(ic);          // confirm the highlighted candidate, then continue
        }
        raw.append(Character.toLowerCase(c));
        render(ic);
    }

    private void render(InputConnection ic) {
        converting = false;
        candIndex = -1;
        cands.clear();
        ic.setComposingText(toHiragana(raw.toString()), 1);
        hideBar();
    }

    // -- conversion (変換 / Space) -----------------------------------------
    boolean convertNext(InputConnection ic) {
        if (raw.length() == 0) return false;
        if (!converting) {
            buildCandidates();
            converting = true;
            candIndex = 0;
        } else {
            candIndex = (candIndex + 1) % cands.size();
        }
        ic.setComposingText(cands.get(candIndex), 1);
        if (listener != null) listener.onCandidates(cands, candIndex);
        return true;
    }

    private void buildCandidates() {
        cands.clear();
        String hira = toHiragana(raw.toString());
        String kataFull = toKatakana(hira);
        String kataHalf = toHalfWidthKatakana(hira);
        String latinFull = toFullWidth(raw.toString());
        String latinHalf = raw.toString();

        LinkedHashSet<String> set = new LinkedHashSet<>();
        List<String> kanji = dict.get(hira);
        if (kanji != null) set.addAll(kanji);
        set.add(hira);
        // Order the width variants by the current 全角/半角 preference.
        if (preferFullWidth) {
            set.add(kataFull); set.add(latinFull); set.add(kataHalf); set.add(latinHalf);
        } else {
            set.add(kataHalf); set.add(latinHalf); set.add(kataFull); set.add(latinFull);
        }
        cands.addAll(set);
    }

    /** Tapping a candidate in the bar. */
    void selectCandidate(InputConnection ic, int i) {
        if (!converting || i < 0 || i >= cands.size()) return;
        ic.setComposingText(cands.get(i), 1);
        candIndex = i;
        commit(ic);
    }

    // -- 無変換 ------------------------------------------------------------
    boolean muhenkan(InputConnection ic) {
        if (raw.length() == 0) return false;
        ic.setComposingText(toHiragana(raw.toString()), 1);
        commit(ic);
        return true;
    }

    // -- editing -----------------------------------------------------------
    boolean backspace(InputConnection ic) {
        if (raw.length() == 0) return false;
        if (converting) {            // cancel conversion, return to the reading
            converting = false;
            candIndex = -1;
            cands.clear();
            ic.setComposingText(toHiragana(raw.toString()), 1);
            hideBar();
            return true;
        }
        raw.deleteCharAt(raw.length() - 1);
        if (raw.length() == 0) {
            ic.setComposingText("", 1);
            ic.finishComposingText();
            hideBar();
        } else {
            render(ic);
        }
        return true;
    }

    // -- commit ------------------------------------------------------------
    void commit(InputConnection ic) {
        ic.finishComposingText();
        reset();
        hideBar();
    }

    void commitIfComposing(InputConnection ic) {
        if (raw.length() > 0) commit(ic);
    }

    private void hideBar() {
        if (listener != null) listener.onHideCandidates();
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

    /** hiragana -> half-width katakana (ｶﾀｶﾅ), incl. dakuten/handakuten splitting. */
    static String toHalfWidthKatakana(String hira) {
        String full = toKatakana(hira);
        StringBuilder out = new StringBuilder(full.length());
        for (int i = 0; i < full.length(); i++) {
            char c = full.charAt(i);
            String h = HALF_KATA.get(c);
            out.append(h != null ? h : String.valueOf(c));
        }
        return out.toString();
    }

    private static Map<Character, String> buildHalfKatakana() {
        Map<Character, String> m = new HashMap<>();
        String[] pairs = {
            "ア","ｱ","イ","ｲ","ウ","ｳ","エ","ｴ","オ","ｵ",
            "カ","ｶ","キ","ｷ","ク","ｸ","ケ","ｹ","コ","ｺ",
            "サ","ｻ","シ","ｼ","ス","ｽ","セ","ｾ","ソ","ｿ",
            "タ","ﾀ","チ","ﾁ","ツ","ﾂ","テ","ﾃ","ト","ﾄ",
            "ナ","ﾅ","ニ","ﾆ","ヌ","ﾇ","ネ","ﾈ","ノ","ﾉ",
            "ハ","ﾊ","ヒ","ﾋ","フ","ﾌ","ヘ","ﾍ","ホ","ﾎ",
            "マ","ﾏ","ミ","ﾐ","ム","ﾑ","メ","ﾒ","モ","ﾓ",
            "ヤ","ﾔ","ユ","ﾕ","ヨ","ﾖ",
            "ラ","ﾗ","リ","ﾘ","ル","ﾙ","レ","ﾚ","ロ","ﾛ",
            "ワ","ﾜ","ヲ","ｦ","ン","ﾝ",
            "ガ","ｶﾞ","ギ","ｷﾞ","グ","ｸﾞ","ゲ","ｹﾞ","ゴ","ｺﾞ",
            "ザ","ｻﾞ","ジ","ｼﾞ","ズ","ｽﾞ","ゼ","ｾﾞ","ゾ","ｿﾞ",
            "ダ","ﾀﾞ","ヂ","ﾁﾞ","ヅ","ﾂﾞ","デ","ﾃﾞ","ド","ﾄﾞ",
            "バ","ﾊﾞ","ビ","ﾋﾞ","ブ","ﾌﾞ","ベ","ﾍﾞ","ボ","ﾎﾞ",
            "パ","ﾊﾟ","ピ","ﾋﾟ","プ","ﾌﾟ","ペ","ﾍﾟ","ポ","ﾎﾟ",
            "ァ","ｧ","ィ","ｨ","ゥ","ｩ","ェ","ｪ","ォ","ｫ",
            "ッ","ｯ","ャ","ｬ","ュ","ｭ","ョ","ｮ",
            "ヴ","ｳﾞ","ー","ｰ","、","､","。","｡","・","･"
        };
        for (int i = 0; i + 1 < pairs.length; i += 2) {
            m.put(pairs[i].charAt(0), pairs[i + 1]);
        }
        return m;
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
