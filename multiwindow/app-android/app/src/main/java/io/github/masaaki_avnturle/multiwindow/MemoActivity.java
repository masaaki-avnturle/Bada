package io.github.masaaki_avnturle.multiwindow;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.TypedValue;
import android.view.Gravity;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/**
 * メモ ウィンドウ。何枚でも開ける (documentLaunchMode="always")。
 *
 * 内容はウィンドウごとにアプリ専用領域 (filesDir) の小さなテキスト
 * ファイルへ自動保存する。空き容量が尽きて書き込めない場合も
 * クラッシュせず、その旨を表示して編集は継続できる。
 */
public class MemoActivity extends Activity {

    public static final String EXTRA_MEMO_ID = "memo_id";

    private EditText edit;
    private TextView status;
    private File file;
    private boolean dirty = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        long id = getIntent().getIntExtra(EXTRA_MEMO_ID, -1);
        if (id < 0) id = System.currentTimeMillis() % 100000;
        file = new File(getFilesDir(), "memo-" + id + ".txt");
        setTitle("メモ #" + id);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(255, 253, 240));

        edit = new EditText(this);
        edit.setGravity(Gravity.TOP | Gravity.START);
        edit.setBackgroundColor(Color.TRANSPARENT);
        edit.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        edit.setPadding(dp(12), dp(12), dp(12), dp(12));
        edit.setHint("ここにメモを書くと自動保存されます…");
        root.addView(edit, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        status = new TextView(this);
        status.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        status.setTextColor(Color.rgb(140, 130, 100));
        status.setPadding(dp(12), dp(2), dp(12), dp(4));
        status.setText(file.getName());
        root.addView(status);

        setContentView(root);

        load();
        edit.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void afterTextChanged(Editable s) { dirty = true; }
        });
    }

    @Override
    protected void onPause() {
        super.onPause();
        save();
    }

    private void load() {
        if (!file.exists()) return;
        try (FileInputStream in = new FileInputStream(file)) {
            byte[] buf = new byte[(int) file.length()];
            int off = 0;
            while (off < buf.length) {
                int r = in.read(buf, off, buf.length - off);
                if (r < 0) break;
                off += r;
            }
            edit.setText(new String(buf, 0, off, StandardCharsets.UTF_8));
        } catch (IOException e) {
            status.setText("読み込みエラー: " + e.getMessage());
        }
    }

    private void save() {
        if (!dirty) return;
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(edit.getText().toString().getBytes(StandardCharsets.UTF_8));
            dirty = false;
            status.setText(file.getName() + " — 保存済み");
        } catch (IOException e) {
            // 空き容量不足などでもクラッシュさせない
            status.setText("⚠ 保存できません(空き容量不足?): " + e.getMessage());
            Toast.makeText(this, "メモを保存できませんでした。空き容量を確認してください。",
                    Toast.LENGTH_LONG).show();
        }
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
