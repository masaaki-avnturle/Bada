package com.bada.xp;

import android.app.Activity;
import android.os.Bundle;
import android.view.KeyEvent;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;

/**
 * Bada XP — ChatGPT 分派. A thin WebView shell around the bundled PWA in
 * assets/www. The whole app (engine, version ladder, optional real-LLM) is the
 * HTML/JS; this Activity just hosts it and wires the Android back button.
 *
 * Uses a plain framework Activity (no AndroidX) so the build has zero external
 * dependencies — small APK, no transitive Kotlin stdlib conflicts.
 */
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // localStorage (version + API key)
        s.setMediaPlaybackRequiresUserGesture(false);
        web.setWebChromeClient(new WebChromeClient());
        web.loadUrl("file:///android_asset/www/index.html");

        setContentView(web);
    }

    // Android back button navigates the WebView history first.
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && web != null && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
}
