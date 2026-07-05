package com.masaaki.bada.iq

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import java.util.Locale

/**
 * 赤外線センサー + 温度計モード。
 *
 * 端末の温度計（TYPE_AMBIENT_TEMPERATURE）と赤外線近接センサー
 * （TYPE_PROXIMITY, IR ベース）を読み取り、赤外線体表温と環境温度から、
 * ガンマ関数の大域的部分積分多様体を通して IQ推定・ベイズ推定・ミラー統計・
 * ウィスパード判定を行う。センサーが無い端末では手動入力にフォールバックする。
 */
class ThermalActivity : AppCompatActivity(), SensorEventListener {

    private lateinit var sm: SensorManager
    private var tempSensor: Sensor? = null
    private var proximity: Sensor? = null

    private lateinit var inIr: EditText
    private lateinit var inTemp: EditText
    private lateinit var status: TextView
    private lateinit var result: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_thermal)
        BadaAssets.ensureLoaded(this)   // load the .bada engine library

        inIr = findViewById(R.id.inIr)
        inTemp = findViewById(R.id.inTemp)
        status = findViewById(R.id.txtSensorStatus)
        result = findViewById(R.id.txtThermalResult)

        sm = getSystemService(SENSOR_SERVICE) as SensorManager
        tempSensor = sm.getDefaultSensor(Sensor.TYPE_AMBIENT_TEMPERATURE)
        proximity = sm.getDefaultSensor(Sensor.TYPE_PROXIMITY)

        findViewById<Button>(R.id.btnReadSensors).setOnClickListener { readSensors() }
        findViewById<Button>(R.id.btnThermalAssess).setOnClickListener { runAssessment() }
        findViewById<Button>(R.id.btnThermalDemo).setOnClickListener { fillDemo() }

        val avail = buildString {
            append(if (tempSensor != null) "温度計センサー: 有" else "温度計センサー: 無(手動)")
            append(" / ")
            append(if (proximity != null) "赤外線近接センサー: 有" else "赤外線近接センサー: 無")
        }
        status.text = avail
    }

    private fun readSensors() {
        var registered = false
        tempSensor?.let {
            sm.registerListener(this, it, SensorManager.SENSOR_DELAY_UI); registered = true
        }
        proximity?.let {
            sm.registerListener(this, it, SensorManager.SENSOR_DELAY_UI); registered = true
        }
        if (!registered) {
            Toast.makeText(
                this, "利用可能なセンサーがありません。手動入力してください。", Toast.LENGTH_SHORT
            ).show()
        } else {
            status.text = "センサー取得中… 端末を対象者の額に近づけてください。"
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_AMBIENT_TEMPERATURE -> {
                val c = event.values[0]
                inTemp.setText(String.format(Locale.US, "%.2f", c))
                status.text = "温度計取得: ${String.format(Locale.US, "%.2f", c)} ℃"
                sm.unregisterListener(this, tempSensor)
            }
            Sensor.TYPE_PROXIMITY -> {
                val near = event.values[0] < (proximity?.maximumRange ?: 5f)
                status.append(
                    if (near) "  赤外線(近接): 対象検知" else "  赤外線(近接): 未検知"
                )
                sm.unregisterListener(this, proximity)
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onPause() {
        super.onPause()
        sm.unregisterListener(this)
    }

    private fun fillDemo() {
        val (ir, temp) = IqEngine.demoThermal()
        inIr.setText(ir.toString())
        inTemp.setText(temp.toString())
        runAssessment()
    }

    private fun runAssessment() {
        val ir = inIr.text.toString().trim().toDoubleOrNull()
        val temp = inTemp.text.toString().trim().toDoubleOrNull()
        if (ir == null || temp == null) {
            result.text = getString(R.string.err_thermal_input)
            return
        }
        result.text = try {
            IqEngine.report(IqEngine.assessThermal(ir, temp, id = "THERMAL"))
        } catch (ex: Exception) {
            "エラー: ${ex.message}"
        }
    }
}
