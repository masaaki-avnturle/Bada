package io.github.masaaki_avnturle.badafiles;

import android.annotation.TargetApi;
import android.app.Activity;
import android.app.DownloadManager;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.provider.OpenableColumns;
import android.util.Base64;

import org.apache.cordova.CallbackContext;
import org.apache.cordova.CordovaPlugin;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Bada アプリのファイル取り込み・保存。
 * WebView の &lt;input type="file"&gt; は accept に拡張子 (".pdf" など) があると
 * ファイル選択画面が開かない端末があるため、Storage Access Framework を直接呼ぶ。
 */
public class BadaFiles extends CordovaPlugin {
    private static final int REQ_OPEN = 7101;
    private static final int REQ_SAVE = 7102;

    private CallbackContext pending;
    private byte[] pendingData;

    @Override
    public boolean execute(String action, JSONArray args, CallbackContext cb) throws JSONException {
        if ("open".equals(action)) {
            Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            i.addCategory(Intent.CATEGORY_OPENABLE);
            i.setType(args.optString(0, "*/*"));
            start(i, REQ_OPEN, cb, null);
            return true;
        }
        if ("saveAs".equals(action)) {
            Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            i.addCategory(Intent.CATEGORY_OPENABLE);
            i.setType(args.getString(1));
            i.putExtra(Intent.EXTRA_TITLE, args.getString(0));
            start(i, REQ_SAVE, cb, Base64.decode(args.getString(2), Base64.DEFAULT));
            return true;
        }
        if ("saveDownloads".equals(action)) {
            final String name = args.getString(0), mime = args.getString(1);
            final byte[] data = Base64.decode(args.getString(2), Base64.DEFAULT);
            if (Build.VERSION.SDK_INT < 29) { cb.error("legacy"); return true; }
            cordova.getThreadPool().execute(() -> {
                try { cb.success(saveToDownloads(name, mime, data)); } catch (Exception e) { cb.error(e.toString()); }
            });
            return true;
        }
        if ("showDownloads".equals(action)) {
            try {
                Intent i = new Intent(DownloadManager.ACTION_VIEW_DOWNLOADS);
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                cordova.getActivity().startActivity(i);
                cb.success();
            } catch (Exception e) { cb.error(e.toString()); }
            return true;
        }
        return false;
    }

    private void start(Intent i, int req, CallbackContext cb, byte[] data) {
        if (pending != null) pending.error("cancel");
        pending = cb;
        pendingData = data;
        try {
            cordova.startActivityForResult(this, i, req);
        } catch (Exception e) {
            pending = null;
            pendingData = null;
            cb.error("ファイル画面を開けません: " + e);
        }
    }

    @Override
    public void onActivityResult(int req, int res, Intent intent) {
        final CallbackContext cb = pending;
        final byte[] data = pendingData;
        pending = null;
        pendingData = null;
        if (cb == null) return;
        if (res != Activity.RESULT_OK || intent == null || intent.getData() == null) { cb.error("cancel"); return; }
        final Uri uri = intent.getData();
        cordova.getThreadPool().execute(() -> {
            try {
                ContentResolver cr = cordova.getActivity().getContentResolver();
                if (req == REQ_OPEN) {
                    byte[] bytes;
                    try (InputStream in = cr.openInputStream(uri)) { bytes = readAll(in); }
                    JSONObject o = new JSONObject();
                    o.put("name", displayName(cr, uri));
                    o.put("size", bytes.length);
                    o.put("data", Base64.encodeToString(bytes, Base64.NO_WRAP));
                    cb.success(o);
                } else {
                    try (OutputStream out = cr.openOutputStream(uri)) { out.write(data); }
                    cb.success(displayName(cr, uri));
                }
            } catch (Exception e) {
                cb.error(e.toString());
            }
        });
    }

    @TargetApi(29)
    private String saveToDownloads(String name, String mime, byte[] data) throws Exception {
        ContentResolver cr = cordova.getActivity().getContentResolver();
        ContentValues v = new ContentValues();
        v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
        v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
        v.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
        v.put(MediaStore.MediaColumns.IS_PENDING, 1);
        Uri uri = cr.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
        if (uri == null) throw new Exception("ダウンロード フォルダに作成できません");
        try (OutputStream out = cr.openOutputStream(uri)) { out.write(data); }
        v.clear();
        v.put(MediaStore.MediaColumns.IS_PENDING, 0);
        cr.update(uri, v, null, null);
        return Environment.DIRECTORY_DOWNLOADS + "/" + displayName(cr, uri);
    }

    private static String displayName(ContentResolver cr, Uri uri) {
        try (Cursor c = cr.query(uri, new String[] { OpenableColumns.DISPLAY_NAME }, null, null, null)) {
            if (c != null && c.moveToFirst() && !c.isNull(0)) return c.getString(0);
        } catch (Exception e) { /* 名前が取れない提供元もある */ }
        String s = uri.getLastPathSegment();
        return s == null ? "file" : s.substring(s.lastIndexOf('/') + 1);
    }

    private static byte[] readAll(InputStream in) throws Exception {
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        byte[] buf = new byte[65536];
        int n;
        while ((n = in.read(buf)) > 0) b.write(buf, 0, n);
        return b.toByteArray();
    }
}
