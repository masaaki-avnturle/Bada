package io.bada.omega.iqtelomere;

import android.app.Activity;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;

/**
 * Bada 赤外線IQ・テロメア分裂測定 — a single-Activity WebView app. The whole IQ
 * pipeline runs on-device as JavaScript (assets/iq_engine.js). If the tablet has
 * an ambient-temperature sensor it is exposed to the page via AndroidThermal so
 * the 温度計 reading is real; otherwise the bundled sample frame is used.
 */
public class MainActivity extends Activity {

    private volatile float ambientC = Float.NaN;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        registerThermometer();

        WebView web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        web.addJavascriptInterface(new ThermalBridge(), "AndroidThermal");
        web.loadUrl("file:///android_asset/index.html");
        setContentView(web);
    }

    /** Exposed to JS as AndroidThermal.ambientC(). */
    private class ThermalBridge {
        @JavascriptInterface
        public float ambientC() {
            return ambientC;
        }
    }

    private void registerThermometer() {
        SensorManager sm = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        if (sm == null) return;
        Sensor temp = sm.getDefaultSensor(Sensor.TYPE_AMBIENT_TEMPERATURE);
        if (temp == null) return;
        sm.registerListener(new SensorEventListener() {
            @Override public void onSensorChanged(SensorEvent e) { ambientC = e.values[0]; }
            @Override public void onAccuracyChanged(Sensor sensor, int accuracy) { }
        }, temp, SensorManager.SENSOR_DELAY_NORMAL);
    }
}
