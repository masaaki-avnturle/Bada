package com.bada.silenttalk;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

/**
 * Setup / launcher screen. Carries the same circular Voice-Access-style button
 * used by the floating launcher, plus the three permission steps Silent Talk
 * needs: Accessibility (to operate the device), Overlay (to float on top), and
 * Camera (for gaze / facial-expression tracking).
 */
public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        int pad = dp(20);
        root.setPadding(pad, pad, pad, pad);
        scroll.addView(root);

        root.addView(title("Silent Talk\nサイレントトーク"));
        root.addView(body(
                "声を出さずに、視線・表情・近接(赤外線)・温度センサーから翻訳した\n" +
                "コマンドで端末を操作するハンズフリー入力です（Voice Access の無音版）。"));

        // The Voice-Access-style circular launch button.
        root.addView(launchButton());
        root.addView(caption("タップでサイレントトークを起動 / 停止"));

        root.addView(section("セットアップ"));
        root.addView(button("① アクセシビリティを有効化",
                v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))));
        root.addView(button("② 重ね表示(オーバーレイ)を許可", v -> requestOverlay()));
        root.addView(button("③ カメラを許可（視線・表情用）", v -> requestCamera()));

        root.addView(section("使い方"));
        root.addView(body(
                "・起動すると画面に丸い操作ボタンとカーソルが出ます。\n" +
                "・視線（頭の向き）または端末の傾きでカーソルを移動。\n" +
                "・止めて見つめる(ドウェル) / まばたき / 近接センサーを覆う → 決定。\n" +
                "・右端のドックを見つめると 戻る/ホーム/履歴/通知/スクロール。\n" +
                "・ドック以外を決定するとその位置をタップします。"));

        root.addView(note(
                "※ 重要：温度計や赤外線センサーで思考そのものは読めません。本アプリは" +
                "観測できる信号（視線・まばたき・表情・近接・温度）を言語コマンドに翻訳します。" +
                "ガンマ関数の大域的部分積分多様体／熱ネットワークは信号融合の理論モデルとして" +
                "確信度・確定時間の調整に用いています。"));

        setContentView(scroll);
    }

    private View launchButton() {
        ImageView b = new ImageView(this);
        b.setImageResource(R.drawable.ic_silent);
        b.setBackgroundResource(R.drawable.btn_circle);
        int p = dp(26);
        b.setPadding(p, p, p, p);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(112), dp(112));
        lp.topMargin = dp(18);
        b.setLayoutParams(lp);
        b.setOnClickListener(v -> launchSilentTalk());
        return b;
    }

    private void launchSilentTalk() {
        if (!canOverlay()) {
            Toast.makeText(this, "先に「重ね表示」を許可してください", Toast.LENGTH_LONG).show();
            requestOverlay();
            return;
        }
        Intent i = new Intent(this, OverlayService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(i);
        else startService(i);
        Toast.makeText(this,
                "サイレントトーク起動。画面の丸ボタンでON/OFF。",
                Toast.LENGTH_LONG).show();
        moveTaskToBack(true);
    }

    private boolean canOverlay() {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.M || Settings.canDrawOverlays(this);
    }

    private void requestOverlay() {
        if (canOverlay()) {
            Toast.makeText(this, "許可済み", Toast.LENGTH_SHORT).show();
            return;
        }
        startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:" + getPackageName())));
    }

    private void requestCamera() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "許可済み", Toast.LENGTH_SHORT).show();
            return;
        }
        ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, 1);
    }

    // -- tiny UI helpers ---------------------------------------------------
    private TextView title(String s) { return text(s, 22, 0xFF1A73E8, dp(8)); }
    private TextView section(String s) { return text(s, 17, 0xFF1A73E8, dp(20)); }
    private TextView body(String s) { return text(s, 14, 0xFF333333, dp(6)); }
    private TextView caption(String s) {
        TextView t = text(s, 12, 0xFF777777, dp(6));
        t.setGravity(Gravity.CENTER);
        return t;
    }
    private TextView note(String s) {
        TextView t = text(s, 12, 0xFF8A6D1A, dp(20));
        t.setBackgroundColor(0x22C8A44A);
        t.setPadding(dp(12), dp(12), dp(12), dp(12));
        return t;
    }
    private TextView text(String s, int sp, int color, int topMargin) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.topMargin = topMargin;
        t.setLayoutParams(lp);
        return t;
    }
    private Button button(String s, View.OnClickListener l) {
        Button b = new Button(this);
        b.setText(s);
        b.setAllCaps(false);
        b.setOnClickListener(l);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(8);
        b.setLayoutParams(lp);
        return b;
    }

    private int dp(int v) { return Math.round(getResources().getDisplayMetrics().density * v); }
}
