package io.github.masaaki_avnturle.multiwindow;

import android.app.Activity;
import android.app.ActivityOptions;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.View;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * ランチャー ウィンドウ。
 *
 * ボタンを押すたびに、各ツールを OS のフリーフォーム ウィンドウ
 * (Samsung ポップアップ表示 / Samsung DeX / Android freeform) として
 * タブレット画面上へ直接開く。アプリの画面「内部」に描く擬似ウィンドウではなく、
 * それぞれが独立した Android タスク = 独立ウィンドウになる。
 *
 * 仕組み:
 *   - Intent.FLAG_ACTIVITY_NEW_DOCUMENT | FLAG_ACTIVITY_MULTIPLE_TASK
 *       → 起動のたびに新しいタスク (= 新しいウィンドウ)
 *   - ActivityOptions#setLaunchBounds(Rect)
 *       → フリーフォーム対応端末では指定した位置・サイズの
 *         フリーフォーム ウィンドウとして開く (カスケード配置)
 */
public class LauncherActivity extends Activity {

    private static final String PREFS = "bada_multiwindow";
    private static final String KEY_CASCADE = "cascade";
    private static final String KEY_MEMO_SEQ = "memo_seq";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(20);
        root.setPadding(pad, pad, pad, pad);
        root.setBackgroundColor(Color.rgb(245, 247, 250));

        TextView title = new TextView(this);
        title.setText("Bada MultiWindow");
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 26);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(Color.rgb(11, 42, 74));
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText(freeformSupported()
                ? "ボタンを押すと、各ツールがタブレット画面上の独立した\nフリーフォーム ウィンドウとして開きます(何枚でも)。"
                : "ボタンを押すと各ツールが独立ウィンドウとして開きます。\nSamsung 端末では最近使ったアプリ画面のアイコンから\n「ポップアップ表示で開く」を選ぶとフリーフォームになります。");
        subtitle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        subtitle.setTextColor(Color.rgb(70, 85, 100));
        subtitle.setPadding(0, dp(6), 0, dp(14));
        root.addView(subtitle);

        GridLayout grid = new GridLayout(this);
        grid.setColumnCount(2);
        addTool(grid, "📝 メモ", Color.rgb(63, 136, 197), MemoActivity.class, 360, 420);
        addTool(grid, "🧮 電卓", Color.rgb(244, 185, 66), CalcActivity.class, 300, 440);
        addTool(grid, "🕐 時計", Color.rgb(68, 187, 164), ClockActivity.class, 340, 200);
        addTool(grid, "📊 空き容量モニター", Color.rgb(120, 100, 200), MonitorActivity.class, 360, 320);
        root.addView(grid);

        TextView hint = new TextView(this);
        hint.setText("💡 使い方のヒント\n"
                + "・各ウィンドウはドラッグで移動、端をドラッグでサイズ変更できます。\n"
                + "・同じツールを何度でも開けます(メモを 3 枚並べる等)。\n"
                + "・Samsung DeX / One UI のポップアップ表示に対応しています。\n"
                + "・WebView 不使用・依存ライブラリゼロの軽量設計なので、\n"
                + "  ストレージやメモリの空きが少ないタブレットでも動作します。\n"
                + "・空き容量が心配なときは「空き容量モニター」を開いたまま\n"
                + "  作業してください。");
        hint.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        hint.setTextColor(Color.rgb(90, 100, 115));
        hint.setPadding(0, dp(16), 0, 0);
        root.addView(hint);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.addView(root);
        setContentView(scroll);
    }

    private void addTool(GridLayout grid, String label, int color,
                         final Class<?> activity, final int widthDp, final int heightDp) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(color);
        GridLayout.LayoutParams lp = new GridLayout.LayoutParams(
                GridLayout.spec(GridLayout.UNDEFINED, 1f),
                GridLayout.spec(GridLayout.UNDEFINED, 1f));
        lp.width = 0;
        lp.height = dp(76);
        lp.setMargins(dp(4), dp(4), dp(4), dp(4));
        b.setLayoutParams(lp);
        b.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                openWindow(activity, widthDp, heightDp);
            }
        });
        grid.addView(b);
    }

    /** ツールを独立フリーフォーム ウィンドウとして開く。 */
    private void openWindow(Class<?> activity, int widthDp, int heightDp) {
        Intent intent = new Intent(this, activity);
        // 起動のたびに新規タスク → 独立ウィンドウ (マルチインスタンス)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_DOCUMENT
                | Intent.FLAG_ACTIVITY_MULTIPLE_TASK);
        if (activity == MemoActivity.class) {
            intent.putExtra(MemoActivity.EXTRA_MEMO_ID, nextMemoId());
        }
        try {
            ActivityOptions opts = ActivityOptions.makeBasic();
            opts.setLaunchBounds(nextCascadeBounds(widthDp, heightDp));
            startActivity(intent, opts.toBundle());
        } catch (Exception e) {
            // launch bounds 非対応端末などでは通常起動にフォールバック
            try {
                startActivity(intent);
            } catch (Exception e2) {
                Toast.makeText(this, "起動できませんでした: " + e2.getMessage(),
                        Toast.LENGTH_SHORT).show();
            }
        }
    }

    /** ウィンドウが重ならないよう、少しずつずらした (カスケード) 起動位置を返す。 */
    private Rect nextCascadeBounds(int widthDp, int heightDp) {
        DisplayMetrics dm = getResources().getDisplayMetrics();
        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        int n = prefs.getInt(KEY_CASCADE, 0);
        prefs.edit().putInt(KEY_CASCADE, (n + 1) % 8).apply();

        int w = Math.min(dp(widthDp), dm.widthPixels - dp(32));
        int h = Math.min(dp(heightDp), dm.heightPixels - dp(32));
        int step = dp(40);
        int maxX = Math.max(dp(16), dm.widthPixels - w - dp(16));
        int maxY = Math.max(dp(16), dm.heightPixels - h - dp(16));
        int x = Math.min(dp(48) + n * step, maxX);
        int y = Math.min(dp(48) + n * step, maxY);
        return new Rect(x, y, x + w, y + h);
    }

    private int nextMemoId() {
        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        int seq = prefs.getInt(KEY_MEMO_SEQ, 0) + 1;
        prefs.edit().putInt(KEY_MEMO_SEQ, seq).apply();
        return seq;
    }

    private boolean freeformSupported() {
        return getPackageManager().hasSystemFeature(
                PackageManager.FEATURE_FREEFORM_WINDOW_MANAGEMENT);
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
