package io.github.masaaki_avnturle.multiwindow;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.app.ActivityOptions;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.VelocityTracker;
import android.view.View;
import android.view.ViewConfiguration;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.text.Collator;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * ファイルキャビネット ウィンドウ。
 *
 * タブレット内のアプリとファイルを、横スライドではなく
 * 「札束 / ロロデックス / ファイルキャビネットの書類」をペラペラめくるように
 * 閲覧する。1 件 = 1 枚のマニラフォルダ風カードで、
 *   ・上下にドラッグ → カードが上端を軸に 3D 回転して 1 枚めくれる
 *   ・速くはじく (フリング) → 札束のように連続でリッフルめくり
 *   ・タップ → 開く (アプリはフリーフォーム ウィンドウ起動、
 *     フォルダはキャビネット内で移動、ファイルは対応アプリのウィンドウで表示)
 */
public class CabinetActivity extends Activity {

    private static final String PREFS = "bada_multiwindow";
    private static final String KEY_CASCADE = "cascade";

    private static final int TYPE_APP = 0;
    private static final int TYPE_DIR = 1;
    private static final int TYPE_FILE = 2;
    private static final int TYPE_NOTE = 3; // 案内カード (権限要求など)

    private static final int BG_CABINET = Color.rgb(52, 46, 40);
    private static final int MANILA = Color.rgb(245, 230, 200);
    private static final int MANILA_DARK = Color.rgb(216, 196, 158);
    private static final int INK = Color.rgb(60, 48, 32);

    private static class Item {
        int type;
        String name;
        String sub;
        String emoji;
        Drawable icon;    // アプリのみ
        String pkg;       // アプリのみ
        File file;        // ファイル/フォルダのみ
        boolean permNote; // 案内カード: タップで権限要求
    }

    private boolean appsMode = true;
    private final List<Item> items = new ArrayList<>();
    private int index = 0;
    private File rootDir;
    private File curDir;
    private boolean waitingPerm = false;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private FrameLayout stackArea;
    private View frontCard;
    private View overCard;   // 「前へ戻る」用: 上に被さって 90°→0° で降りてくる
    private TextView tabApps;
    private TextView tabFiles;
    private TextView pathText;
    private TextView upBtn;
    private TextView counter;

    private final SimpleDateFormat dateFmt =
            new SimpleDateFormat("yyyy/MM/dd HH:mm", Locale.JAPAN);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTitle("ファイルキャビネット");
        rootDir = Environment.getExternalStorageDirectory();
        curDir = rootDir;

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG_CABINET);

        // ---- タブ (アプリ / ファイル) + 上へ ----
        LinearLayout tabs = new LinearLayout(this);
        tabs.setOrientation(LinearLayout.HORIZONTAL);
        tabs.setPadding(dp(10), dp(10), dp(10), dp(4));
        tabApps = makeTab("📱 アプリ");
        tabFiles = makeTab("📁 ファイル");
        tabApps.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { switchMode(true); }
        });
        tabFiles.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { switchMode(false); }
        });
        tabs.addView(tabApps);
        tabs.addView(tabFiles);
        View sp = new View(this);
        tabs.addView(sp, new LinearLayout.LayoutParams(0, 1, 1f));
        upBtn = makeTab("⬆ 上へ");
        upBtn.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { goUp(); }
        });
        tabs.addView(upBtn);
        root.addView(tabs);

        pathText = new TextView(this);
        pathText.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        pathText.setTextColor(Color.rgb(200, 190, 175));
        pathText.setPadding(dp(14), 0, dp(14), 0);
        pathText.setSingleLine(true);
        root.addView(pathText);

        // ---- カードの束 ----
        stackArea = new FrameLayout(this);
        stackArea.setClipChildren(false);
        stackArea.setClipToPadding(false);
        attachFlipTouch(stackArea);
        root.addView(stackArea, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        // ---- フッター (件数 + ヒント) ----
        counter = new TextView(this);
        counter.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        counter.setTextColor(Color.WHITE);
        counter.setGravity(Gravity.CENTER);
        root.addView(counter);

        TextView hint = new TextView(this);
        hint.setText("上下にドラッグ = 1枚めくる ・ 速くはじく = 連続めくり ・ タップ = 開く");
        hint.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        hint.setTextColor(Color.rgb(170, 160, 145));
        hint.setGravity(Gravity.CENTER);
        hint.setPadding(dp(8), dp(2), dp(8), dp(8));
        root.addView(hint);

        setContentView(root);

        switchMode(true);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (waitingPerm && !appsMode && !needsFilePermission()) {
            waitingPerm = false;
            loadFiles();
        }
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        super.onRequestPermissionsResult(code, perms, results);
        if (!appsMode) loadFiles();
    }

    @Override
    public void onBackPressed() {
        if (!appsMode && curDir != null && !curDir.equals(rootDir)
                && curDir.getParentFile() != null) {
            goUp();
            return;
        }
        super.onBackPressed();
    }

    // ------------------------------------------------------------------ モード / 読み込み

    private void switchMode(boolean apps) {
        appsMode = apps;
        styleTab(tabApps, apps);
        styleTab(tabFiles, !apps);
        upBtn.setVisibility(apps ? View.GONE : View.VISIBLE);
        pathText.setVisibility(apps ? View.INVISIBLE : View.VISIBLE);
        if (apps) {
            loadApps();
        } else {
            loadFiles();
        }
    }

    private void loadApps() {
        items.clear();
        index = 0;
        Item loading = new Item();
        loading.type = TYPE_NOTE;
        loading.emoji = "⏳";
        loading.name = "読み込み中…";
        loading.sub = "インストール済みアプリを調べています";
        items.add(loading);
        rebind();
        new Thread(new Runnable() {
            @Override public void run() {
                final PackageManager pm = getPackageManager();
                Intent main = new Intent(Intent.ACTION_MAIN);
                main.addCategory(Intent.CATEGORY_LAUNCHER);
                List<ResolveInfo> ris = pm.queryIntentActivities(main, 0);
                final List<Item> loaded = new ArrayList<>();
                for (ResolveInfo ri : ris) {
                    if (getPackageName().equals(ri.activityInfo.packageName)) continue;
                    Item it = new Item();
                    it.type = TYPE_APP;
                    it.pkg = ri.activityInfo.packageName;
                    it.name = String.valueOf(ri.loadLabel(pm));
                    it.sub = it.pkg;
                    it.icon = ri.loadIcon(pm);
                    loaded.add(it);
                }
                final Collator col = Collator.getInstance(Locale.JAPAN);
                Collections.sort(loaded, new Comparator<Item>() {
                    @Override public int compare(Item a, Item b) {
                        return col.compare(a.name, b.name);
                    }
                });
                handler.post(new Runnable() {
                    @Override public void run() {
                        if (!appsMode) return; // その間にタブが切り替わった
                        items.clear();
                        items.addAll(loaded);
                        index = 0;
                        rebind();
                    }
                });
            }
        }, "cabinet-apps").start();
    }

    private void loadFiles() {
        items.clear();
        index = 0;
        if (needsFilePermission()) {
            Item note = new Item();
            note.type = TYPE_NOTE;
            note.permNote = true;
            note.emoji = "🔐";
            note.name = "ファイルへのアクセス許可が必要です";
            note.sub = Build.VERSION.SDK_INT >= 30
                    ? "このカードをタップして「すべてのファイルへのアクセス」を許可してください"
                    : "このカードをタップしてストレージへのアクセスを許可してください";
            items.add(note);
            rebind();
            return;
        }
        File[] fs = curDir.listFiles();
        if (fs == null) {
            Item note = new Item();
            note.type = TYPE_NOTE;
            note.emoji = "🚫";
            note.name = "このフォルダは読み取れません";
            note.sub = curDir.getAbsolutePath();
            items.add(note);
            rebind();
            return;
        }
        List<Item> dirs = new ArrayList<>();
        List<Item> files = new ArrayList<>();
        for (File f : fs) {
            Item it = new Item();
            it.file = f;
            it.name = f.getName();
            if (f.isDirectory()) {
                it.type = TYPE_DIR;
                it.emoji = "📁";
                it.sub = "フォルダ ・ " + dateFmt.format(new Date(f.lastModified()));
                dirs.add(it);
            } else {
                it.type = TYPE_FILE;
                it.emoji = emojiFor(f.getName());
                it.sub = human(f.length()) + " ・ " + dateFmt.format(new Date(f.lastModified()));
                files.add(it);
            }
        }
        final Collator col = Collator.getInstance(Locale.JAPAN);
        Comparator<Item> byName = new Comparator<Item>() {
            @Override public int compare(Item a, Item b) { return col.compare(a.name, b.name); }
        };
        Collections.sort(dirs, byName);
        Collections.sort(files, byName);
        items.addAll(dirs);
        items.addAll(files);
        if (items.isEmpty()) {
            Item note = new Item();
            note.type = TYPE_NOTE;
            note.emoji = "🗂";
            note.name = "(空のフォルダ)";
            note.sub = curDir.getAbsolutePath();
            items.add(note);
        }
        rebind();
    }

    private void goUp() {
        if (appsMode) return;
        File parent = curDir.getParentFile();
        if (curDir.equals(rootDir) || parent == null) {
            Toast.makeText(this, "いちばん上の階層です", Toast.LENGTH_SHORT).show();
            return;
        }
        curDir = parent;
        loadFiles();
    }

    private boolean needsFilePermission() {
        if (Build.VERSION.SDK_INT >= 30) {
            return !Environment.isExternalStorageManager();
        }
        return checkSelfPermission(android.Manifest.permission.READ_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED;
    }

    private void requestFilePermission() {
        waitingPerm = true;
        if (Build.VERSION.SDK_INT >= 30) {
            try {
                startActivity(new Intent(
                        Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                        Uri.parse("package:" + getPackageName())));
            } catch (Exception e) {
                startActivity(new Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION));
            }
        } else {
            requestPermissions(
                    new String[]{android.Manifest.permission.READ_EXTERNAL_STORAGE}, 1);
        }
    }

    // ------------------------------------------------------------------ カードの束の描画

    /** 現在の位置でカードの束を組み直す。 */
    private void rebind() {
        stackArea.removeAllViews();
        overCard = null;
        frontCard = null;
        if (items.isEmpty()) return;
        if (index < 0) index = 0;
        if (index >= items.size()) index = items.size() - 1;

        // 後ろに残っている枚数ぶん、上端に「めくり待ちのふち」を見せる
        int behind = Math.min(3, items.size() - index - 1);
        for (int i = behind; i >= 1; i--) {
            View edge = new View(this);
            GradientDrawable g = new GradientDrawable();
            g.setColor(i % 2 == 0 ? MANILA_DARK : MANILA);
            g.setCornerRadius(dp(8));
            edge.setBackground(g);
            FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.MATCH_PARENT, dp(14), Gravity.TOP);
            lp.leftMargin = dp(20 + i * 6);
            lp.rightMargin = dp(20 + i * 6);
            lp.topMargin = dp(26 - i * 7);
            stackArea.addView(edge, lp);
        }

        // 次のカード (めくった下から現れる)
        if (index + 1 < items.size()) {
            View under = buildCard(items.get(index + 1));
            under.setScaleX(0.97f);
            under.setScaleY(0.97f);
            stackArea.addView(under, cardParams());
        }

        // 現在のカード
        frontCard = buildCard(items.get(index));
        stackArea.addView(frontCard, cardParams());

        // 前のカード (下ドラッグで 90°→0° に降りてくる)
        if (index > 0) {
            overCard = buildCard(items.get(index - 1));
            overCard.setRotationX(90f);
            overCard.setAlpha(0f);
            stackArea.addView(overCard, cardParams());
        }

        counter.setText((index + 1) + " / " + items.size());
        if (!appsMode) pathText.setText(curDir.getAbsolutePath());
    }

    private FrameLayout.LayoutParams cardParams() {
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT);
        lp.leftMargin = dp(20);
        lp.rightMargin = dp(20);
        lp.topMargin = dp(28);
        lp.bottomMargin = dp(20);
        return lp;
    }

    private View buildCard(Item it) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(MANILA);
        bg.setCornerRadius(dp(12));
        bg.setStroke(dp(1), MANILA_DARK);
        card.setBackground(bg);
        card.setElevation(dp(8));
        card.setPadding(dp(18), dp(12), dp(18), dp(12));
        card.setCameraDistance(12000f * getResources().getDisplayMetrics().density);
        card.setPivotY(0f);

        // フォルダ タブ (種別ラベル)
        TextView tab = new TextView(this);
        tab.setText(it.type == TYPE_APP ? "アプリ"
                : it.type == TYPE_DIR ? "フォルダ"
                : it.type == TYPE_FILE ? "ファイル" : "お知らせ");
        tab.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        tab.setTextColor(INK);
        GradientDrawable tabBg = new GradientDrawable();
        tabBg.setColor(MANILA_DARK);
        tabBg.setCornerRadius(dp(6));
        tab.setBackground(tabBg);
        tab.setPadding(dp(10), dp(3), dp(10), dp(3));
        LinearLayout.LayoutParams tabLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        card.addView(tab, tabLp);

        // アイコン (アプリは実アイコン、それ以外は絵文字)
        FrameLayout iconArea = new FrameLayout(this);
        if (it.icon != null) {
            ImageView iv = new ImageView(this);
            iv.setImageDrawable(it.icon);
            FrameLayout.LayoutParams ivLp = new FrameLayout.LayoutParams(
                    dp(84), dp(84), Gravity.CENTER);
            iconArea.addView(iv, ivLp);
        } else {
            TextView em = new TextView(this);
            em.setText(it.emoji == null ? "📄" : it.emoji);
            em.setTextSize(TypedValue.COMPLEX_UNIT_SP, 64);
            em.setGravity(Gravity.CENTER);
            iconArea.addView(em, new FrameLayout.LayoutParams(
                    FrameLayout.LayoutParams.MATCH_PARENT,
                    FrameLayout.LayoutParams.MATCH_PARENT, Gravity.CENTER));
        }
        card.addView(iconArea, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        TextView name = new TextView(this);
        name.setText(it.name);
        name.setTypeface(Typeface.DEFAULT_BOLD);
        name.setTextSize(TypedValue.COMPLEX_UNIT_SP, 19);
        name.setTextColor(INK);
        name.setGravity(Gravity.CENTER_HORIZONTAL);
        name.setMaxLines(2);
        card.addView(name);

        TextView sub = new TextView(this);
        sub.setText(it.sub == null ? "" : it.sub);
        sub.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        sub.setTextColor(Color.rgb(120, 104, 80));
        sub.setGravity(Gravity.CENTER_HORIZONTAL);
        sub.setMaxLines(3);
        sub.setPadding(0, dp(4), 0, dp(6));
        card.addView(sub);

        TextView open = new TextView(this);
        open.setText(it.type == TYPE_APP ? "タップでウィンドウ起動"
                : it.type == TYPE_DIR ? "タップで中を開く"
                : it.type == TYPE_FILE ? "タップで表示" : "");
        open.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        open.setTextColor(Color.rgb(150, 130, 100));
        open.setGravity(Gravity.CENTER_HORIZONTAL);
        card.addView(open);

        return card;
    }

    // ------------------------------------------------------------------ めくり操作

    private void attachFlipTouch(final FrameLayout area) {
        area.setOnTouchListener(new View.OnTouchListener() {
            final int slop = ViewConfiguration.get(CabinetActivity.this).getScaledTouchSlop();
            float downY;
            long downT;
            int dir; // +1 = 次へ (上ドラッグ), -1 = 前へ (下ドラッグ), 0 = 未確定
            boolean animating;
            VelocityTracker vt;

            @Override public boolean onTouch(View v, MotionEvent ev) {
                if (animating) return true;
                switch (ev.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downY = ev.getY();
                        downT = ev.getEventTime();
                        dir = 0;
                        vt = VelocityTracker.obtain();
                        vt.addMovement(ev);
                        return true;
                    case MotionEvent.ACTION_MOVE: {
                        if (vt != null) vt.addMovement(ev);
                        float dy = ev.getY() - downY;
                        if (dir == 0 && Math.abs(dy) > slop) dir = dy < 0 ? 1 : -1;
                        if (dir == 1 && frontCard != null && index < items.size() - 1) {
                            frontCard.setRotationX(dragAngle(-dy, area.getHeight()));
                        } else if (dir == -1 && overCard != null) {
                            overCard.setAlpha(1f);
                            overCard.setRotationX(90f - dragAngle(dy, area.getHeight()));
                        }
                        return true;
                    }
                    case MotionEvent.ACTION_UP:
                    case MotionEvent.ACTION_CANCEL: {
                        float dy = ev.getY() - downY;
                        float vy = 0;
                        if (vt != null) {
                            vt.computeCurrentVelocity(1000);
                            vy = vt.getYVelocity();
                            vt.recycle();
                            vt = null;
                        }
                        boolean tap = Math.abs(dy) < slop
                                && ev.getEventTime() - downT < 300
                                && ev.getActionMasked() == MotionEvent.ACTION_UP;
                        if (tap) {
                            resetCards();
                            openCurrent();
                            return true;
                        }
                        if (Math.abs(vy) > 3200) {
                            // 札束リッフル: 速さに応じて連続でめくる
                            int steps = Math.min(25, (int) (Math.abs(vy) / 1800));
                            riffle(vy < 0 ? 1 : -1, Math.max(2, steps));
                            return true;
                        }
                        if (dir == 1 && frontCard != null && index < items.size() - 1) {
                            float a = frontCard.getRotationX();
                            if (a > 40f || vy < -1200) flipNext(a);
                            else settleBack(frontCard, a, 0f);
                        } else if (dir == -1 && overCard != null) {
                            float a = overCard.getRotationX();
                            if (a < 50f || vy > 1200) flipPrev(a);
                            else settleOver(a);
                        }
                        return true;
                    }
                }
                return false;
            }

            float dragAngle(float drag, int h) {
                if (drag < 0) drag = 0;
                float a = drag / (Math.max(1, h) * 0.55f) * 90f;
                return Math.min(90f, a);
            }

            void flipNext(float from) {
                animating = true;
                animate(frontCard, from, 90f, new Runnable() {
                    @Override public void run() {
                        index++;
                        rebind();
                        animating = false;
                    }
                });
            }

            void flipPrev(float from) {
                animating = true;
                animate(overCard, from, 0f, new Runnable() {
                    @Override public void run() {
                        index--;
                        rebind();
                        animating = false;
                    }
                });
            }

            void settleBack(View card, float from, float to) {
                animating = true;
                animate(card, from, to, new Runnable() {
                    @Override public void run() { animating = false; }
                });
            }

            void settleOver(float from) {
                animating = true;
                animate(overCard, from, 90f, new Runnable() {
                    @Override public void run() {
                        if (overCard != null) overCard.setAlpha(0f);
                        animating = false;
                    }
                });
            }

            void riffle(final int step, final int count) {
                animating = true;
                final Runnable[] tick = new Runnable[1];
                tick[0] = new Runnable() {
                    int left = count;
                    @Override public void run() {
                        int next = index + step;
                        if (left <= 0 || next < 0 || next >= items.size()) {
                            animating = false;
                            resetCards();
                            return;
                        }
                        index = next;
                        left--;
                        rebind();
                        // めくれた感を出す小さなフリック
                        if (frontCard != null) {
                            frontCard.setRotationX(28f);
                            frontCard.animate().rotationX(0f).setDuration(40).start();
                        }
                        handler.postDelayed(tick[0], 55);
                    }
                };
                tick[0].run();
            }
        });
    }

    private void resetCards() {
        if (frontCard != null) frontCard.setRotationX(0f);
        if (overCard != null) {
            overCard.setRotationX(90f);
            overCard.setAlpha(0f);
        }
    }

    private void animate(final View card, float from, float to, final Runnable end) {
        if (card == null) {
            end.run();
            return;
        }
        ValueAnimator va = ValueAnimator.ofFloat(from, to);
        va.setDuration(160);
        va.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
            @Override public void onAnimationUpdate(ValueAnimator a) {
                card.setRotationX((Float) a.getAnimatedValue());
            }
        });
        va.addListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator a) { end.run(); }
        });
        va.start();
    }

    // ------------------------------------------------------------------ 開く

    private void openCurrent() {
        if (items.isEmpty()) return;
        Item it = items.get(index);
        switch (it.type) {
            case TYPE_APP: {
                Intent i = getPackageManager().getLaunchIntentForPackage(it.pkg);
                if (i == null) {
                    Toast.makeText(this, it.name + " は起動できません", Toast.LENGTH_SHORT).show();
                    return;
                }
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startInWindow(i);
                break;
            }
            case TYPE_DIR:
                curDir = it.file;
                loadFiles();
                break;
            case TYPE_FILE: {
                Intent i = new Intent(Intent.ACTION_VIEW);
                i.setDataAndType(CabinetFileProvider.uriFor(it.file),
                        CabinetFileProvider.mimeFor(it.file.getName()));
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                        | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                try {
                    startInWindow(i);
                } catch (ActivityNotFoundException e) {
                    Toast.makeText(this, "このファイルを開けるアプリがありません",
                            Toast.LENGTH_SHORT).show();
                }
                break;
            }
            case TYPE_NOTE:
                if (it.permNote) requestFilePermission();
                break;
        }
    }

    /** フリーフォーム対応環境ではカスケード位置のウィンドウとして起動する。 */
    private void startInWindow(Intent intent) {
        try {
            ActivityOptions opts = ActivityOptions.makeBasic();
            opts.setLaunchBounds(nextCascadeBounds(520, 640));
            startActivity(intent, opts.toBundle());
        } catch (ActivityNotFoundException e) {
            throw e;
        } catch (Exception e) {
            startActivity(intent);
        }
    }

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

    // ------------------------------------------------------------------ 小物

    private TextView makeTab(String text) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        t.setPadding(dp(12), dp(6), dp(12), dp(6));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.rightMargin = dp(6);
        t.setLayoutParams(lp);
        styleTab(t, false);
        return t;
    }

    private void styleTab(TextView t, boolean selected) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(selected ? MANILA : Color.rgb(80, 72, 62));
        g.setCornerRadius(dp(8));
        t.setBackground(g);
        t.setTextColor(selected ? INK : Color.rgb(220, 212, 200));
        t.setTypeface(selected ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
    }

    private static String emojiFor(String name) {
        String n = name.toLowerCase(Locale.ROOT);
        if (n.endsWith(".png") || n.endsWith(".jpg") || n.endsWith(".jpeg")
                || n.endsWith(".gif") || n.endsWith(".webp") || n.endsWith(".bmp")) return "🖼";
        if (n.endsWith(".mp4") || n.endsWith(".mkv") || n.endsWith(".webm")
                || n.endsWith(".avi") || n.endsWith(".mov")) return "🎬";
        if (n.endsWith(".mp3") || n.endsWith(".wav") || n.endsWith(".flac")
                || n.endsWith(".ogg") || n.endsWith(".m4a")) return "🎵";
        if (n.endsWith(".pdf")) return "📕";
        if (n.endsWith(".txt") || n.endsWith(".md") || n.endsWith(".log")) return "📝";
        if (n.endsWith(".zip") || n.endsWith(".7z") || n.endsWith(".rar")
                || n.endsWith(".tar") || n.endsWith(".gz")) return "📦";
        if (n.endsWith(".apk")) return "🤖";
        if (n.endsWith(".doc") || n.endsWith(".docx")) return "📘";
        if (n.endsWith(".xls") || n.endsWith(".xlsx") || n.endsWith(".csv")) return "📗";
        if (n.endsWith(".ppt") || n.endsWith(".pptx")) return "📙";
        return "📄";
    }

    private static String human(long bytes) {
        if (bytes >= 1L << 30) return String.format(Locale.JAPAN, "%.1f GB", bytes / (double) (1L << 30));
        if (bytes >= 1L << 20) return String.format(Locale.JAPAN, "%.1f MB", bytes / (double) (1L << 20));
        if (bytes >= 1024) return String.format(Locale.JAPAN, "%.1f KB", bytes / 1024.0);
        return bytes + " B";
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
