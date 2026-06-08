package com.bada.biofeedback.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.navigation.NavController
import com.bada.biofeedback.sensor.PpgHeartRate
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner
import com.bada.biofeedback.ui.ScreenHeader
import com.bada.biofeedback.ui.SectionCard
import java.util.concurrent.Executors
import kotlin.math.exp

@Composable
fun EcgScreen(nav: NavController) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var t by remember { mutableFloatStateOf(0f) }
    var bpm by remember { mutableIntStateOf(72) }
    var ppgEnabled by remember { mutableStateOf(false) }
    var hasCamPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    val ppgTrace = remember { mutableStateListOf<Float>() }

    val permLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasCamPermission = granted
        if (!granted) ppgEnabled = false
    }

    LaunchedEffect(Unit) {
        val start = withFrameNanos { it }
        while (true) {
            val now = withFrameNanos { it }
            t = (now - start) / 1_000_000_000f
        }
    }

    // CameraX PPG binding lifecycle
    DisposableEffect(ppgEnabled, hasCamPermission) {
        var provider: ProcessCameraProvider? = null
        val executor = Executors.newSingleThreadExecutor()
        if (ppgEnabled && hasCamPermission) {
            val future = ProcessCameraProvider.getInstance(context)
            future.addListener({
                provider = future.get()
                val analysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()
                analysis.setAnalyzer(
                    executor,
                    PpgHeartRate(
                        onSample = { v ->
                            ppgTrace.add(v)
                            if (ppgTrace.size > 256) ppgTrace.removeAt(0)
                        },
                        onBpm = { b -> bpm = b }
                    )
                )
                try {
                    provider?.unbindAll()
                    val cam = provider?.bindToLifecycle(
                        lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, analysis
                    )
                    // enable torch so the fingertip is lit for PPG
                    cam?.cameraControl?.enableTorch(true)
                } catch (_: Exception) { }
            }, ContextCompat.getMainExecutor(context))
        }
        onDispose {
            provider?.unbindAll()
            executor.shutdown()
        }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("心電図 (ECG) + 心拍", BadaColors.Gold) { nav.popBackStack() }
        DisclaimerBanner(
            "ECG波形は合成シミュレーションです。PPG心拍は実測ですが消費者向けの目安で、" +
            "診断には使えません。胸の痛み・動悸など異常時は医療機関へ。"
        )

        SectionCard("心拍数", BadaColors.Gold) {
            Text("$bpm BPM", color = BadaColors.Gold, fontWeight = FontWeight.Bold, fontSize = 40.sp)
            Text(
                if (ppgEnabled && hasCamPermission) "PPG実測中（背面カメラに指を当ててください・ライト点灯）"
                else "シミュレーション値",
                color = BadaColors.TextDim, fontSize = 12.sp
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Switch(checked = ppgEnabled, onCheckedChange = {
                    if (it && !hasCamPermission) permLauncher.launch(Manifest.permission.CAMERA)
                    ppgEnabled = it
                })
                Text("  指で実測 (PPG)", color = BadaColors.Text, fontSize = 14.sp)
            }
        }

        SectionCard("ECG 波形 (擬似 PQRST)", BadaColors.Gold) {
            Canvas(Modifier.fillMaxWidth().height(160.dp)) {
                val samples = 360
                val path = Path()
                val beatHz = bpm / 60f
                for (i in 0 until samples) {
                    val x = size.width * i / (samples - 1f)
                    val tt = (t + i * 0.01f) * beatHz
                    val phase = tt - kotlin.math.floor(tt) // 0..1 within beat
                    val v = ecgBeat(phase)
                    val y = size.height * 0.55f - v * size.height * 0.40f
                    if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
                }
                drawPath(path, BadaColors.Gold, style = Stroke(2.5f))
            }
        }

        if (ppgEnabled && hasCamPermission) {
            SectionCard("PPG 生波形 (実測)", BadaColors.Cyan) {
                Canvas(Modifier.fillMaxWidth().height(120.dp)) {
                    if (ppgTrace.size > 2) {
                        val path = Path()
                        val mn = ppgTrace.min()
                        val mx = ppgTrace.max()
                        val range = (mx - mn).coerceAtLeast(0.001f)
                        for (i in ppgTrace.indices) {
                            val px = size.width * i / (ppgTrace.size - 1f)
                            val norm = (ppgTrace[i] - mn) / range
                            val py = size.height * (1f - norm) * 0.9f + size.height * 0.05f
                            if (i == 0) path.moveTo(px, py) else path.lineTo(px, py)
                        }
                        drawPath(path, BadaColors.Cyan, style = Stroke(2f))
                    }
                }
            }
        }
    }
}

/** One ECG beat as a sum of Gaussians (P, Q, R, S, T), phase in 0..1. */
private fun ecgBeat(phase: Float): Float {
    fun g(center: Float, amp: Float, width: Float) =
        amp * exp(-((phase - center) * (phase - center)) / (2f * width * width))
    return g(0.18f, 0.10f, 0.025f) +   // P
            g(0.38f, -0.12f, 0.008f) +  // Q
            g(0.40f, 1.00f, 0.007f) +   // R
            g(0.42f, -0.22f, 0.009f) +  // S
            g(0.62f, 0.22f, 0.040f)     // T
}
