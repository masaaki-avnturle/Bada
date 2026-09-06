package io.github.masaaki_avnturle.multiwindow;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.TypedValue;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * 時計ウィンドウ。表示中だけ 1 秒ごとに更新し、
 * 非表示 (onStop) では更新を止めて電力・メモリを節約する。
 */
public class ClockActivity extends Activity {

    private TextView time;
    private TextView date;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final SimpleDateFormat timeFmt = new SimpleDateFormat("HH:mm:ss", Locale.JAPAN);
    private final SimpleDateFormat dateFmt =
            new SimpleDateFormat("yyyy年M月d日 (E)", Locale.JAPAN);

    private final Runnable tick = new Runnable() {
        @Override public void run() {
            Date now = new Date();
            time.setText(timeFmt.format(now));
            date.setText(dateFmt.format(now));
            handler.postDelayed(this, 1000 - (SystemClock.elapsedRealtime() % 1000));
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle("時計");

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(Color.rgb(11, 42, 74));

        time = new TextView(this);
        time.setTextSize(TypedValue.COMPLEX_UNIT_SP, 52);
        time.setTypeface(Typeface.MONOSPACE, Typeface.BOLD);
        time.setTextColor(Color.WHITE);
        root.addView(time);

        date = new TextView(this);
        date.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        date.setTextColor(Color.rgb(160, 190, 220));
        root.addView(date);

        setContentView(root);
    }

    @Override
    protected void onStart() {
        super.onStart();
        tick.run();
    }

    @Override
    protected void onStop() {
        super.onStop();
        handler.removeCallbacks(tick);
    }
}
