package com.bada.hhkb;

import android.graphics.drawable.GradientDrawable;
import android.inputmethodservice.InputMethodService;
import android.os.SystemClock;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.InputConnection;
import android.widget.Button;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Bada HHKB Pro — a Happy Hacking Keyboard Pro style soft keyboard for Android 12.
 *
 * <p>Highlights:
 * <ul>
 *   <li>Faithful HHKB Pro (US) layout: Esc, Tab, Control, Shift, Alt, Meta(&#9670;),
 *       Fn, Return, Delete and the full Fn layer (arrows, F1&ndash;F12,
 *       Home/End, PgUp/PgDn, Insert, CapsLock, forward-delete).</li>
 *   <li>Sticky modifiers: one tap = apply to the next key only, second tap = lock,
 *       third tap = release.</li>
 *   <li>The whole keyboard floats and can be dragged anywhere on screen via the
 *       handle bar; the [Dock] button snaps it back to the bottom centre.</li>
 * </ul>
 */
public class HhkbImeService extends InputMethodService
        implements JapaneseInputEngine.Listener {

    // ---- key types -------------------------------------------------------
    private static final int T_CHAR = 0;   // printable: types label/shift, or keyCode when modified
    private static final int T_MOD  = 1;   // modifier: Shift/Ctrl/Alt/Meta
    private static final int T_FN   = 2;   // the Fn key
    private static final int T_FUNC = 3;   // special function key (Esc/Tab/Enter/Space/Delete/...)
    private static final int T_JP   = 4;   // Japanese key (変換 / 無変換)
    private static final int T_MODE = 5;   // Japanese/English (あ/A) toggle
    private static final int T_WIDTH = 6;  // full-width / half-width (全/半) toggle

    // ---- Japanese key actions / input modes ------------------------------
    private static final int JP_HENKAN   = 1;   // 変換
    private static final int JP_MUHENKAN = 2;   // 無変換
    private static final int MODE_EN   = 0;
    private static final int MODE_KANA = 1;

    // ---- modifier ids ----------------------------------------------------
    private static final int MOD_SHIFT = 0;
    private static final int MOD_CTRL  = 1;
    private static final int MOD_ALT   = 2;
    private static final int MOD_META  = 3;

    // ---- sticky states ---------------------------------------------------
    private static final int OFF = 0, ONESHOT = 1, LOCK = 2;

    // ---- colours ---------------------------------------------------------
    private static final int COL_BG       = 0xFF1B1F24;
    private static final int COL_KEY      = 0xFF2C323A;
    private static final int COL_KEY_TXT  = 0xFFE8E8E8;
    private static final int COL_SPECIAL  = 0xFF3A3026;
    private static final int COL_GOLD     = 0xFFC8A44A;
    private static final int COL_ONESHOT  = 0xFF6E5A22;
    private static final int COL_LOCK     = 0xFFC8A44A;
    private static final int COL_LOCK_TXT = 0xFF1B1F24;

    private final int[] modState = new int[]{OFF, OFF, OFF, OFF};
    private int fnState = OFF;

    private final Map<Integer, List<Button>> modButtons = new HashMap<>();
    private Button fnButton;

    // ---- Japanese input --------------------------------------------------
    private final JapaneseInputEngine jp = new JapaneseInputEngine();
    private int inputMode = MODE_EN;
    private boolean fullWidth = false;        // 全角(true) / 半角(false)
    private Button modeButton;
    private Button widthButton;
    private HorizontalScrollView candidateScroll;
    private LinearLayout candidateBar;

    // ---- holographic mode + dictionary -----------------------------------
    private boolean holo = false;
    private LinearLayout root;
    private LinearLayout keysContainer;
    private android.widget.ScrollView dictScroll;
    private TextView dictView;
    private DictionaryRepository dictRepo;
    private final android.os.Handler mainHandler =
            new android.os.Handler(android.os.Looper.getMainLooper());

    // ---- floating window state ------------------------------------------
    private View rootView;
    private boolean floating = false;
    private int winX = 0, winY = 0;
    private int keyboardWidthPx = 0;
    private int screenW = 0, screenH = 0;

    @Override
    public void onCreate() {
        super.onCreate();
        jp.setDictionary(loadDictionary());
        jp.setListener(this);
        dictRepo = new DictionaryRepository(getFilesDir());
    }

    /** Load the bundled reading→kanji dictionary from assets/jadict.tsv. */
    private Map<String, List<String>> loadDictionary() {
        Map<String, List<String>> dict = new HashMap<>();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(
                getAssets().open("jadict.tsv"), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) {
                if (line.isEmpty() || line.charAt(0) == '#') continue;
                int tab = line.indexOf('\t');
                if (tab <= 0) continue;
                String reading = line.substring(0, tab).trim();
                String[] words = line.substring(tab + 1).trim().split(",");
                if (reading.isEmpty() || words.length == 0) continue;
                dict.put(reading, new ArrayList<>(Arrays.asList(words)));
            }
        } catch (Exception ignored) {
            // No dictionary => kanji conversion simply offers no kanji candidates.
        }
        return dict;
    }

    // =====================================================================
    //  Key definition
    // =====================================================================
    private static final class KeyDef {
        final String label;
        final String shift;
        final int keyCode;
        final int type;
        final float weight;
        int modId = -1;
        int fnKeyCode = 0;   // when Fn is active and != 0, send this instead
        int jpAction = 0;    // JP_HENKAN / JP_MUHENKAN for T_JP keys

        KeyDef(String label, String shift, int keyCode, int type, float weight) {
            this.label = label;
            this.shift = shift;
            this.keyCode = keyCode;
            this.type = type;
            this.weight = weight;
        }

        KeyDef fn(int code) { this.fnKeyCode = code; return this; }
        KeyDef mod(int id) { this.modId = id; return this; }
    }

    // ---- key factory helpers --------------------------------------------
    private static KeyDef c(String label, String shift, int keyCode) {
        return new KeyDef(label, shift, keyCode, T_CHAR, 1f);
    }
    private static KeyDef func(String label, int keyCode, float w) {
        return new KeyDef(label, label, keyCode, T_FUNC, w);
    }
    private static KeyDef mod(String label, int modId, float w) {
        return new KeyDef(label, label, 0, T_MOD, w).mod(modId);
    }
    private static KeyDef jpKey(String label, int action, float w) {
        int code = (action == JP_HENKAN) ? KeyEvent.KEYCODE_HENKAN : KeyEvent.KEYCODE_MUHENKAN;
        KeyDef k = new KeyDef(label, label, code, T_JP, w);
        k.jpAction = action;
        return k;
    }
    private static KeyDef modeKey(float w) {
        return new KeyDef("A", "A", 0, T_MODE, w);
    }
    private static KeyDef widthKey(float w) {
        return new KeyDef("半", "半", 0, T_WIDTH, w);
    }

    // =====================================================================
    //  HHKB Pro (US) layout
    // =====================================================================
    private List<List<KeyDef>> buildLayout() {
        List<List<KeyDef>> rows = new ArrayList<>();

        // Row 1: Esc 1..0 - = \ `
        List<KeyDef> r1 = new ArrayList<>();
        r1.add(func("Esc", KeyEvent.KEYCODE_ESCAPE, 1f));
        addDigits(r1);                                              // 1..0 + F1..F10 via Fn
        r1.add(c("-", "_", KeyEvent.KEYCODE_MINUS).fn(KeyEvent.KEYCODE_F11));
        r1.add(c("=", "+", KeyEvent.KEYCODE_EQUALS).fn(KeyEvent.KEYCODE_F12));
        r1.add(c("\\", "|", KeyEvent.KEYCODE_BACKSLASH).fn(KeyEvent.KEYCODE_INSERT));
        r1.add(c("`", "~", KeyEvent.KEYCODE_GRAVE));
        rows.add(r1);

        // Row 2: Tab Q..P [ ] Delete
        List<KeyDef> r2 = new ArrayList<>();
        r2.add(func("Tab", KeyEvent.KEYCODE_TAB, 1.5f).fn(KeyEvent.KEYCODE_CAPS_LOCK));
        addLetters(r2, "QWERTYUIOP");
        r2.add(c("[", "{", KeyEvent.KEYCODE_LEFT_BRACKET).fn(KeyEvent.KEYCODE_DPAD_UP));
        r2.add(c("]", "}", KeyEvent.KEYCODE_RIGHT_BRACKET).fn(KeyEvent.KEYCODE_PAGE_UP));
        r2.add(func("Delete", KeyEvent.KEYCODE_DEL, 1.5f).fn(KeyEvent.KEYCODE_FORWARD_DEL));
        rows.add(r2);

        // Row 3: Control A..L ; ' Return
        List<KeyDef> r3 = new ArrayList<>();
        r3.add(mod("Ctrl", MOD_CTRL, 1.75f));
        addLetters(r3, "ASDFGHJKL");
        r3.add(c(";", ":", KeyEvent.KEYCODE_SEMICOLON).fn(KeyEvent.KEYCODE_DPAD_LEFT));
        r3.add(c("'", "\"", KeyEvent.KEYCODE_APOSTROPHE).fn(KeyEvent.KEYCODE_DPAD_RIGHT));
        r3.add(func("Return", KeyEvent.KEYCODE_ENTER, 2.25f));
        rows.add(r3);

        // Row 4: Shift Z..M , . / Shift Fn
        List<KeyDef> r4 = new ArrayList<>();
        r4.add(mod("Shift", MOD_SHIFT, 2.25f));
        addLetters(r4, "ZXCVBNM");
        r4.add(c(",", "<", KeyEvent.KEYCODE_COMMA).fn(KeyEvent.KEYCODE_MOVE_HOME));
        r4.add(c(".", ">", KeyEvent.KEYCODE_PERIOD).fn(KeyEvent.KEYCODE_MOVE_END));
        r4.add(c("/", "?", KeyEvent.KEYCODE_SLASH).fn(KeyEvent.KEYCODE_DPAD_DOWN));
        r4.add(mod("Shift", MOD_SHIFT, 1.75f));
        r4.add(new KeyDef("Fn", "Fn", 0, T_FN, 1f));
        rows.add(r4);

        // Row 5 (JIS-style): ◇ Alt 無変換 Space 変換 あ/A 全/半
        List<KeyDef> r5 = new ArrayList<>();
        r5.add(mod("◇", MOD_META, 1.5f));
        r5.add(mod("Alt", MOD_ALT, 1.5f));
        r5.add(jpKey("無変換", JP_MUHENKAN, 2f));
        r5.add(func("Space", KeyEvent.KEYCODE_SPACE, 4f).fn(KeyEvent.KEYCODE_PAGE_DOWN));
        r5.add(jpKey("変換", JP_HENKAN, 2f));
        r5.add(modeKey(2f));
        r5.add(widthKey(2f));
        rows.add(r5);

        return rows;
    }

    private void addDigits(List<KeyDef> row) {
        String[] sh = {")", "!", "@", "#", "$", "%", "^", "&", "*", "("}; // 0..9 shifted
        for (int d = 1; d <= 10; d++) {
            int digit = d % 10;                 // 1..9 then 0
            KeyDef k = c(String.valueOf(digit), sh[digit], KeyEvent.KEYCODE_0 + digit);
            k.fn(KeyEvent.KEYCODE_F1 + (d - 1)); // 1->F1 ... 9->F9, 0->F10
            row.add(k);
        }
    }

    private void addLetters(List<KeyDef> row, String letters) {
        for (int i = 0; i < letters.length(); i++) {
            char up = letters.charAt(i);
            char lo = Character.toLowerCase(up);
            row.add(c(String.valueOf(lo), String.valueOf(up),
                    KeyEvent.KEYCODE_A + (up - 'A')));
        }
    }

    // =====================================================================
    //  View construction
    // =====================================================================
    @Override
    public View onCreateInputView() {
        DisplayMetrics dm = getResources().getDisplayMetrics();
        screenW = dm.widthPixels;
        screenH = dm.heightPixels;
        keyboardWidthPx = Math.min(screenW, dp(520));

        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(colBg());
        root.setPadding(dp(4), dp(2), dp(4), dp(6));
        root.setLayoutParams(new ViewGroup.LayoutParams(keyboardWidthPx,
                ViewGroup.LayoutParams.WRAP_CONTENT));

        root.addView(buildHandleBar());
        root.addView(buildCandidateBar());
        root.addView(buildDictPanel());

        keysContainer = new LinearLayout(this);
        keysContainer.setOrientation(LinearLayout.VERTICAL);
        keysContainer.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));
        root.addView(keysContainer);

        rootView = root;
        buildKeyRows();
        return root;
    }

    /** (Re)builds all key rows into keysContainer — used on create and holo toggle. */
    private void buildKeyRows() {
        modButtons.clear();
        fnButton = modeButton = widthButton = null;
        keysContainer.removeAllViews();
        for (List<KeyDef> rowDef : buildLayout()) {
            keysContainer.addView(buildRow(rowDef));
        }
        updateModeButton();
        updateWidthButton();
        refreshModVisuals();
    }

    /** Multi-line dictionary result panel (hidden until 辞 is used). */
    private View buildDictPanel() {
        dictScroll = new android.widget.ScrollView(this);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(110));
        lp.bottomMargin = dp(4);
        dictScroll.setLayoutParams(lp);
        dictScroll.setBackground(keyBackground(0xF002060A));

        dictView = new TextView(this);
        dictView.setTextColor(0xFF8CFFF0);
        dictView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        dictView.setPadding(dp(12), dp(8), dp(12), dp(8));
        dictView.setOnClickListener(v -> dictScroll.setVisibility(View.GONE));
        dictScroll.addView(dictView);
        dictScroll.setVisibility(View.GONE);
        return dictScroll;
    }

    /** Conversion candidate bar (hidden until 変換/Space is used). */
    private View buildCandidateBar() {
        candidateScroll = new HorizontalScrollView(this);
        candidateScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(36));
        lp.bottomMargin = dp(4);
        candidateScroll.setLayoutParams(lp);
        candidateScroll.setBackground(keyBackground(0xFF12161A));

        candidateBar = new LinearLayout(this);
        candidateBar.setOrientation(LinearLayout.HORIZONTAL);
        candidateBar.setGravity(Gravity.CENTER_VERTICAL);
        candidateBar.setLayoutParams(new HorizontalScrollView.LayoutParams(
                HorizontalScrollView.LayoutParams.WRAP_CONTENT,
                HorizontalScrollView.LayoutParams.MATCH_PARENT));
        candidateScroll.addView(candidateBar);

        candidateScroll.setVisibility(View.GONE);
        return candidateScroll;
    }

    /** Top bar: drag handle + title + Dock button. */
    private View buildHandleBar() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(30));
        lp.bottomMargin = dp(4);
        bar.setLayoutParams(lp);

        TextView handle = new TextView(this);
        handle.setText("⠿  HHKB Pro — ドラッグで移動");
        handle.setTextColor(COL_GOLD);
        handle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        handle.setPadding(dp(10), 0, 0, 0);
        LinearLayout.LayoutParams hlp = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.MATCH_PARENT, 1f);
        handle.setLayoutParams(hlp);
        handle.setGravity(Gravity.CENTER_VERTICAL);
        attachDrag(handle);
        bar.addView(handle);

        bar.addView(barButton("辞", v -> doDictLookup()));
        bar.addView(barButton("Holo", v -> toggleHolo()));
        bar.addView(barButton("Dock", v -> dockToBottom()));
        return bar;
    }

    private Button barButton(String label, View.OnClickListener l) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        b.setTextColor(colText());
        b.setBackground(keyBackground(colFill(true)));
        b.setPadding(dp(6), 0, dp(6), 0);
        b.setMinWidth(0);
        b.setMinimumWidth(0);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, dp(28));
        lp.leftMargin = dp(4);
        b.setLayoutParams(lp);
        b.setOnClickListener(l);
        return b;
    }

    private LinearLayout buildRow(List<KeyDef> rowDef) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        float sum = 0f;
        for (KeyDef k : rowDef) sum += k.weight;
        row.setWeightSum(sum);
        LinearLayout.LayoutParams rlp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(46));
        rlp.bottomMargin = dp(3);
        row.setLayoutParams(rlp);

        for (KeyDef k : rowDef) row.addView(buildKey(k));
        return row;
    }

    private Button buildKey(final KeyDef k) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(keyLabel(k));
        b.setTextColor(colText());
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, labelSize(k));
        b.setPadding(0, 0, 0, 0);
        b.setMinWidth(0);
        b.setMinimumWidth(0);
        b.setMinHeight(0);
        b.setMinimumHeight(0);

        boolean special = k.type != T_CHAR;
        b.setBackground(keyBackground(colFill(special)));

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.MATCH_PARENT, k.weight);
        lp.leftMargin = dp(2);
        lp.rightMargin = dp(2);
        b.setLayoutParams(lp);

        if (k.type == T_MOD) {
            List<Button> list = modButtons.get(k.modId);
            if (list == null) { list = new ArrayList<>(); modButtons.put(k.modId, list); }
            list.add(b);
        }
        if (k.type == T_FN) fnButton = b;
        if (k.type == T_MODE) modeButton = b;
        if (k.type == T_WIDTH) widthButton = b;

        b.setOnClickListener(v -> onKey(k));
        return b;
    }

    private String keyLabel(KeyDef k) {
        if (k.type == T_CHAR && !k.label.equals(k.shift)
                && k.shift.length() == 1 && !Character.isLetter(k.shift.charAt(0))) {
            // show shifted symbol above the base, e.g. "! / 1"
            return k.shift + "\n" + k.label;
        }
        return k.label;
    }

    private float labelSize(KeyDef k) {
        if (k.type == T_JP) return 11f;               // 変換 / 無変換
        if (k.type == T_MODE || k.type == T_WIDTH) return 16f;   // あ/A · 全/半
        if (k.type == T_FUNC || k.type == T_MOD || k.type == T_FN) return 12f;
        if (k.type == T_CHAR && k.label.length() == 1 && Character.isLetter(k.label.charAt(0)))
            return 16f;
        return 12f;
    }

    private GradientDrawable keyBackground(int color) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(6));
        if (holo) g.setStroke(dp(2), 0xFF00E5FF);     // neon glow edge
        else g.setStroke(dp(1), 0xFF12161A);
        return g;
    }

    // ---- holographic-aware colours ---------------------------------------
    private int colBg()   { return holo ? 0xCC02060A : COL_BG; }
    private int colText() { return holo ? 0xFF8CFFF0 : COL_KEY_TXT; }
    private int colFill(boolean special) {
        if (holo) return special ? 0x3300C8FF : 0x2600E5FF;   // translucent neon
        return special ? COL_SPECIAL : COL_KEY;
    }

    private void toggleHolo() {
        holo = !holo;
        if (root != null) root.setBackgroundColor(colBg());
        // Rebuild the handle bar buttons' colours by rebuilding rows + leaving handle as is.
        buildKeyRows();
    }

    // =====================================================================
    //  Key handling
    // =====================================================================
    private void onKey(KeyDef k) {
        switch (k.type) {
            case T_MOD:
                cycle(k.modId);
                refreshModVisuals();
                return;
            case T_FN:
                fnState = next(fnState);
                refreshModVisuals();
                return;
            case T_FUNC:
                sendFunctional(k);
                consumeOneShots();
                return;
            case T_JP:
                handleJp(k);
                consumeOneShots();
                return;
            case T_MODE:
                toggleMode();
                return;
            case T_WIDTH:
                toggleWidth();
                return;
            default: // T_CHAR
                sendChar(k);
                consumeOneShots();
        }
    }

    // ---- Japanese mode ---------------------------------------------------
    private boolean kana() { return inputMode == MODE_KANA; }

    private void toggleMode() {
        InputConnection ic = getCurrentInputConnection();
        if (ic != null) jp.commitIfComposing(ic);
        inputMode = (inputMode == MODE_EN) ? MODE_KANA : MODE_EN;
        updateModeButton();
    }

    private void updateModeButton() {
        if (modeButton == null) return;
        boolean k = kana();
        modeButton.setText(k ? "あ" : "A");
        modeButton.setBackground(keyBackground(k ? COL_GOLD : colFill(true)));
        modeButton.setTextColor(k ? COL_LOCK_TXT : colText());
    }

    private void toggleWidth() {
        fullWidth = !fullWidth;
        jp.setPreferFullWidth(fullWidth);
        updateWidthButton();
    }

    private void updateWidthButton() {
        if (widthButton == null) return;
        widthButton.setText(fullWidth ? "全" : "半");
        widthButton.setBackground(keyBackground(fullWidth ? COL_GOLD : colFill(true)));
        widthButton.setTextColor(fullWidth ? COL_LOCK_TXT : colText());
    }

    /** Apply the current 全角/半角 preference to directly-typed ASCII text. */
    private String applyWidth(String s) {
        return fullWidth ? JapaneseInputEngine.toFullWidth(s) : s;
    }

    private void handleJp(KeyDef k) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;
        boolean handled;
        if (k.jpAction == JP_HENKAN) {
            handled = jp.convertNext(ic);   // kanji / kana candidate cycling
        } else {
            handled = jp.muhenkan(ic);
        }
        // Nothing to convert: behave like a hardware JIS key for other IMEs.
        if (!handled) sendKey(ic, k.keyCode, currentMeta());
    }

    // ---- candidate bar (JapaneseInputEngine.Listener) --------------------
    @Override
    public void onCandidates(List<String> candidates, int selected) {
        if (candidateBar == null || candidateScroll == null) return;
        candidateBar.removeAllViews();
        for (int i = 0; i < candidates.size(); i++) {
            final int idx = i;
            TextView chip = new TextView(this);
            chip.setText(candidates.get(i));
            chip.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18);
            chip.setPadding(dp(12), dp(2), dp(12), dp(2));
            chip.setGravity(Gravity.CENTER);
            boolean sel = i == selected;
            chip.setBackground(keyBackground(sel ? COL_GOLD : COL_KEY));
            chip.setTextColor(sel ? COL_LOCK_TXT : COL_KEY_TXT);
            LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.MATCH_PARENT);
            clp.rightMargin = dp(4);
            chip.setLayoutParams(clp);
            chip.setOnClickListener(v -> {
                InputConnection ic = getCurrentInputConnection();
                if (ic != null) jp.selectCandidate(ic, idx);
            });
            candidateBar.addView(chip);
        }
        candidateScroll.setVisibility(View.VISIBLE);
    }

    @Override
    public void onHideCandidates() {
        if (candidateBar != null) candidateBar.removeAllViews();
        if (candidateScroll != null) candidateScroll.setVisibility(View.GONE);
    }

    private void cycle(int modId) { modState[modId] = next(modState[modId]); }

    private int next(int s) { return (s + 1) % 3; }

    private boolean active(int modId) { return modState[modId] != OFF; }

    private boolean fnActive() { return fnState != OFF; }

    private int currentMeta() {
        int m = 0;
        if (active(MOD_SHIFT)) m |= KeyEvent.META_SHIFT_ON | KeyEvent.META_SHIFT_LEFT_ON;
        if (active(MOD_CTRL))  m |= KeyEvent.META_CTRL_ON  | KeyEvent.META_CTRL_LEFT_ON;
        if (active(MOD_ALT))   m |= KeyEvent.META_ALT_ON   | KeyEvent.META_ALT_LEFT_ON;
        if (active(MOD_META))  m |= KeyEvent.META_META_ON  | KeyEvent.META_META_LEFT_ON;
        return m;
    }

    private void sendChar(KeyDef k) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;

        boolean ctrlAltMeta = active(MOD_CTRL) || active(MOD_ALT) || active(MOD_META);

        // Fn layer takes priority when mapped (arrows, F-keys, navigation…).
        if (fnActive() && k.fnKeyCode != 0) {
            jp.commitIfComposing(ic);
            sendKey(ic, k.fnKeyCode, currentMeta());
            return;
        }

        if (ctrlAltMeta) {
            // Combos such as Ctrl+C, Alt+Tab, Meta+L are delivered as key events.
            jp.commitIfComposing(ic);
            sendKey(ic, k.keyCode, currentMeta());
            return;
        }

        // Japanese mode: route plain lowercase letters through romaji conversion.
        if (kana()) {
            char ch = k.label.length() == 1 ? k.label.charAt(0) : 0;
            if (!active(MOD_SHIFT) && ch >= 'a' && ch <= 'z') {
                jp.inputLetter(ic, ch);
                return;
            }
            // Digits / symbols / shifted letters: confirm any reading, then type ASCII.
            jp.commitIfComposing(ic);
            ic.commitText(applyWidth(active(MOD_SHIFT) ? k.shift : k.label), 1);
            return;
        }

        // English mode.
        ic.commitText(applyWidth(active(MOD_SHIFT) ? k.shift : k.label), 1);
    }

    private void sendFunctional(KeyDef k) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;
        boolean ctrlAltMeta = active(MOD_CTRL) || active(MOD_ALT) || active(MOD_META);

        // While composing Japanese: Space converts/cycles candidates, Enter
        // confirms the selection, and Backspace edits/cancels the reading.
        if (kana() && jp.isComposing() && !ctrlAltMeta && !fnActive()) {
            if (k.keyCode == KeyEvent.KEYCODE_SPACE) {
                jp.convertNext(ic);
                return;
            }
            if (k.keyCode == KeyEvent.KEYCODE_ENTER) {
                jp.commit(ic);
                return;
            }
            if (k.keyCode == KeyEvent.KEYCODE_DEL) {
                if (jp.backspace(ic)) return;
            }
            jp.commitIfComposing(ic);  // Esc / Tab: confirm first, then fall through
        }

        int code = (fnActive() && k.fnKeyCode != 0) ? k.fnKeyCode : k.keyCode;
        sendKey(ic, code, currentMeta());
    }

    private void sendKey(InputConnection ic, int keyCode, int meta) {
        long now = SystemClock.uptimeMillis();
        ic.sendKeyEvent(new KeyEvent(now, now, KeyEvent.ACTION_DOWN, keyCode, 0,
                meta, KeyEvent.KEYCODE_UNKNOWN, 0,
                KeyEvent.FLAG_SOFT_KEYBOARD | KeyEvent.FLAG_KEEP_TOUCH_MODE));
        ic.sendKeyEvent(new KeyEvent(now, now, KeyEvent.ACTION_UP, keyCode, 0,
                meta, KeyEvent.KEYCODE_UNKNOWN, 0,
                KeyEvent.FLAG_SOFT_KEYBOARD | KeyEvent.FLAG_KEEP_TOUCH_MODE));
    }

    /** Clear all one-shot modifiers after a key, keep locks. */
    private void consumeOneShots() {
        boolean changed = false;
        for (int i = 0; i < modState.length; i++) {
            if (modState[i] == ONESHOT) { modState[i] = OFF; changed = true; }
        }
        if (fnState == ONESHOT) { fnState = OFF; changed = true; }
        if (changed) refreshModVisuals();
    }

    private void refreshModVisuals() {
        for (Map.Entry<Integer, List<Button>> e : modButtons.entrySet()) {
            for (Button b : e.getValue()) styleSticky(b, modState[e.getKey()]);
        }
        if (fnButton != null) styleSticky(fnButton, fnState);
    }

    private void styleSticky(Button b, int state) {
        switch (state) {
            case ONESHOT:
                b.setBackground(keyBackground(COL_ONESHOT));
                b.setTextColor(COL_KEY_TXT);
                break;
            case LOCK:
                b.setBackground(keyBackground(COL_LOCK));
                b.setTextColor(COL_LOCK_TXT);
                break;
            default:
                b.setBackground(keyBackground(colFill(true)));
                b.setTextColor(colText());
        }
    }

    // =====================================================================
    //  Dictionary lookup (free KANJIDIC2 kanji + Webster English-English)
    // =====================================================================
    private void doDictLookup() {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;
        CharSequence before = ic.getTextBeforeCursor(40, 0);
        final String query = extractQuery(before);
        if (query == null) {
            showDict("辞書：直前に漢字、または英単語を入力してから「辞」を押してください。");
            return;
        }
        if (dictRepo == null) return;
        if (!dictRepo.isReady()) {
            showDict(dictRepo.isDownloading()
                    ? "辞書をダウンロード中…（KANJIDIC2＋英英辞典・無料、初回のみ）"
                    : "辞書を初回ダウンロード中…（無料：KANJIDIC2 漢字辞典＋Webster英英辞典）\n"
                      + "完了後にもう一度「辞」を押してください。");
            dictRepo.ensureDownloaded(
                    () -> mainHandler.post(() -> showDict("辞書の準備ができました。もう一度「辞」を押してください。")),
                    err -> mainHandler.post(() -> showDict("辞書のダウンロードに失敗しました: " + err
                            + "\n（ネットワーク接続を確認してください）")));
            return;
        }
        showDict("検索中… " + query);
        new Thread(() -> {
            String result = buildLookup(query);
            mainHandler.post(() -> showDict(result));
        }, "dict-lookup").start();
    }

    private String buildLookup(String q) {
        boolean latin = true;
        for (int i = 0; i < q.length(); i++) {
            if (!isLatinLetter(q.charAt(i))) { latin = false; break; }
        }
        if (latin) {
            String def = dictRepo.lookupEnglish(q);
            return "【英英辞典 / English】 " + q + "\n\n"
                    + (def != null ? def : "(見つかりませんでした)");
        }
        StringBuilder sb = new StringBuilder("【漢字辞典 / KANJIDIC2】 " + q + "\n");
        boolean any = false;
        for (int i = 0; i < q.length(); i++) {
            String e = dictRepo.lookupKanji(String.valueOf(q.charAt(i)));
            if (e != null) { sb.append("\n").append(e).append("\n"); any = true; }
        }
        if (!any) sb.append("\n(見つかりませんでした)");
        return sb.toString();
    }

    private String extractQuery(CharSequence cs) {
        if (cs == null || cs.length() == 0) return null;
        String s = cs.toString();
        int end = s.length();
        char last = s.charAt(end - 1);
        if (isLatinLetter(last)) {
            int i = end;
            while (i > 0 && isLatinLetter(s.charAt(i - 1))) i--;
            return s.substring(i, end);
        }
        if (isKanji(last)) {
            int i = end;
            while (i > 0 && isKanji(s.charAt(i - 1))) i--;
            return s.substring(i, end);
        }
        return null;
    }

    private static boolean isLatinLetter(char c) {
        return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
    }
    private static boolean isKanji(char c) {
        return (c >= 0x4E00 && c <= 0x9FFF) || (c >= 0x3400 && c <= 0x4DBF);
    }

    private void showDict(String text) {
        if (dictView == null || dictScroll == null) return;
        dictView.setText(text);
        dictScroll.setVisibility(View.VISIBLE);
        dictScroll.scrollTo(0, 0);
    }

    // =====================================================================
    //  Floating window: drag to move, Dock to reset
    // =====================================================================
    @Override
    public void onStartInputView(android.view.inputmethod.EditorInfo info, boolean restarting) {
        super.onStartInputView(info, restarting);
        jp.reset();  // no stale composition carried into a new field
        onHideCandidates();
        if (dictScroll != null) dictScroll.setVisibility(View.GONE);
        // Re-apply the chosen geometry each time the keyboard is shown.
        if (floating) applyFloating(); else dockToBottom();
    }

    @Override
    public void onFinishInputView(boolean finishingInput) {
        InputConnection ic = getCurrentInputConnection();
        if (ic != null) jp.commitIfComposing(ic);
        super.onFinishInputView(finishingInput);
    }

    private void attachDrag(View handle) {
        handle.setOnTouchListener(new View.OnTouchListener() {
            float downRawX, downRawY;
            int startX, startY;

            @Override
            public boolean onTouch(View v, MotionEvent ev) {
                switch (ev.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        if (!floating) {
                            // Enter floating mode anchored at the current location.
                            int h = rootView != null ? rootView.getHeight() : dp(280);
                            winX = Math.max(0, (screenW - keyboardWidthPx) / 2);
                            winY = Math.max(0, screenH - h - dp(40));
                            floating = true;
                        }
                        startX = winX;
                        startY = winY;
                        downRawX = ev.getRawX();
                        downRawY = ev.getRawY();
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        winX = (int) (startX + (ev.getRawX() - downRawX));
                        winY = (int) (startY + (ev.getRawY() - downRawY));
                        clampWindow();
                        applyFloating();
                        return true;
                    default:
                        return false;
                }
            }
        });
    }

    private void clampWindow() {
        int h = rootView != null ? rootView.getHeight() : dp(280);
        winX = Math.max(0, Math.min(winX, Math.max(0, screenW - keyboardWidthPx)));
        winY = Math.max(0, Math.min(winY, Math.max(0, screenH - h)));
    }

    private Window imeWindow() {
        return getWindow() != null ? getWindow().getWindow() : null;
    }

    private void applyFloating() {
        Window w = imeWindow();
        if (w == null || keyboardWidthPx == 0) return;
        WindowManager.LayoutParams lp = w.getAttributes();
        lp.gravity = Gravity.TOP | Gravity.START;
        lp.width = keyboardWidthPx;
        lp.height = WindowManager.LayoutParams.WRAP_CONTENT;
        lp.x = winX;
        lp.y = winY;
        // Let touches outside the keyboard reach the app underneath.
        lp.flags |= WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS;
        w.setAttributes(lp);
    }

    private void dockToBottom() {
        floating = false;
        Window w = imeWindow();
        if (w == null || keyboardWidthPx == 0) return;
        WindowManager.LayoutParams lp = w.getAttributes();
        lp.gravity = Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL;
        lp.width = keyboardWidthPx;
        lp.height = WindowManager.LayoutParams.WRAP_CONTENT;
        lp.x = 0;
        lp.y = 0;
        lp.flags |= WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL;
        w.setAttributes(lp);
    }

    // ---- util ------------------------------------------------------------
    private int dp(int v) {
        return Math.round(getResources().getDisplayMetrics().density * v);
    }
}
