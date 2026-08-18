package bada.android;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.util.concurrent.Executors;

import bada.coder.Coder;
import bada.mind.MindReader;
import bada.silent.SilentTalk;
import bada.silent.Whisper;
import bada.silent.Vim;
// SilentTalk.Thought / thoughtFill drive the 🧠 思考入力 button
import bada.qc.Isa;
import bada.qc.PseudoQC;
import bada.quantum.SpaceTelegraph;

/**
 * Bada Android front end. One screen, modes selected by a spinner:
 *   ① 宇宙電信 Telegraph   — quantum-entanglement space telegraph
 *   ② 擬似QC モニタ        — von-Neumann pseudo QC: control-circuit monitor
 *   ③ 半導体 Verilog       — the pseudo QC's semiconductor (Verilog) source
 *   ④ 思考言語化 Mind      — thought-verbalization simulation
 *   ⑤ コード生成 Coder     — thought-to-code transformer (EN/JA)
 *   ⑥ サイレント入力 IME   — silent-talk input method: cues -> text/code
 *   ⑦ ウィスパード Whisper — whispered English reconstruction / unknown language
 *   ⑧ Bada Vim エディタ    — embedded vi-like editor; :math inserts a long math paper
 * Every engine is the same shared pure-Java core, so the APK ships no Ruby.
 */
public class MainActivity extends Activity {

    private static final String QC_DEMO = "H 0; CX 0 1; HALT";
    private static final String MIND_DEMO = "光 と 音 の 記憶 が 波 の よう に 流れ 望み と 恐れ が 交錯 する";
    private static final String CODE_DEMO = "print hello 3 times loop";
    private static final String SILENT_DEMO =
            "光 記憶 波 | :code | :lang ruby | fibonacci 8 | :qc | bell | :verilog | ghz | :bada | 光 記憶 "
            + "| :whisper | qntm lght wv | φωτ κυμα | :report | φωτ μνημη κυμα σημα "
            + "| :latex | 多様体 量子 もつれ | :math | 多様体 量子 もつれ | :telegraph | QUANTUM HELLO";
    private static final String WHISPER_DEMO = "qntm lght mmry wv sgnl";
    // '|'-separated vi/ex commands driven through the embedded Bada Vim editor.
    private static final String VIM_DEMO =
            "iタイトル：多様体研究 | o序論 | :whisperen qntm lght wv mmry sgnl "
            + "| :burst qntm lght wv;mmry sgnl fld;bll ntngl stt "
            + "| :verilog semiconductor lattice qubit gate | :qc entangle bell measure "
            + "| :math 多様体 量子 もつれ | :w paper.tex";

    private Spinner mode;
    private EditText input;
    private Spinner material;
    private TextView output;
    private final Handler ui = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int pad = dp(12);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("Bada 量子もつれ電信 ＋ 擬似量子計算機");
        title.setTextSize(18);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(title);

        mode = new Spinner(this);
        mode.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"① 宇宙電信 Telegraph", "② 擬似QC モニタ投射",
                        "③ 半導体 Verilog 生成", "④ 思考言語化 Mind (sim)",
                        "⑤ コード生成 Coder (EN/JA)", "⑥ サイレント入力 IME (sim)",
                        "⑦ ウィスパード Whisper (sim)", "⑧ Bada Vim エディタ (sim)"}));
        root.addView(mode);

        input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setText("QUANTUM HELLO FROM EARTH");
        root.addView(input);

        material = new Spinner(this);
        material.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"GaAs", "InAs", "InGaAs", "Si", "diamond(NV)"}));
        root.addView(material);

        Button think = new Button(this);
        think.setText("🧠 思考入力 (Thought Input)");
        think.setOnClickListener(v -> captureThought());
        root.addView(think);

        Button whisperBtn = new Button(this);
        whisperBtn.setText("🔉 ウィスパード英語 (Whisper EN)");
        whisperBtn.setOnClickListener(v -> showWhisperInput());
        root.addView(whisperBtn);

        Button go = new Button(this);
        go.setText("実行 (Run)");
        go.setOnClickListener(v -> runSelected());
        root.addView(go);

        mode.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) {
                material.setVisibility(pos == 0 ? View.VISIBLE : View.GONE);
                switch (pos) {
                    case 0 -> input.setText("QUANTUM HELLO FROM EARTH");
                    case 1, 2 -> input.setText(QC_DEMO);
                    case 3 -> input.setText(MIND_DEMO);
                    case 4 -> input.setText(CODE_DEMO);
                    case 5 -> input.setText(SILENT_DEMO);
                    case 6 -> input.setText(WHISPER_DEMO);
                    case 7 -> input.setText(VIM_DEMO);
                    default -> { }
                }
                runSelected();
            }
            @Override public void onNothingSelected(AdapterView<?> p) { }
        });

        output = new TextView(this);
        output.setTypeface(Typeface.MONOSPACE);
        output.setTextSize(11);
        output.setTextColor(Color.parseColor("#101418"));
        output.setPadding(dp(8), dp(8), dp(8), dp(8));
        output.setTextIsSelectable(true);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(output);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f);
        lp.topMargin = dp(8);
        root.addView(scroll, lp);

        setContentView(root);
        runSelected();
    }

    private int thoughtNonce = 0;
    private int whisperThoughtNonce = 0;

    // Thought-input with NO typed or spoken input: each tap captures thought-tokens
    // from the gamma-manifold prior and fills the current mode's field via the
    // Mind transformer, above silent-talk precision.
    private void captureThought() {
        String kind = thoughtKind(mode.getSelectedItemPosition());
        SilentTalk.Thought t = SilentTalk.thoughtCapture(kind, thoughtNonce++);
        input.setText(t.text);
        Toast.makeText(this, String.format("思考を捕捉して入力（発声なし）precision %.1f%% > silent-talk %.1f%%",
                t.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100), Toast.LENGTH_LONG).show();
        runSelected();
    }

    // Field shape per mode: QC/Verilog want a program (qasm), Coder an intent,
    // the rest plain verbalized text.
    private static String thoughtKind(int mode) {
        return switch (mode) {
            case 1, 2 -> "qasm";
            case 4 -> "intent";
            default -> "text";
        };
    }

    // Whisper English mode for ANY function: a FULL-SCREEN, MULTI-LINE whisper
    // editor (not a short one-line field). Type many whispered lines directly and
    // reconstruct the whole block AT ONCE (複数行を一辺に・一瞬で), voicelessly,
    // above silent-talk precision, then fill the current mode's field.
    private void showWhisperInput() {
        final EditText cue = new EditText(this);
        cue.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        cue.setMinLines(6);
        cue.setGravity(android.view.Gravity.TOP | android.view.Gravity.START);
        cue.setTypeface(android.graphics.Typeface.MONOSPACE);
        cue.setHint("複数行のウィスパード英語（母音を落として）をそのまま入力\n例:\nqntm lght wv\nbll ntngl mesure");
        new AlertDialog.Builder(this)
                .setTitle("🔉 ウィスパード英語 — 全画面・複数行（発声せず・一瞬で）")
                .setMessage("複数行のウィスパード英語を直接入力してください。複数行を一辺に、完全な英語へ一括復元します（短文入力ではありません）。")
                .setView(cue)
                .setPositiveButton("⚡ 一括復元", (d, w) -> {
                    Whisper.Result r = Whisper.verbalizeBlock(cue.getText().toString());
                    input.setText(r.text);
                    int lines = r.text.split("\n", -1).length;
                    Toast.makeText(this, String.format("一括ウィスパード復元 %d行を一瞬で (precision %.1f%% > silent-talk %.1f%%)",
                            lines, r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100), Toast.LENGTH_LONG).show();
                    runSelected();
                })
                .setNeutralButton("🧠 思考入力", (d, w) -> {
                    // 打鍵せず・発声せず、思考から複数行を一辺に捕捉して入力
                    SilentTalk.Thought t = SilentTalk.thoughtBlock("text", whisperThoughtNonce++, 6);
                    input.setText(t.text);
                    int lines = t.text.split("\n", -1).length;
                    Toast.makeText(this, String.format("🧠 思考入力 %d行を一辺に捕捉 (precision %.1f%% > silent-talk %.1f%%)",
                            lines, t.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100), Toast.LENGTH_LONG).show();
                    runSelected();
                })
                .setNegativeButton("取消", null)
                .show();
    }

    private void runSelected() {
        final int m = mode.getSelectedItemPosition();
        final String text = input.getText().toString();
        final String mat = (String) material.getSelectedItem();
        output.setText("… computing …");
        Executors.newSingleThreadExecutor().execute(() -> {
            String result;
            try {
                result = switch (m) {
                    case 0 -> telegraph(text, mat);
                    case 3 -> new MindReader().render(text, "対象");
                    case 4 -> coder(text);
                    case 5 -> silent(text);
                    case 6 -> whisper(text);
                    case 7 -> vim(text);
                    default -> pseudoQc(text, m == 2);
                };
            } catch (Throwable t) {
                result = "error: " + t;
            }
            final String out = result;
            ui.post(() -> output.setText(out));
        });
    }

    private String telegraph(String text, String material) {
        String msg = text.trim().isEmpty() ? "HELLO SPACE" : text.trim();
        return new SpaceTelegraph(material, 4.0, 3).render(msg);
    }

    private String coder(String intent) {
        Coder.GenResult r = Coder.generate(intent, null);
        StringBuilder sb = new StringBuilder();
        sb.append("# language : ").append(r.language)
          .append(String.format("  (confidence %.2f)\n", r.confidence));
        sb.append("# reserved : ").append(String.join(" ", r.reservedUsed)).append("\n");
        sb.append(String.format("# precision: %.1f%%  (silent-talk %.1f%%)\n\n",
                r.precision * 100, Coder.SILENT_TALK_BASELINE * 100));
        sb.append(r.code);
        return sb.toString();
    }

    // Silent-talk IME (simulation): each '|'-separated segment is a silently-typed
    // cue or a :command; the Mind transformer verbalizes cues into a document and
    // the Coder transformer generates source in :code mode.
    private String silent(String text) {
        SilentTalk.Session s = new SilentTalk.Session();
        StringBuilder log = new StringBuilder();
        for (String seg : text.split("\\|")) {
            seg = seg.trim();
            if (seg.isEmpty()) continue;
            String out = s.render(s.feed(seg));
            if (!out.isEmpty()) log.append(out).append("\n");
        }
        StringBuilder sb = new StringBuilder();
        sb.append("=== サイレント入力ログ ===\n").append(log);
        sb.append("\n=== 入力結果 (document) ===\n").append(s.text()).append("\n\n");
        sb.append(String.format("precision = %.1f%%  (silent-talk %.1f%%)  -> %s",
                s.precision() * 100, SilentTalk.SILENT_TALK_BASELINE * 100,
                s.exceedsSilentTalk() ? "EXCEEDS" : "below"));
        return sb.toString();
    }

    // Whispered / unknown-language -> LONG-form report (長長文, not short), 発声せず.
    private String whisper(String text) {
        Whisper.Report r = Whisper.longReport(text);
        return "入力 (whispered/unknown):\n  " + text
                + "\n\n長長文レポート (" + r.sentences + "文, source=" + r.lang + "):\n" + r.text
                + String.format("%n%nprecision = %.1f%%  (silent-talk %.1f%%)  -> %s",
                        r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100,
                        r.precision > SilentTalk.SILENT_TALK_BASELINE ? "EXCEEDS" : "below");
    }

    // Bada Vim embedded editor: run '|'-separated vi/ex commands over a buffer.
    private String vim(String text) {
        Vim v = new Vim("");
        for (String seg : text.split("\\|")) {
            seg = seg.trim();
            if (!seg.isEmpty()) v.feed(seg);
        }
        return "=== Bada Vim " + v.status() + " ===\n" + v.text();
    }

    private String pseudoQc(String text, boolean verilog) {
        String src = text.replace(';', '\n');
        int n = inferQubits(src);
        try (PseudoQC qc = new PseudoQC(n).load(src).run()) {
            return verilog ? qc.verilog() : qc.report();
        }
    }

    private int inferQubits(String src) {
        int n = 1;
        try {
            for (Isa.Instr ins : Isa.assemble(src)) {
                n = Math.max(n, Math.max(ins.a, ins.b) + 1);
            }
        } catch (Throwable ignored) {
            return 2;
        }
        return Math.max(1, n);
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
