package io.github.masaaki_avnturle.multiwindow;

import android.app.Activity;
import android.app.ActivityManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.os.StatFs;
import android.util.TypedValue;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.util.Locale;

/**
 * 空き容量モニター ウィンドウ。
 *
 * 「ハードディスク (内部ストレージ) やメモリの空きが少ない」タブレットで
 * 状況をひと目で確認できるよう、内部ストレージと RAM の使用率を
 * 2 秒ごとに表示する。使用率が 90% を超えた項目は赤字で警告する。
 */
public class MonitorActivity extends Activity {

    private TextView storageLabel;
    private ProgressBar storageBar;
    private TextView ramLabel;
    private ProgressBar ramBar;
    private TextView note;
    private final Handler handler = new Handler(Looper.getMainLooper());

    private final Runnable refresh = new Runnable() {
        @Override public void run() {
            update();
            handler.postDelayed(this, 2000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle("空き容量モニター");

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(16);
        root.setPadding(pad, pad, pad, pad);
        root.setBackgroundColor(Color.rgb(245, 247, 250));

        TextView h1 = header("内部ストレージ");
        root.addView(h1);
        storageLabel = value();
        root.addView(storageLabel);
        storageBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        storageBar.setMax(100);
        root.addView(storageBar, barParams());

        TextView h2 = header("メモリ (RAM)");
        h2.setPadding(0, dp(14), 0, 0);
        root.addView(h2);
        ramLabel = value();
        root.addView(ramLabel);
        ramBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        ramBar.setMax(100);
        root.addView(ramBar, barParams());

        note = new TextView(this);
        note.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        note.setTextColor(Color.rgb(120, 130, 145));
        note.setPadding(0, dp(14), 0, 0);
        note.setText("2秒ごとに自動更新。このウィンドウを開いたまま作業できます。");
        root.addView(note);

        setContentView(root);
    }

    @Override
    protected void onStart() {
        super.onStart();
        refresh.run();
    }

    @Override
    protected void onStop() {
        super.onStop();
        handler.removeCallbacks(refresh);
    }

    private void update() {
        // 内部ストレージ
        StatFs fs = new StatFs(Environment.getDataDirectory().getAbsolutePath());
        long total = fs.getTotalBytes();
        long free = fs.getAvailableBytes();
        int usedPct = total > 0 ? (int) (100 - free * 100 / total) : 0;
        storageLabel.setText(String.format(Locale.JAPAN,
                "空き %s / 全体 %s (使用 %d%%)", human(free), human(total), usedPct));
        storageLabel.setTextColor(usedPct >= 90 ? Color.rgb(200, 40, 40) : Color.rgb(30, 40, 55));
        storageBar.setProgress(usedPct);

        // RAM
        ActivityManager am = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
        if (am != null) {
            am.getMemoryInfo(mi);
            int ramPct = mi.totalMem > 0
                    ? (int) (100 - mi.availMem * 100 / mi.totalMem) : 0;
            ramLabel.setText(String.format(Locale.JAPAN,
                    "空き %s / 全体 %s (使用 %d%%)%s",
                    human(mi.availMem), human(mi.totalMem), ramPct,
                    mi.lowMemory ? " ⚠ 低メモリ状態" : ""));
            ramLabel.setTextColor(mi.lowMemory || ramPct >= 90
                    ? Color.rgb(200, 40, 40) : Color.rgb(30, 40, 55));
            ramBar.setProgress(ramPct);
        }
    }

    private static String human(long bytes) {
        if (bytes >= 1L << 30) return String.format(Locale.JAPAN, "%.1f GB", bytes / (double) (1L << 30));
        if (bytes >= 1L << 20) return String.format(Locale.JAPAN, "%.1f MB", bytes / (double) (1L << 20));
        return String.format(Locale.JAPAN, "%.1f KB", bytes / 1024.0);
    }

    private TextView header(String text) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        t.setTextColor(Color.rgb(11, 42, 74));
        return t;
    }

    private TextView value() {
        TextView t = new TextView(this);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        t.setTextColor(Color.rgb(30, 40, 55));
        t.setPadding(0, dp(2), 0, dp(4));
        return t;
    }

    private LinearLayout.LayoutParams barParams() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(10));
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
