package io.github.masaaki_avnturle.multiwindow;

import android.app.Activity;
import android.app.ActivityOptions;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.DisplayMetrics;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.text.Collator;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * Windows 風デスクトップ。
 *
 * タブレットにインストールされている全アプリをデスクトップ アイコンと
 * スタート メニューに一覧表示し、タップすると Microsoft Windows のように
 * 画面上で重なり合う OS フリーフォーム ウィンドウ
 * (Samsung ポップアップ表示 / Samsung DeX / Android freeform) として起動する。
 * アプリ画面の内部に描く擬似ウィンドウではなく、各アプリは OS が管理する
 * 本物のウィンドウとして開き、ドラッグ移動・リサイズ・重ね合わせができる。
 *
 * 仕組み:
 *   - 外部アプリ: PackageManager#getLaunchIntentForPackage() +
 *     FLAG_ACTIVITY_NEW_TASK + ActivityOptions#setLaunchBounds(Rect)
 *       → フリーフォーム対応環境では指定位置・サイズのウィンドウとして開く
 *   - 内蔵ツール (メモ/電卓/時計/モニター): さらに
 *     FLAG_ACTIVITY_NEW_DOCUMENT | FLAG_ACTIVITY_MULTIPLE_TASK で
 *     同じツールを何枚でも開ける
 *   - 新しいウィンドウはカスケード (少しずつずらして) 配置
 */
public class LauncherActivity extends Activity {

    private static final String PREFS = "bada_multiwindow";
    private static final String KEY_CASCADE = "cascade";
    private static final String KEY_MEMO_SEQ = "memo_seq";

    /** クラシック Windows 風カラー */
    private static final int DESKTOP_TEAL = Color.rgb(0, 128, 128);
    private static final int TASKBAR_GRAY = Color.rgb(212, 208, 200);
    private static final int MENU_BG = Color.rgb(245, 245, 245);
    private static final int MENU_SIDE = Color.rgb(0, 0, 128);

    private static class AppEntry {
        CharSequence label;
        String pkg;
        ResolveInfo ri;
        Drawable icon; // 遅延ロード
    }

    private final List<AppEntry> allApps = new ArrayList<>();
    private final List<AppEntry> filteredApps = new ArrayList<>();
    private final Handler handler = new Handler(Looper.getMainLooper());

    private GridView desktopGrid;
    private LinearLayout startMenu;
    private ListView startList;
    private EditText searchBox;
    private TextView clockText;
    private BaseAdapter desktopAdapter;
    private BaseAdapter startAdapter;

    private final SimpleDateFormat clockFmt = new SimpleDateFormat("HH:mm", Locale.JAPAN);
    private final Runnable clockTick = new Runnable() {
        @Override public void run() {
            clockText.setText(clockFmt.format(new Date()));
            handler.postDelayed(this, 15000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(DESKTOP_TEAL);

        // ---- デスクトップ (アプリ アイコンのグリッド) ----
        desktopGrid = new GridView(this);
        desktopGrid.setNumColumns(GridView.AUTO_FIT);
        desktopGrid.setColumnWidth(dp(96));
        desktopGrid.setStretchMode(GridView.STRETCH_COLUMN_WIDTH);
        desktopGrid.setVerticalSpacing(dp(8));
        desktopGrid.setPadding(dp(8), dp(8), dp(8), dp(56));
        desktopGrid.setClipToPadding(false);
        desktopAdapter = new AppAdapter(true);
        desktopGrid.setAdapter(desktopAdapter);
        desktopGrid.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) {
                hideStartMenu();
                launchApp(allApps.get(pos), true);
            }
        });
        desktopGrid.setOnItemLongClickListener(new AdapterView.OnItemLongClickListener() {
            @Override public boolean onItemLongClick(AdapterView<?> p, View v, int pos, long id) {
                hideStartMenu();
                launchApp(allApps.get(pos), false); // 長押し = 通常 (全画面) 起動
                return true;
            }
        });
        root.addView(desktopGrid, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));

        // ---- スタート メニュー (オーバーレイ) ----
        startMenu = buildStartMenu();
        FrameLayout.LayoutParams menuLp = new FrameLayout.LayoutParams(
                dp(320), dp(440), Gravity.BOTTOM | Gravity.START);
        menuLp.bottomMargin = dp(48);
        startMenu.setVisibility(View.GONE);
        root.addView(startMenu, menuLp);

        // ---- タスクバー ----
        root.addView(buildTaskbar(), new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, dp(48), Gravity.BOTTOM));

        setContentView(root);

        loadInstalledApps();
    }

    @Override
    protected void onStart() {
        super.onStart();
        clockTick.run();
    }

    @Override
    protected void onStop() {
        super.onStop();
        handler.removeCallbacks(clockTick);
    }

    @Override
    public void onBackPressed() {
        if (startMenu.getVisibility() == View.VISIBLE) {
            hideStartMenu();
            return;
        }
        super.onBackPressed();
    }

    // ------------------------------------------------------------------ UI 構築

    private LinearLayout buildTaskbar() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setBackgroundColor(TASKBAR_GRAY);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(4), dp(4), dp(8), dp(4));
        bar.setElevation(dp(8));

        TextView start = new TextView(this);
        start.setText("⊞ スタート");
        start.setTypeface(Typeface.DEFAULT_BOLD);
        start.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        start.setTextColor(Color.BLACK);
        start.setBackgroundColor(Color.rgb(192, 192, 192));
        start.setGravity(Gravity.CENTER);
        start.setPadding(dp(12), 0, dp(12), 0);
        start.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { toggleStartMenu(); }
        });
        bar.addView(start, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.MATCH_PARENT));

        bar.addView(taskbarDivider());

        // 内蔵ツールのクイック起動
        addQuickTool(bar, "📝", "メモ", MemoActivity.class, 360, 420);
        addQuickTool(bar, "🧮", "電卓", CalcActivity.class, 300, 440);
        addQuickTool(bar, "🕐", "時計", ClockActivity.class, 340, 200);
        addQuickTool(bar, "📊", "空き容量", MonitorActivity.class, 360, 320);
        addQuickTool(bar, "🗄", "キャビネット", CabinetActivity.class, 400, 580);

        // スペーサー
        View spacer = new View(this);
        bar.addView(spacer, new LinearLayout.LayoutParams(0,
                LinearLayout.LayoutParams.MATCH_PARENT, 1f));

        clockText = new TextView(this);
        clockText.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        clockText.setTextColor(Color.BLACK);
        clockText.setGravity(Gravity.CENTER);
        clockText.setBackgroundColor(Color.rgb(224, 222, 216));
        clockText.setPadding(dp(10), 0, dp(10), 0);
        bar.addView(clockText, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.MATCH_PARENT));

        return bar;
    }

    private View taskbarDivider() {
        View d = new View(this);
        d.setBackgroundColor(Color.rgb(160, 160, 160));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                dp(1), LinearLayout.LayoutParams.MATCH_PARENT);
        lp.setMargins(dp(6), dp(4), dp(6), dp(4));
        d.setLayoutParams(lp);
        return d;
    }

    private void addQuickTool(LinearLayout bar, String emoji, final String name,
                              final Class<?> cls, final int wDp, final int hDp) {
        TextView b = new TextView(this);
        b.setText(emoji);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        b.setGravity(Gravity.CENTER);
        b.setPadding(dp(8), 0, dp(8), 0);
        b.setContentDescription(name);
        b.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                hideStartMenu();
                openToolWindow(cls, wDp, hDp);
            }
        });
        bar.addView(b, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.MATCH_PARENT));
    }

    private LinearLayout buildStartMenu() {
        LinearLayout menu = new LinearLayout(this);
        menu.setOrientation(LinearLayout.VERTICAL);
        menu.setBackgroundColor(MENU_BG);
        menu.setElevation(dp(16));

        TextView header = new TextView(this);
        header.setText(" Bada MultiWindow");
        header.setTypeface(Typeface.DEFAULT_BOLD);
        header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16);
        header.setTextColor(Color.WHITE);
        header.setBackgroundColor(MENU_SIDE);
        header.setPadding(dp(10), dp(8), dp(10), dp(8));
        menu.addView(header);

        searchBox = new EditText(this);
        searchBox.setHint("🔍 アプリを検索…");
        searchBox.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        searchBox.setSingleLine(true);
        searchBox.setPadding(dp(10), dp(8), dp(10), dp(8));
        searchBox.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void afterTextChanged(Editable s) { filterApps(s.toString()); }
        });
        menu.addView(searchBox);

        startList = new ListView(this);
        startList.setDivider(null);
        startAdapter = new AppAdapter(false);
        startList.setAdapter(startAdapter);
        startList.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override public void onItemClick(AdapterView<?> p, View v, int pos, long id) {
                hideStartMenu();
                launchApp(filteredApps.get(pos), true);
            }
        });
        startList.setOnItemLongClickListener(new AdapterView.OnItemLongClickListener() {
            @Override public boolean onItemLongClick(AdapterView<?> p, View v, int pos, long id) {
                hideStartMenu();
                launchApp(filteredApps.get(pos), false);
                return true;
            }
        });
        menu.addView(startList, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        TextView tip = new TextView(this);
        boolean freeform = getPackageManager().hasSystemFeature(
                PackageManager.FEATURE_FREEFORM_WINDOW_MANAGEMENT);
        tip.setText(freeform
                ? "タップ = ウィンドウで開く / 長押し = 全画面で開く"
                : "タップ = ウィンドウ起動を試行 / 長押し = 全画面\n"
                + "Samsung: 最近のアプリ →「ポップアップ表示で開く」でも\n"
                + "ウィンドウ化できます");
        tip.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
        tip.setTextColor(Color.rgb(90, 100, 115));
        tip.setBackgroundColor(Color.rgb(232, 232, 232));
        tip.setPadding(dp(10), dp(6), dp(10), dp(6));
        menu.addView(tip);

        return menu;
    }

    private void toggleStartMenu() {
        if (startMenu.getVisibility() == View.VISIBLE) {
            hideStartMenu();
        } else {
            startMenu.setVisibility(View.VISIBLE);
            searchBox.setText("");
        }
    }

    private void hideStartMenu() {
        startMenu.setVisibility(View.GONE);
    }

    // ------------------------------------------------------------------ アプリ一覧

    /** インストール済みアプリを背景スレッドで読み込む (低メモリ端末でも UI を止めない)。 */
    private void loadInstalledApps() {
        new Thread(new Runnable() {
            @Override public void run() {
                final PackageManager pm = getPackageManager();
                Intent main = new Intent(Intent.ACTION_MAIN);
                main.addCategory(Intent.CATEGORY_LAUNCHER);
                List<ResolveInfo> ris = pm.queryIntentActivities(main, 0);
                final List<AppEntry> loaded = new ArrayList<>();
                for (ResolveInfo ri : ris) {
                    if (getPackageName().equals(ri.activityInfo.packageName)) continue;
                    AppEntry e = new AppEntry();
                    e.ri = ri;
                    e.pkg = ri.activityInfo.packageName;
                    e.label = ri.loadLabel(pm);
                    loaded.add(e);
                }
                final Collator collator = Collator.getInstance(Locale.JAPAN);
                Collections.sort(loaded, new Comparator<AppEntry>() {
                    @Override public int compare(AppEntry a, AppEntry b) {
                        return collator.compare(String.valueOf(a.label), String.valueOf(b.label));
                    }
                });
                handler.post(new Runnable() {
                    @Override public void run() {
                        allApps.clear();
                        allApps.addAll(loaded);
                        filterApps(searchBox.getText().toString());
                        desktopAdapter.notifyDataSetChanged();
                    }
                });
            }
        }, "app-loader").start();
    }

    private void filterApps(String query) {
        filteredApps.clear();
        String q = query.trim().toLowerCase(Locale.JAPAN);
        for (AppEntry e : allApps) {
            if (q.isEmpty()
                    || String.valueOf(e.label).toLowerCase(Locale.JAPAN).contains(q)
                    || e.pkg.toLowerCase(Locale.ROOT).contains(q)) {
                filteredApps.add(e);
            }
        }
        startAdapter.notifyDataSetChanged();
    }

    /** デスクトップ (grid=true) とスタート メニュー (grid=false) 共用のアダプタ。 */
    private class AppAdapter extends BaseAdapter {
        private final boolean grid;

        AppAdapter(boolean grid) { this.grid = grid; }

        private List<AppEntry> data() { return grid ? allApps : filteredApps; }

        @Override public int getCount() { return data().size(); }
        @Override public Object getItem(int pos) { return data().get(pos); }
        @Override public long getItemId(int pos) { return pos; }

        @Override
        public View getView(int pos, View convert, ViewGroup parent) {
            LinearLayout item;
            ImageView icon;
            TextView label;
            if (convert instanceof LinearLayout) {
                item = (LinearLayout) convert;
                icon = (ImageView) item.getChildAt(0);
                label = (TextView) item.getChildAt(1);
            } else {
                item = new LinearLayout(LauncherActivity.this);
                icon = new ImageView(LauncherActivity.this);
                label = new TextView(LauncherActivity.this);
                if (grid) {
                    item.setOrientation(LinearLayout.VERTICAL);
                    item.setGravity(Gravity.CENTER_HORIZONTAL);
                    item.setPadding(dp(4), dp(6), dp(4), dp(6));
                    item.addView(icon, new LinearLayout.LayoutParams(dp(48), dp(48)));
                    label.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11);
                    label.setTextColor(Color.WHITE);
                    label.setShadowLayer(3f, 1f, 1f, Color.BLACK);
                    label.setGravity(Gravity.CENTER_HORIZONTAL);
                    label.setMaxLines(2);
                    LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.MATCH_PARENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT);
                    lp.topMargin = dp(4);
                    item.addView(label, lp);
                } else {
                    item.setOrientation(LinearLayout.HORIZONTAL);
                    item.setGravity(Gravity.CENTER_VERTICAL);
                    item.setPadding(dp(10), dp(6), dp(10), dp(6));
                    item.addView(icon, new LinearLayout.LayoutParams(dp(32), dp(32)));
                    label.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
                    label.setTextColor(Color.BLACK);
                    label.setSingleLine(true);
                    LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                            LinearLayout.LayoutParams.WRAP_CONTENT,
                            LinearLayout.LayoutParams.WRAP_CONTENT);
                    lp.leftMargin = dp(10);
                    item.addView(label, lp);
                }
            }
            AppEntry e = data().get(pos);
            if (e.icon == null) e.icon = e.ri.loadIcon(getPackageManager());
            icon.setImageDrawable(e.icon);
            label.setText(e.label);
            return item;
        }
    }

    // ------------------------------------------------------------------ ウィンドウ起動

    /**
     * インストール済みアプリを起動する。
     * freeform=true ならフリーフォーム ウィンドウ (カスケード位置) として開くことを
     * 試み、非対応環境では通常起動にフォールバックする。
     */
    private void launchApp(AppEntry e, boolean freeform) {
        Intent intent = getPackageManager().getLaunchIntentForPackage(e.pkg);
        if (intent == null) {
            Toast.makeText(this, e.label + " は起動できません", Toast.LENGTH_SHORT).show();
            return;
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        if (freeform) {
            try {
                ActivityOptions opts = ActivityOptions.makeBasic();
                opts.setLaunchBounds(nextCascadeBounds(520, 640));
                startActivity(intent, opts.toBundle());
                return;
            } catch (Exception ignored) {
                // launch bounds 非対応 → 通常起動へフォールバック
            }
        }
        try {
            startActivity(intent);
        } catch (Exception ex) {
            Toast.makeText(this, "起動できませんでした: " + ex.getMessage(),
                    Toast.LENGTH_SHORT).show();
        }
    }

    /** 内蔵ツールを独立フリーフォーム ウィンドウとして開く (マルチインスタンス)。 */
    private void openToolWindow(Class<?> activity, int widthDp, int heightDp) {
        Intent intent = new Intent(this, activity);
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

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
