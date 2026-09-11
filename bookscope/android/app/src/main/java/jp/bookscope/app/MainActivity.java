package jp.bookscope.app;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.webkit.WebViewAssetLoader;

/**
 * bookscope の Web UI (assets/www) を WebView で表示する。
 * WebViewAssetLoader 経由の https://appassets.androidplatform.net は
 * セキュアコンテキスト扱いになるため、カメラ (getUserMedia) が使える。
 */
public class MainActivity extends Activity {

    private static final int REQ_CAMERA = 1;
    private static final int REQ_FILE_CHOOSER = 2;
    private static final String START_URL =
            "https://appassets.androidplatform.net/assets/www/index.html";

    private WebView webView;
    private PermissionRequest pendingPermissionRequest;
    private ValueCallback<Uri[]> pendingFileCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true); // 蔵書データを localStorage に保存する
        settings.setMediaPlaybackRequiresUserGesture(false);

        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(
                    WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> {
                    boolean wantsCamera = false;
                    for (String resource : request.getResources()) {
                        if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) {
                            wantsCamera = true;
                        }
                    }
                    if (!wantsCamera) {
                        request.deny();
                        return;
                    }
                    if (checkSelfPermission(Manifest.permission.CAMERA)
                            == PackageManager.PERMISSION_GRANTED) {
                        request.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
                    } else {
                        // Android の実行時権限を先に取ってから WebView 側へ許可を返す
                        pendingPermissionRequest = request;
                        requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAMERA);
                    }
                });
            }

            // <input type="file"> (表紙画像のギャラリー選択) は WebView では
            // これを実装しないと何も起きない
            @Override
            public boolean onShowFileChooser(WebView view,
                    ValueCallback<Uri[]> filePathCallback,
                    FileChooserParams fileChooserParams) {
                if (pendingFileCallback != null) {
                    pendingFileCallback.onReceiveValue(null);
                }
                pendingFileCallback = filePathCallback;
                try {
                    startActivityForResult(
                            fileChooserParams.createIntent(), REQ_FILE_CHOOSER);
                } catch (Exception e) {
                    pendingFileCallback = null;
                    filePathCallback.onReceiveValue(null);
                    return false;
                }
                return true;
            }
        });

        webView.loadUrl(START_URL);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_FILE_CHOOSER && pendingFileCallback != null) {
            pendingFileCallback.onReceiveValue(
                    WebChromeClient.FileChooserParams.parseResult(resultCode, data));
            pendingFileCallback = null;
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != REQ_CAMERA || pendingPermissionRequest == null) {
            return;
        }
        if (grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            pendingPermissionRequest.grant(
                    new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
        } else {
            pendingPermissionRequest.deny();
        }
        pendingPermissionRequest = null;
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
