package bada.android;

import android.app.Activity;
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

import java.util.concurrent.Executors;

import bada.qc.Isa;
import bada.qc.PseudoQC;
import bada.quantum.SpaceTelegraph;

/**
 * Bada Android front end. One screen, three modes selected by a spinner:
 *   ① 宇宙電信 Telegraph   — quantum-entanglement space telegraph
 *   ② 擬似QC モニタ        — von-Neumann pseudo QC: control-circuit monitor
 *   ③ 半導体 Verilog       — the pseudo QC's semiconductor (Verilog) source
 * Both engines are the same shared pure-Java core, so the APK ships no Ruby.
 */
public class MainActivity extends Activity {

    private static final String QC_DEMO = "H 0; CX 0 1; HALT";

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
                new String[]{"① 宇宙電信 Telegraph", "② 擬似QC モニタ投射", "③ 半導体 Verilog 生成"}));
        root.addView(mode);

        input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setText("QUANTUM HELLO FROM EARTH");
        root.addView(input);

        material = new Spinner(this);
        material.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"GaAs", "InAs", "InGaAs", "Si", "diamond(NV)"}));
        root.addView(material);

        Button go = new Button(this);
        go.setText("実行 (Run)");
        go.setOnClickListener(v -> runSelected());
        root.addView(go);

        mode.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) {
                boolean qc = pos != 0;
                material.setVisibility(qc ? View.GONE : View.VISIBLE);
                input.setText(qc ? QC_DEMO : "QUANTUM HELLO FROM EARTH");
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

    private void runSelected() {
        final int m = mode.getSelectedItemPosition();
        final String text = input.getText().toString();
        final String mat = (String) material.getSelectedItem();
        output.setText("… computing …");
        Executors.newSingleThreadExecutor().execute(() -> {
            String result;
            try {
                result = (m == 0) ? telegraph(text, mat) : pseudoQc(text, m == 2);
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
