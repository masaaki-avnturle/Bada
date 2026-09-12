package com.bada.antigravityos;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * AntiGravity OS -- the generative-AI operating system on the Bada phase
 * core, running on-device. The stage-0 C interpreter is compiled with the
 * NDK; this activity is only a terminal: it hands the interpreter the same
 * agos.bada init process the desktop builds certify, and shows the flight
 * session (G1-G4 invariants re-derived at runtime).
 */
public class MainActivity extends Activity {
    static { System.loadLibrary("agos"); }

    private native String runBada(String path);

    private TextView console;
    private ScrollView scroll;
    private Button bootButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.BLACK);

        bootButton = new Button(this);
        bootButton.setText("RE-BOOT ANTI-GRAVITY OS (PID 1)");
        bootButton.setOnClickListener(v -> boot());

        console = new TextView(this);
        console.setTypeface(Typeface.MONOSPACE);
        console.setTextSize(11f);
        console.setTextColor(Color.rgb(0x7f, 0xff, 0x7f));
        console.setBackgroundColor(Color.BLACK);
        console.setPadding(24, 24, 24, 24);
        console.setHorizontallyScrolling(true);

        android.widget.HorizontalScrollView hscroll =
                new android.widget.HorizontalScrollView(this);
        hscroll.addView(console);

        scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.addView(hscroll);

        root.addView(bootButton, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        setContentView(root);

        boot();
    }

    private void boot() {
        bootButton.setEnabled(false);
        console.setText("charging the phase core ...\n");
        new Thread(() -> {
            String log;
            try {
                File script = new File(getCacheDir(), "agos.bada");
                try (InputStream in = getAssets().open("agos.bada");
                     OutputStream out = new FileOutputStream(script)) {
                    byte[] buf = new byte[8192];
                    int n;
                    while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                }
                log = runBada(script.getAbsolutePath());
            } catch (Exception e) {
                log = "boot failed: " + e;
            }
            final String text = log;
            runOnUiThread(() -> {
                console.setText(text);
                bootButton.setEnabled(true);
                scroll.post(() -> scroll.fullScroll(ScrollView.FOCUS_DOWN));
            });
        }).start();
    }
}
