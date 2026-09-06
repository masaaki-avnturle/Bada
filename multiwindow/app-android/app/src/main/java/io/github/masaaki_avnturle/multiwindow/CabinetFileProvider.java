package io.github.masaaki_avnturle.multiwindow;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import android.webkit.MimeTypeMap;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Locale;

/**
 * ファイルキャビネットが選んだファイルを、閲覧アプリへ content:// URI で
 * 読み取り専用提供する極小 ContentProvider (依存ゼロ方針のため
 * androidx FileProvider は使わない)。
 *
 * exported=false + FLAG_GRANT_READ_URI_PERMISSION 前提: URI を渡した
 * インテントの受け取りアプリだけが一時的に読み取れる。
 */
public class CabinetFileProvider extends ContentProvider {

    public static final String AUTHORITY =
            "io.github.masaaki_avnturle.multiwindow.files";

    public static Uri uriFor(File f) {
        return new Uri.Builder().scheme("content").authority(AUTHORITY)
                .path(f.getAbsolutePath()).build();
    }

    public static String mimeFor(String name) {
        int dot = name.lastIndexOf('.');
        if (dot >= 0 && dot < name.length() - 1) {
            String ext = name.substring(dot + 1).toLowerCase(Locale.ROOT);
            String mime = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext);
            if (mime != null) return mime;
        }
        return "application/octet-stream";
    }

    private static File fileFor(Uri uri) {
        String p = uri.getPath();
        return p == null ? null : new File(p);
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        File f = fileFor(uri);
        if (f == null || !f.isFile()) throw new FileNotFoundException(String.valueOf(uri));
        return ParcelFileDescriptor.open(f, ParcelFileDescriptor.MODE_READ_ONLY);
    }

    @Override
    public String getType(Uri uri) {
        return mimeFor(uri.getLastPathSegment() == null ? "" : uri.getLastPathSegment());
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection,
                        String[] selectionArgs, String sortOrder) {
        File f = fileFor(uri);
        if (f == null) return null;
        if (projection == null) {
            projection = new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE};
        }
        MatrixCursor c = new MatrixCursor(projection, 1);
        Object[] row = new Object[projection.length];
        for (int i = 0; i < projection.length; i++) {
            if (OpenableColumns.DISPLAY_NAME.equals(projection[i])) row[i] = f.getName();
            else if (OpenableColumns.SIZE.equals(projection[i])) row[i] = f.length();
        }
        c.addRow(row);
        return c;
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        return null; // 読み取り専用
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        return 0; // 読み取り専用
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        return 0; // 読み取り専用
    }
}
