package com.bada.silenttalk;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;

/**
 * Reads the device sensors that Silent Talk uses as silent input / context:
 * <ul>
 *   <li><b>Proximity (赤外線)</b> — phones expose an infrared proximity sensor;
 *       covering it is a hands-free "select / click" trigger.</li>
 *   <li><b>Ambient temperature (温度計)</b> — feeds the thermal-network kernel
 *       in {@link ThermalManifold} (absent on most phones → treated as neutral).</li>
 *   <li><b>Accelerometer tilt</b> — a no-camera fallback pointer (tilt to steer
 *       the gaze cursor).</li>
 * </ul>
 */
final class SensorHub implements SensorEventListener {

    interface Listener {
        void onTilt(float dx, float dy);
        void onProximity(boolean near);
        void onTemperature(float celsius);
    }

    private final SensorManager sm;
    private final Sensor accel, proximity, temperature;
    private final Listener listener;

    private volatile boolean proximityNear = false;
    private volatile float lastTempC = Float.NaN;

    SensorHub(Context ctx, Listener listener) {
        this.listener = listener;
        sm = (SensorManager) ctx.getSystemService(Context.SENSOR_SERVICE);
        accel = sm != null ? sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER) : null;
        proximity = sm != null ? sm.getDefaultSensor(Sensor.TYPE_PROXIMITY) : null;
        temperature = sm != null ? sm.getDefaultSensor(Sensor.TYPE_AMBIENT_TEMPERATURE) : null;
    }

    void start() {
        if (sm == null) return;
        if (accel != null) sm.registerListener(this, accel, SensorManager.SENSOR_DELAY_GAME);
        if (proximity != null) sm.registerListener(this, proximity, SensorManager.SENSOR_DELAY_NORMAL);
        if (temperature != null) sm.registerListener(this, temperature, SensorManager.SENSOR_DELAY_NORMAL);
    }

    void stop() {
        if (sm != null) sm.unregisterListener(this);
    }

    boolean isProximityNear() { return proximityNear; }
    float temperatureC() { return lastTempC; }

    @Override
    public void onSensorChanged(SensorEvent e) {
        switch (e.sensor.getType()) {
            case Sensor.TYPE_ACCELEROMETER: {
                // gravity components -> small normalized steering vector
                float gx = e.values[0], gy = e.values[1];
                float dead = 1.2f;                       // ignore small jitter
                float dx = Math.abs(gx) > dead ? -clamp(gx / 9.81f) : 0f;
                float dy = Math.abs(gy - 0f) > dead ? clamp((gy - 4.0f) / 9.81f) : 0f;
                listener.onTilt(dx, dy);
                break;
            }
            case Sensor.TYPE_PROXIMITY: {
                float max = e.sensor.getMaximumRange();
                boolean near = e.values[0] < Math.min(max, 5.0f);
                if (near != proximityNear) {
                    proximityNear = near;
                    listener.onProximity(near);
                }
                break;
            }
            case Sensor.TYPE_AMBIENT_TEMPERATURE: {
                lastTempC = e.values[0];
                listener.onTemperature(lastTempC);
                break;
            }
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) { }

    private static float clamp(float v) {
        return v < -1f ? -1f : (v > 1f ? 1f : v);
    }
}
