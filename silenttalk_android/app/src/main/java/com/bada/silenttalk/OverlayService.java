package com.bada.silenttalk;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.core.content.ContextCompat;
import androidx.lifecycle.LifecycleService;

import com.bada.silenttalk.CommandTranslator.Command;
import com.google.common.util.concurrent.ListenableFuture;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * The Silent Talk runtime: a floating Voice-Access-style button, a gaze cursor,
 * a command dock and a HUD. It fuses camera gaze/expression with the IR proximity
 * and thermal sensors (via {@link ThermalManifold}) and drives the device through
 * {@link SilentTalkAccessibilityService}.
 */
public class OverlayService extends LifecycleService
        implements FaceGazeAnalyzer.Listener, SensorHub.Listener {

    private WindowManager wm;
    private DisplayMetrics dm;

    private ImageView fab;
    private WindowManager.LayoutParams fabLp;
    private FrameLayout hud;
    private View cursor;
    private TextView hudText;
    private boolean hudAttached = false;

    private boolean active = false;

    // engine state
    private float cursorX, cursorY, lastX, lastY;
    private volatile float gazeDx, gazeDy, faceQuality = 0.6f;
    private volatile boolean pendingBlink, pendingProximity;
    private long stationaryStart = 0, lastSelect = 0, lastGazeTime = 0;
    private float lastTempC = Float.NaN;

    private final List<DockBtn> dock = new ArrayList<>();
    private SensorHub sensorHub;
    private ExecutorService cameraExecutor;
    private ProcessCameraProvider cameraProvider;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable ticker = this::tick;

    private static final class DockBtn {
        final RectF rect = new RectF();
        final Command cmd;
        final TextView view;
        DockBtn(Command cmd, TextView view) { this.cmd = cmd; this.view = view; }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        dm = getResources().getDisplayMetrics();
        startAsForeground();
        addFab();
    }

    @Override
    public int onStartCommand(android.content.Intent intent, int flags, int startId) {
        super.onStartCommand(intent, flags, startId);
        return START_STICKY;
    }

    // -- foreground notification ------------------------------------------
    private void startAsForeground() {
        String ch = "silenttalk";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationManager nm = getSystemService(NotificationManager.class);
            nm.createNotificationChannel(new NotificationChannel(
                    ch, getString(R.string.notif_channel), NotificationManager.IMPORTANCE_LOW));
        }
        Notification.Builder nb = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, ch)
                : new Notification.Builder(this);
        Notification n = nb
                .setContentTitle(getString(R.string.app_name))
                .setContentText("サイレントトーク 待機中")
                .setSmallIcon(R.drawable.ic_silent)
                .build();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(1, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA);
        } else {
            startForeground(1, n);
        }
    }

    private int overlayType() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;
    }

    // -- floating Voice-Access-style button -------------------------------
    private void addFab() {
        fab = new ImageView(this);
        fab.setImageResource(R.drawable.ic_silent);
        fab.setBackgroundResource(R.drawable.btn_circle);
        int pad = dp(14);
        fab.setPadding(pad, pad, pad, pad);

        fabLp = new WindowManager.LayoutParams(dp(56), dp(56),
                overlayType(),
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);
        fabLp.gravity = Gravity.TOP | Gravity.START;
        fabLp.x = dm.widthPixels - dp(72);
        fabLp.y = dm.heightPixels / 2;

        fab.setOnTouchListener(new View.OnTouchListener() {
            float downX, downY; int startX, startY; boolean moved;
            @Override public boolean onTouch(View v, MotionEvent e) {
                switch (e.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downX = e.getRawX(); downY = e.getRawY();
                        startX = fabLp.x; startY = fabLp.y; moved = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        int nx = startX + (int) (e.getRawX() - downX);
                        int ny = startY + (int) (e.getRawY() - downY);
                        if (Math.hypot(nx - startX, ny - startY) > dp(8)) moved = true;
                        fabLp.x = nx; fabLp.y = ny;
                        wm.updateViewLayout(fab, fabLp);
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (!moved) toggleActive();
                        return true;
                }
                return false;
            }
        });
        wm.addView(fab, fabLp);
    }

    private void toggleActive() {
        if (active) stopEngine(); else startEngine();
    }

    // -- engine on/off -----------------------------------------------------
    private void startEngine() {
        active = true;
        buildHud();
        cursorX = dm.widthPixels / 2f;
        cursorY = dm.heightPixels / 2f;
        sensorHub = new SensorHub(this, this);
        sensorHub.start();
        startCamera();
        handler.post(ticker);
    }

    private void stopEngine() {
        active = false;
        handler.removeCallbacks(ticker);
        if (sensorHub != null) { sensorHub.stop(); sensorHub = null; }
        stopCamera();
        if (hudAttached) { wm.removeView(hud); hudAttached = false; }
    }

    // -- camera ------------------------------------------------------------
    private void startCamera() {
        if (ContextCompat.checkSelfPermission(this, android.Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            return;  // sensor / tilt fallback handles steering
        }
        cameraExecutor = Executors.newSingleThreadExecutor();
        final ListenableFuture<ProcessCameraProvider> future =
                ProcessCameraProvider.getInstance(this);
        future.addListener(() -> {
            try {
                cameraProvider = future.get();
                ImageAnalysis analysis = new ImageAnalysis.Builder()
                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build();
                analysis.setAnalyzer(cameraExecutor, new FaceGazeAnalyzer(this));
                cameraProvider.unbindAll();
                cameraProvider.bindToLifecycle(this, CameraSelector.DEFAULT_FRONT_CAMERA, analysis);
            } catch (Exception e) {
                // Camera unavailable: fall back to tilt/IR steering silently.
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private void stopCamera() {
        try {
            if (cameraProvider != null) cameraProvider.unbindAll();
        } catch (Exception ignored) { }
        cameraProvider = null;
        if (cameraExecutor != null) { cameraExecutor.shutdown(); cameraExecutor = null; }
    }

    // -- HUD (cursor + dock + telemetry) ----------------------------------
    private void buildHud() {
        hud = new FrameLayout(this);

        hudText = new TextView(this);
        hudText.setTextColor(Color.WHITE);
        hudText.setBackgroundColor(0xAA000000);
        hudText.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        hudText.setPadding(dp(12), dp(6), dp(12), dp(6));
        FrameLayout.LayoutParams tlp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT);
        tlp.gravity = Gravity.TOP;
        hud.addView(hudText, tlp);

        // cursor
        cursor = new View(this);
        GradientDrawable cd = new GradientDrawable();
        cd.setShape(GradientDrawable.OVAL);
        cd.setColor(0x55FFD54F);
        cd.setStroke(dp(3), 0xFFFFD54F);
        cursor.setBackground(cd);
        hud.addView(cursor, new FrameLayout.LayoutParams(dp(30), dp(30)));

        // command dock down the right edge
        dock.clear();
        Command[] cmds = {Command.BACK, Command.HOME, Command.RECENTS,
                Command.NOTIFICATIONS, Command.SCROLL_UP, Command.SCROLL_DOWN};
        int bw = dp(64), bh = dp(52), gap = dp(8);
        int x = dm.widthPixels - bw - dp(6);
        int totalH = cmds.length * bh + (cmds.length - 1) * gap;
        int y0 = Math.max(dp(48), (dm.heightPixels - totalH) / 2);
        for (int i = 0; i < cmds.length; i++) {
            int y = y0 + i * (bh + gap);
            TextView b = new TextView(this);
            b.setText(CommandTranslator.label(cmds[i]));
            b.setTextColor(Color.WHITE);
            b.setGravity(Gravity.CENTER);
            b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(0xCC1A73E8);
            bg.setCornerRadius(dp(10));
            b.setBackground(bg);
            FrameLayout.LayoutParams blp = new FrameLayout.LayoutParams(bw, bh);
            blp.leftMargin = x; blp.topMargin = y;
            hud.addView(b, blp);
            DockBtn db = new DockBtn(cmds[i], b);
            db.rect.set(x, y, x + bw, y + bh);
            dock.add(db);
        }

        WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                overlayType(),
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE
                        | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                        | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        wm.addView(hud, lp);
        hudAttached = true;
    }

    // -- main loop ---------------------------------------------------------
    private void tick() {
        if (!active) return;
        long now = System.currentTimeMillis();

        float speed = dp(16);
        cursorX += gazeDx * speed;
        cursorY += gazeDy * speed;
        cursorX = clamp(cursorX, dp(16), dm.widthPixels - dp(16));
        cursorY = clamp(cursorY, dp(48), dm.heightPixels - dp(16));
        cursor.setX(cursorX - dp(15));
        cursor.setY(cursorY - dp(15));

        double move = Math.hypot(cursorX - lastX, cursorY - lastY);
        if (move < dp(6)) {
            if (stationaryStart == 0) stationaryStart = now;
        } else {
            stationaryStart = 0;
        }
        lastX = cursorX; lastY = cursorY;

        double conf = ThermalManifold.confidence(
                faceQuality, sensorHub != null && sensorHub.isProximityNear(), lastTempC);
        long dwell = ThermalManifold.dwellMillis(conf);

        boolean dwellHit = stationaryStart > 0 && (now - stationaryStart) >= dwell;
        if ((dwellHit || pendingBlink || pendingProximity) && now - lastSelect > 700) {
            pendingBlink = false; pendingProximity = false;
            lastSelect = now; stationaryStart = 0;
            doSelect();
        }
        updateHud(conf, dwell);
        handler.postDelayed(ticker, 33);
    }

    private void doSelect() {
        Command cmd = null;
        for (DockBtn b : dock) {
            if (b.rect.contains(cursorX, cursorY)) { cmd = b.cmd; break; }
        }
        SilentTalkAccessibilityService svc = SilentTalkAccessibilityService.get();
        if (svc == null) {
            hudText.setText("⚠ 操作サービス未接続（設定でアクセシビリティを有効化）");
            return;
        }
        if (cmd == null) {
            svc.tap(cursorX, cursorY);
            flash(CommandTranslator.spoken(Command.TAP));
            return;
        }
        switch (cmd) {
            case BACK: svc.back(); break;
            case HOME: svc.home(); break;
            case RECENTS: svc.recents(); break;
            case NOTIFICATIONS: svc.notifications(); break;
            case SCROLL_UP:
                svc.swipe(dm.widthPixels / 2f, dm.heightPixels * 0.35f,
                        dm.widthPixels / 2f, dm.heightPixels * 0.7f, 300); break;
            case SCROLL_DOWN:
                svc.swipe(dm.widthPixels / 2f, dm.heightPixels * 0.7f,
                        dm.widthPixels / 2f, dm.heightPixels * 0.35f, 300); break;
            default: break;
        }
        flash(CommandTranslator.spoken(cmd));
    }

    private String lastFlash = "";
    private long flashUntil = 0;
    private void flash(String s) {
        lastFlash = s;
        flashUntil = System.currentTimeMillis() + 1200;
    }

    private void updateHud(double conf, long dwell) {
        String mode = (System.currentTimeMillis() - lastGazeTime < 600) ? "視線" : "傾き";
        String temp = Float.isNaN(lastTempC) ? "—" : String.format("%.1f℃", lastTempC);
        String ir = (sensorHub != null && sensorHub.isProximityNear()) ? "近" : "遠";
        String flashTxt = System.currentTimeMillis() < flashUntil ? "   " + lastFlash : "";
        hudText.setText(String.format(
                "サイレントトーク ● %s追従 | IR赤外線:%s | 温度:%s | 確信度:%.2f | 確定:%dms%s",
                mode, ir, temp, conf, dwell, flashTxt));
    }

    // -- analyzer / sensor callbacks --------------------------------------
    @Override public void onGaze(float dx, float dy, float quality) {
        gazeDx = dx; gazeDy = dy; faceQuality = quality;
        lastGazeTime = System.currentTimeMillis();
    }
    @Override public void onBlink() { pendingBlink = true; }
    @Override public void onSmile() { pendingProximity = true; /* smile = quick select too */ }
    @Override public void onFaceLost() { faceQuality = 0.35f; }

    @Override public void onTilt(float dx, float dy) {
        // Only steer by tilt when no fresh camera gaze is arriving.
        if (System.currentTimeMillis() - lastGazeTime > 500) {
            gazeDx = dx; gazeDy = dy;
            if (faceQuality < 0.7f) faceQuality = 0.7f;
        }
    }
    @Override public void onProximity(boolean near) { if (near) pendingProximity = true; }
    @Override public void onTemperature(float celsius) { lastTempC = celsius; }

    @Override
    public void onDestroy() {
        stopEngine();
        if (fab != null) { try { wm.removeView(fab); } catch (Exception ignored) {} }
        super.onDestroy();
    }

    private int dp(int v) { return Math.round(dm.density * v); }
    private static float clamp(float v, float lo, float hi) {
        return v < lo ? lo : (v > hi ? hi : v);
    }
}
