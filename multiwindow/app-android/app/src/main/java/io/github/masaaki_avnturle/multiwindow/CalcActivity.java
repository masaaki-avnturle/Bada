package io.github.masaaki_avnturle.multiwindow;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * 電卓ウィンドウ。クラシック電卓と同じ「左から順に計算」方式。
 * フリーフォームで小さくリサイズしても崩れないよう全マスを重み付きで配置。
 */
public class CalcActivity extends Activity {

    private TextView display;
    private double acc = 0;
    private char pendingOp = 0;
    private boolean startNewNumber = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle("電卓");

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(30, 34, 42));

        display = new TextView(this);
        display.setText("0");
        display.setGravity(Gravity.END | Gravity.CENTER_VERTICAL);
        display.setTextSize(TypedValue.COMPLEX_UNIT_SP, 34);
        display.setTypeface(Typeface.MONOSPACE);
        display.setTextColor(Color.WHITE);
        display.setPadding(dp(12), dp(8), dp(12), dp(8));
        display.setSingleLine(true);
        root.addView(display, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(4);
        grid.setRowCount(5);
        String[] keys = {
                "C", "±", "%", "÷",
                "7", "8", "9", "×",
                "4", "5", "6", "−",
                "1", "2", "3", "+",
                "0", ".", "⌫", "=",
        };
        for (final String k : keys) {
            Button b = new Button(this);
            b.setText(k);
            b.setAllCaps(false);
            b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
            boolean op = "C±%÷×−+=⌫".contains(k);
            b.setTextColor(Color.WHITE);
            b.setBackgroundColor(op ? Color.rgb(63, 136, 197) : Color.rgb(52, 58, 70));
            GridLayout.LayoutParams lp = new GridLayout.LayoutParams(
                    GridLayout.spec(GridLayout.UNDEFINED, 1f),
                    GridLayout.spec(GridLayout.UNDEFINED, 1f));
            lp.width = 0;
            lp.height = 0;
            lp.setMargins(dp(2), dp(2), dp(2), dp(2));
            b.setLayoutParams(lp);
            b.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) { press(k); }
            });
            grid.addView(b);
        }
        root.addView(grid, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 4f));

        setContentView(root);
    }

    private void press(String k) {
        char c = k.charAt(0);
        if (c >= '0' && c <= '9') {
            String cur = startNewNumber ? "" : display.getText().toString();
            if (cur.equals("0")) cur = "";
            display.setText(cur + c);
            startNewNumber = false;
        } else if (c == '.') {
            String cur = startNewNumber ? "0" : display.getText().toString();
            if (!cur.contains(".")) display.setText(cur + ".");
            startNewNumber = false;
        } else if (c == 'C') {
            acc = 0; pendingOp = 0; startNewNumber = true;
            display.setText("0");
        } else if (c == '⌫') {
            String cur = display.getText().toString();
            display.setText(cur.length() > 1 ? cur.substring(0, cur.length() - 1) : "0");
        } else if (c == '±') {
            double v = current();
            show(-v);
            startNewNumber = false;
        } else if (c == '%') {
            show(current() / 100.0);
            startNewNumber = false;
        } else if (c == '=' ) {
            applyPending();
            pendingOp = 0;
            startNewNumber = true;
        } else { // + − × ÷
            applyPending();
            pendingOp = c;
            startNewNumber = true;
        }
    }

    private void applyPending() {
        double v = current();
        if (pendingOp == 0) {
            acc = v;
        } else if (pendingOp == '+') {
            acc += v;
        } else if (pendingOp == '−') {
            acc -= v;
        } else if (pendingOp == '×') {
            acc *= v;
        } else if (pendingOp == '÷') {
            acc = (v == 0) ? Double.NaN : acc / v;
        }
        show(acc);
    }

    private double current() {
        try {
            return Double.parseDouble(display.getText().toString());
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private void show(double v) {
        if (Double.isNaN(v) || Double.isInfinite(v)) {
            display.setText("エラー");
            return;
        }
        if (v == Math.rint(v) && Math.abs(v) < 1e15) {
            display.setText(String.valueOf((long) v));
        } else {
            display.setText(String.valueOf(v));
        }
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
