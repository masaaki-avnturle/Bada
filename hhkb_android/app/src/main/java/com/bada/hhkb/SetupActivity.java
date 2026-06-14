package com.bada.hhkb;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Launcher / help screen for the Bada HHKB keyboard.
 *
 * It is also referenced as the IME's {@code settingsActivity}, so the same
 * screen opens from Android 12's "On-screen keyboard" settings.
 */
public class SetupActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(20);
        root.setPadding(pad, pad, pad, pad);
        scroll.addView(root);

        root.addView(title("Bada HHKB Pro\nフローティング・キーボード"));
        root.addView(body(
                "Happy Hacking Keyboard Pro 風のレイアウトを再現した、画面上を自由に\n" +
                "ドラッグ移動できる Android 12 対応キーボードです。\n\n" +
                "Esc / Tab / Control / Shift / Alt / Meta(◇) / Fn など特殊キーを\n" +
                "すべて搭載し、Fn レイヤーで矢印・F1〜F12・PgUp/PgDn 等も入力できます。"));

        root.addView(stepHeader("① 入力方法として有効化する"));
        root.addView(body("下のボタンで「画面キーボード」設定を開き、" +
                "『Bada HHKB Pro Keyboard』を ON にしてください。"));
        root.addView(button("入力方法の設定を開く", v -> startActivity(
                new Intent(Settings.ACTION_INPUT_METHOD_SETTINGS))));

        root.addView(stepHeader("② キーボードを切り替える"));
        root.addView(body("文字入力欄をタップした状態で、下のボタンから " +
                "Bada HHKB を選択します。"));
        root.addView(button("キーボードを切り替える", v -> {
            InputMethodManager imm =
                    (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
            if (imm != null) imm.showInputMethodPicker();
        }));

        root.addView(stepHeader("③ 使い方"));
        root.addView(body(
                "・上部のバー（⠿ ハンドル）をドラッグするとキーボードを移動できます。\n" +
                "・[Dock] で画面下中央に戻ります。\n" +
                "・Shift / Ctrl / Alt / ◇ / Fn は 1回タップで次の1キーだけ有効、\n" +
                "  もう1回タップでロック（固定）、もう1回で解除されます。\n" +
                "・Fn + 数字列 = F1〜F12、Fn + [ ; ' / = ↑ ← → ↓ など。"));

        root.addView(body("\n動作確認用の入力欄 ↓"));
        android.widget.EditText test = new android.widget.EditText(this);
        test.setHint("ここをタップして入力テスト");
        root.addView(test);

        setContentView(scroll);
    }

    private TextView title(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(22);
        t.setTextColor(Color.parseColor("#1B1F24"));
        t.setGravity(Gravity.CENTER_HORIZONTAL);
        t.setPadding(0, 0, 0, dp(16));
        return t;
    }

    private TextView stepHeader(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(17);
        t.setTextColor(Color.parseColor("#8A6D1A"));
        t.setPadding(0, dp(22), 0, dp(6));
        return t;
    }

    private TextView body(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(14);
        t.setTextColor(Color.parseColor("#33373C"));
        return t;
    }

    private Button button(String s, View.OnClickListener l) {
        Button b = new Button(this);
        b.setText(s);
        b.setOnClickListener(l);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(8);
        b.setLayoutParams(lp);
        return b;
    }

    private int dp(int v) {
        return Math.round(getResources().getDisplayMetrics().density * v);
    }
}
