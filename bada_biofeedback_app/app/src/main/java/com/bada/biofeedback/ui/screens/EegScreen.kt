package com.bada.biofeedback.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner
import com.bada.biofeedback.ui.ScreenHeader
import com.bada.biofeedback.ui.SectionCard
import kotlin.math.sin

private val channels = listOf("Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2")

@Composable
fun EegScreen(nav: NavController) {
    var t by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(Unit) {
        val start = withFrameNanos { it }
        while (true) {
            val now = withFrameNanos { it }
            t = (now - start) / 1_000_000_000f
        }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("脳波計 (EEG)", BadaColors.Cyan) { nav.popBackStack() }
        DisclaimerBanner("表示波形は合成信号です。実際の脳波は計測していません。")

        SectionCard("10チャンネル EEG (擬似 / 10秒窓)", BadaColors.Cyan) {
            Canvas(Modifier.fillMaxWidth().height(420.dp)) {
                val rows = channels.size
                val rowH = size.height / rows
                val samples = 240
                for (ch in 0 until rows) {
                    val baseY = rowH * ch + rowH / 2f
                    val path = Path()
                    for (i in 0 until samples) {
                        val x = size.width * i / (samples - 1f)
                        val tt = t + i * 0.02f
                        val seed = ch * 1.7f
                        val v = 0.45f * sin(tt * 11f + seed) +      // alpha-ish
                                0.25f * sin(tt * 23f + seed * 2f) + // beta-ish
                                0.18f * sin(tt * 5f + seed) +       // theta-ish
                                0.10f * sin(tt * 47f + seed * 3f)   // gamma-ish
                        val y = baseY - v * rowH * 0.38f
                        if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
                    }
                    drawPath(path, BadaColors.Cyan.copy(alpha = 0.85f), style = Stroke(2f))
                    drawLine(BadaColors.Surface, Offset(0f, rowH * (ch + 1)), Offset(size.width, rowH * (ch + 1)), 1f)
                }
            }
            Column {
                Text("チャンネル: " + channels.joinToString(" "), color = BadaColors.TextDim, fontSize = 11.sp)
            }
        }
    }
}
