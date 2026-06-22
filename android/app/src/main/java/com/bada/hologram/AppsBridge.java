package com.bada.hologram;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.util.Base64;
import android.webkit.JavascriptInterface;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 * Bridge exposing the device's installed applications to the Freeform desktop's
 * Start menu.  The WebView calls AndroidApps.listApps() to populate the menu and
 * AndroidApps.launchApp(pkg) to start an installed app.  (Enumerating installed
 * apps is device state, so it is surfaced natively here, not from Bada — the
 * window-manager geometry and the bundled catalog still come from Bada.)
 */
public class AppsBridge {

    private final Context ctx;

    public AppsBridge(Context ctx) {
        this.ctx = ctx;
    }

    /** All launchable installed apps as JSON: [{label, pkg, icon}, ...]. */
    @JavascriptInterface
    public String listApps() {
        PackageManager pm = ctx.getPackageManager();
        Intent main = new Intent(Intent.ACTION_MAIN, null);
        main.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> ris = pm.queryIntentActivities(main, 0);
        Collections.sort(ris, new Comparator<ResolveInfo>() {
            @Override
            public int compare(ResolveInfo a, ResolveInfo b) {
                return a.loadLabel(pm).toString()
                        .compareToIgnoreCase(b.loadLabel(pm).toString());
            }
        });
        JSONArray arr = new JSONArray();
        for (ResolveInfo ri : ris) {
            try {
                JSONObject o = new JSONObject();
                o.put("label", ri.loadLabel(pm).toString());
                o.put("pkg", ri.activityInfo.packageName);
                o.put("icon", iconDataUri(ri.loadIcon(pm)));
                arr.put(o);
            } catch (Exception ignored) {
            }
        }
        return arr.toString();
    }

    /** Launch an installed app by package name. */
    @JavascriptInterface
    public boolean launchApp(String pkg) {
        Intent i = ctx.getPackageManager().getLaunchIntentForPackage(pkg);
        if (i == null) {
            return false;
        }
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        ctx.startActivity(i);
        return true;
    }

    private String iconDataUri(Drawable d) {
        int s = 96;
        Bitmap bmp = Bitmap.createBitmap(s, s, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(bmp);
        d.setBounds(0, 0, s, s);
        d.draw(c);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.PNG, 100, bos);
        bmp.recycle();
        return "data:image/png;base64,"
                + Base64.encodeToString(bos.toByteArray(), Base64.NO_WRAP);
    }
}
