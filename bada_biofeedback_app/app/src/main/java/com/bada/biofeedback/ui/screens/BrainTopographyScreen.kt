package com.bada.biofeedback.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.bada.biofeedback.lang.BadaMath
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner
import com.bada.biofeedback.ui.ScreenHeader
import com.bada.biofeedback.ui.SectionCard
import androidx.compose.material3.Text
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

// 10-20 electrode layout in unit-circle coordinates (x right, y down).
private val electrodes = listOf(
    "Fp1" to Offset(-0.27f, -0.80f), "Fp2" to Offset(0.27f, -0.80f),
    "F7" to Offset(-0.70f, -0.45f), "F3" to Offset(-0.35f, -0.40f),
    "Fz" to Offset(0.0f, -0.42f), "F4" to Offset(0.35f, -0.40f), "F8" to Offset(0.70f, -0.45f),
    "T3" to Offset(-0.85f, 0.0f), "C3" to Offset(-0.42f, 0.0f), "Cz" to Offset(0.0f, 0.0f),
    "C4" to Offset(0.42f, 0.0f), "T4" to Offset(0.85f, 0.0f),
    "P3" to Offset(-0.35f, 0.40f), "Pz" to Offset(0.0f, 0.42f), "P4" to Offset(0.35f, 0.40f),
    "O1" to Offset(-0.27f, 0.80f), "O2" to Offset(0.27f, 0.80f)
)

@Composable
fun BrainTopographyScreen(nav: NavController) {
    var t by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(Unit) {
        val start = withFrameNanos { it }
        while (true) {
            val now = withFrameNanos { it }
            t = (now - start) / 1_000_000_000f
        }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("脳トポグラフィー", BadaColors.Cyan) { nav.popBackStack() }
        DisclaimerBanner("これは手続き的に生成したシミュレーションです。実際の脳活動は測定していません。")

        SectionCard("EEG トポマップ (擬似)", BadaColors.Cyan) {
            Box(Modifier.fillMaxWidth().aspectRatio(1f)) {
                Canvas(Modifier.fillMaxSize()) {
                    val cx = size.width / 2f
                    val cy = size.height / 2f
                    val r = size.minDimension / 2f * 0.92f

                    // scalp glow field from electrode "activations"
                    for ((i, e) in electrodes.withIndex()) {
                        val (_, pos) = e
                        val phase = i * 0.7f
                        val act = (0.5f + 0.5f * sin(t * (0.8f + 0.05f * i) + phase))
                        val entropy = BadaMath.thermalEntropy(act.toDouble()).toFloat()
                        val px = cx + pos.x * r
                        val py = cy + pos.y * r
                        val hue = lerpColor(BadaColors.Violet, BadaColors.Cyan, act)
                        drawCircle(
                            brush = Brush.radialGradient(
                                colors = listOf(hue.copy(alpha = 0.45f * entropy), Color.Transparent),
                                center = Offset(px, py),
                                radius = r * 0.5f
                            ),
                            radius = r * 0.5f,
                            center = Offset(px, py)
                        )
                    }
                    // head outline
                    drawCircle(BadaColors.TextDim, radius = r, center = Offset(cx, cy), style = androidx.compose.ui.graphics.drawscope.Stroke(2f))
                    // nose
                    val noseY = cy - r
                    drawLine(BadaColors.TextDim, Offset(cx - r * 0.08f, noseY), Offset(cx, noseY - r * 0.10f), 2f)
                    drawLine(BadaColors.TextDim, Offset(cx + r * 0.08f, noseY), Offset(cx, noseY - r * 0.10f), 2f)
                    // electrode dots
                    for ((_, pos) in electrodes) {
                        drawCircle(BadaColors.Text.copy(alpha = 0.6f), 4f, Offset(cx + pos.x * r, cy + pos.y * r))
                    }
                }
            }
        }

        SectionCard("バンドパワー (擬似)", BadaColors.Cyan) {
            val bands = listOf(
                "δ Delta (0.5–4Hz)" to bandLevel(t, 0.3f),
                "θ Theta (4–8Hz)" to bandLevel(t, 0.55f),
                "α Alpha (8–12Hz)" to bandLevel(t, 0.8f),
                "β Beta (12–30Hz)" to bandLevel(t, 1.3f),
                "γ Gamma (30–80Hz)" to bandLevel(t, 2.1f),
            )
            for ((name, lvl) in bands) {
                Text("$name   ${"%.0f".format(lvl * 100)}%", color = BadaColors.Text, fontSize = 13.sp)
                Box(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
                    Canvas(Modifier.fillMaxWidth().padding(end = 4.dp).aspectRatio(28f)) {
                        drawRoundRect(BadaColors.Surface, size = size)
                        drawRoundRect(BadaColors.Cyan.copy(alpha = 0.8f),
                            size = size.copy(width = size.width * lvl))
                    }
                }
            }
            Text("γ帯はガンマ関数 envelope と連動した装飾です（実測ではありません）。",
                color = BadaColors.TextDim, fontSize = 11.sp)
        }
    }
}

private fun bandLevel(t: Float, speed: Float): Float =
    (0.5f + 0.5f * sin(t * speed + speed)).coerceIn(0.05f, 1f)

private fun lerpColor(a: Color, b: Color, f: Float): Color {
    val g = f.coerceIn(0f, 1f)
    return Color(
        red = a.red + (b.red - a.red) * g,
        green = a.green + (b.green - a.green) * g,
        blue = a.blue + (b.blue - a.blue) * g,
        alpha = 1f
    )
}
