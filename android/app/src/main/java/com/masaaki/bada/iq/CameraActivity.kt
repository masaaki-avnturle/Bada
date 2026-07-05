package com.masaaki.bada.iq

import android.Manifest
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

/**
 * 赤外線カメラ + 温度計モード（タブレット機材で実測）。
 *
 * タブレットのカメラ映像の中心領域（対象者の額）から赤外線体表温の近似値を
 * リアルタイムに算出し（RGB カメラを IR/サーマルの近似として使用）、端末の温度計
 * センサー（TYPE_AMBIENT_TEMPERATURE）で環境温度を取得します。得られた 2 値を、
 * Bada 言語エンジンのサーマル評価／大脳基底核推定にそのまま渡します。
 *
 * ※ 消費者向けタブレットの多くは放射計測型サーマルカメラを備えないため、通常カメラの
 *    輝度・赤成分から体表温を近似する教育的プロキシです。医療計測ではありません。
 */
class CameraActivity : AppCompatActivity(), SensorEventListener {

    @Volatile private var currentIrProxy: Double = 33.0
    @Volatile private var currentTemp: Double = 23.0
    private var tempFromSensor = false

    private lateinit var previewView: PreviewView
    private lateinit var status: TextView
    private lateinit var inIr: EditText
    private lateinit var inTemp: EditText
    private lateinit var result: TextView
    private lateinit var analysisExecutor: ExecutorService

    private lateinit var sm: SensorManager
    private var tempSensor: Sensor? = null

    private val requestCamera =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) startCamera()
            else status.text = getString(R.string.camera_denied)
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_camera)
        BadaAssets.ensureLoaded(this)

        previewView = findViewById(R.id.previewView)
        status = findViewById(R.id.txtCameraStatus)
        inIr = findViewById(R.id.inCamIr)
        inTemp = findViewById(R.id.inCamTemp)
        result = findViewById(R.id.txtCameraResult)
        analysisExecutor = Executors.newSingleThreadExecutor()

        sm = getSystemService(SENSOR_SERVICE) as SensorManager
        tempSensor = sm.getDefaultSensor(Sensor.TYPE_AMBIENT_TEMPERATURE)

        inIr.setText(String.format(Locale.US, "%.1f", currentIrProxy))
        inTemp.setText(String.format(Locale.US, "%.1f", currentTemp))

        findViewById<Button>(R.id.btnCapture).setOnClickListener { capture() }
        findViewById<Button>(R.id.btnCamAssess).setOnClickListener { runAssessment(false) }
        findViewById<Button>(R.id.btnCamDerived).setOnClickListener { runAssessment(true) }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
            == PackageManager.PERMISSION_GRANTED
        ) {
            startCamera()
        } else {
            requestCamera.launch(Manifest.permission.CAMERA)
        }
    }

    private fun startCamera() {
        val future = ProcessCameraProvider.getInstance(this)
        future.addListener({
            val provider = future.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(previewView.surfaceProvider)
            }
            val analysis = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
                .build()
            analysis.setAnalyzer(analysisExecutor) { image -> analyze(image) }
            try {
                provider.unbindAll()
                provider.bindToLifecycle(
                    this, CameraSelector.DEFAULT_BACK_CAMERA, preview, analysis
                )
                status.text = getString(R.string.camera_scanning)
            } catch (e: Exception) {
                status.text = "カメラ起動エラー: ${e.message}"
            }
        }, ContextCompat.getMainExecutor(this))
    }

    // Mean red-channel warmth over the central ROI → an IR body-surface proxy
    // mapped into [30, 37] °C.
    private fun analyze(image: ImageProxy) {
        try {
            val plane = image.planes[0]
            val buf = plane.buffer
            val rowStride = plane.rowStride
            val pixStride = plane.pixelStride
            val w = image.width
            val h = image.height
            val x0 = (w * 0.30).toInt(); val x1 = (w * 0.70).toInt()
            val y0 = (h * 0.30).toInt(); val y1 = (h * 0.70).toInt()
            var sum = 0L; var count = 0
            var y = y0
            while (y < y1) {
                var x = x0
                while (x < x1) {
                    val idx = y * rowStride + x * pixStride
                    if (idx in 0 until buf.limit()) {
                        sum += (buf.get(idx).toInt() and 0xFF) // R channel
                        count++
                    }
                    x += 8
                }
                y += 8
            }
            val meanR = if (count > 0) sum.toDouble() / count else 0.0
            currentIrProxy = 30.0 + (meanR / 255.0) * 7.0
            runOnUiThread {
                status.text = getString(
                    R.string.camera_live,
                    currentIrProxy,
                    if (tempFromSensor) currentTemp else currentTemp
                )
            }
        } finally {
            image.close()
        }
    }

    private fun capture() {
        inIr.setText(String.format(Locale.US, "%.1f", currentIrProxy))
        inTemp.setText(String.format(Locale.US, "%.1f", currentTemp))
        Toast.makeText(this, getString(R.string.camera_captured), Toast.LENGTH_SHORT).show()
    }

    private fun runAssessment(derived: Boolean) {
        val ir = inIr.text.toString().trim().toDoubleOrNull()
        val temp = inTemp.text.toString().trim().toDoubleOrNull()
        if (ir == null || temp == null) {
            result.text = getString(R.string.err_thermal_input)
            return
        }
        result.text = try {
            val a = if (derived) IqEngine.assessThermalDerived(ir, temp)
            else IqEngine.assessThermal(ir, temp, id = "CAMERA")
            IqEngine.report(a)
        } catch (ex: Exception) {
            "エラー: ${ex.message}"
        }
    }

    override fun onResume() {
        super.onResume()
        tempSensor?.let { sm.registerListener(this, it, SensorManager.SENSOR_DELAY_UI) }
    }

    override fun onPause() {
        super.onPause()
        sm.unregisterListener(this)
    }

    override fun onDestroy() {
        super.onDestroy()
        if (::analysisExecutor.isInitialized) analysisExecutor.shutdown()
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type == Sensor.TYPE_AMBIENT_TEMPERATURE) {
            currentTemp = event.values[0].toDouble()
            tempFromSensor = true
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
}
