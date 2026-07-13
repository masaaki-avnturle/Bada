package bada.android;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;

import java.util.concurrent.Executors;

import bada.quantum.SpaceTelegraph;

/**
 * Bada Space Telegraph — Android front end. The whole physics engine is the
 * same shared pure-Java core (bada.quantum.*) used by the Windows EXE, so the
 * APK ships no Ruby runtime. The UI takes a message, runs prove() + transmit(),
 * and shows the seven-pillar report.
 */
public class MainActivity extends Activity {

    private EditText input;
    private Spinner material;
    private Spinner redundancy;
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
        title.setText("Bada 量子もつれ・汎用電信通信機");
        title.setTextSize(18);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(title);

        TextView sub = new TextView(this);
        sub.setText("ベルの実験・5次方程式カリア・Jones相関・不確定性・半導体・証明・宇宙通信");
        sub.setTextSize(11);
        sub.setPadding(0, dp(2), 0, dp(8));
        root.addView(sub);

        input = new EditText(this);
        input.setInputType(InputType.TYPE_CLASS_TEXT);
        input.setHint("メッセージ (message)");
        input.setText("QUANTUM HELLO FROM EARTH");
        root.addView(input);

        LinearLayout opts = new LinearLayout(this);
        opts.setOrientation(LinearLayout.HORIZONTAL);
        opts.setPadding(0, dp(6), 0, dp(6));

        material = new Spinner(this);
        material.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"GaAs", "InAs", "InGaAs", "Si", "diamond(NV)"}));
        opts.addView(labelled("材料", material));

        redundancy = new Spinner(this);
        redundancy.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item,
                new String[]{"1", "3", "5", "7"}));
        redundancy.setSelection(1);
        opts.addView(labelled("冗長度", redundancy));
        root.addView(opts);

        Button send = new Button(this);
        send.setText("送信・証明 (Transmit & Prove)");
        send.setOnClickListener(v -> transmit());
        root.addView(send);

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
        transmit(); // render once on launch
    }

    private LinearLayout labelled(String text, View field) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(0, 0, dp(16), 0);
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextSize(11);
        box.addView(t);
        box.addView(field);
        return box;
    }

    private void transmit() {
        final String msg = input.getText().toString().trim().isEmpty()
                ? "HELLO SPACE" : input.getText().toString().trim();
        final String mat = (String) material.getSelectedItem();
        final int red = Integer.parseInt((String) redundancy.getSelectedItem());
        output.setText("… computing (量子もつれ計算中) …");
        Executors.newSingleThreadExecutor().execute(() -> {
            String report;
            try {
                report = new SpaceTelegraph(mat, 4.0, red).render(msg);
            } catch (Throwable t) {
                report = "error: " + t;
            }
            final String result = report;
            ui.post(() -> output.setText(result));
        });
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
