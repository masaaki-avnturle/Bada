package com.bada.biofeedback.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.foundation.layout.Row
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner
import com.bada.biofeedback.ui.ScreenHeader
import com.bada.biofeedback.ui.SectionCard
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.sin

@Composable
fun ImagingScreen(nav: NavController) {
    var slice by remember { mutableFloatStateOf(0.5f) }
    var fmri by remember { mutableStateOf(true) }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("fMRI / MRI ビューア", BadaColors.Violet) { nav.popBackStack() }
        DisclaimerBanner("断層像・賦活マップは手続き的生成のシミュレーションです。実際のスキャンではありません。")

        SectionCard(if (fmri) "fMRI 賦活オーバーレイ (擬似)" else "MRI 構造像 (擬似)", BadaColors.Violet) {
            Box(Modifier.fillMaxWidth().aspectRatio(1f)) {
                Canvas(Modifier.fillMaxSize()) {
                    val n = 56
                    val cw = size.width / n
                    val ch = size.height / n
                    val z = slice * 6f
                    for (gy in 0 until n) {
                        for (gx in 0 until n) {
                            val u = gx / (n - 1f) * 2f - 1f
                            val v = gy / (n - 1f) * 2f - 1f
                            val rr = u * u + v * v
                            if (rr > 0.92f) continue // outside skull ellipse

                            // structural "tissue" value
                            val tissue = (0.5f + 0.5f * sin(u * 6f + z) * cos(v * 5f - z) +
                                    0.25f * noise(u * 3f, v * 3f, z)).coerceIn(0f, 1f)
                            val gray = 0.25f + 0.6f * tissue * (1f - rr * 0.5f)
                            var c = Color(gray, gray, gray * 1.02f.coerceAtMost(1f), 1f)

                            if (fmri) {
                                // a couple of moving "activation" hotspots
                                val a1 = exp(-(((u - 0.35f * sin(z)) * (u - 0.35f * sin(z)) +
                                        (v + 0.2f) * (v + 0.2f)) / 0.05f))
                                val a2 = exp(-(((u + 0.4f) * (u + 0.4f) +
                                        (v - 0.3f * cos(z)) * (v - 0.3f * cos(z))) / 0.04f))
                                val act = (a1 + a2).coerceIn(0f, 1f)
                                if (act > 0.05f) {
                                    val hot = if (act > 0.5f) Color(1f, 0.55f, 0.1f) else Color(0.9f, 0.2f, 0.1f)
                                    c = blend(c, hot, act)
                                }
                            }
                            drawRect(c, topLeft = Offset(gx * cw, gy * ch), size = Size(cw + 1f, ch + 1f))
                        }
                    }
                }
            }
            Text("スライス位置 z = ${"%.2f".format(slice)}", color = BadaColors.TextDim, fontSize = 12.sp)
            Slider(value = slice, onValueChange = { slice = it })
            Row(verticalAlignment = Alignment.CenterVertically) {
                Switch(checked = fmri, onCheckedChange = { fmri = it })
                Text(if (fmri) "  fMRI賦活ON" else "  MRI構造のみ", color = BadaColors.Text, fontSize = 13.sp)
            }
        }
    }
}

// cheap value noise from hashed sines (deterministic, smooth-ish)
private fun noise(x: Float, y: Float, z: Float): Float {
    val s = sin(x * 12.9898f + y * 78.233f + z * 37.719f) * 43758.5453f
    return (s - kotlin.math.floor(s)) * 2f - 1f
}

private fun blend(a: Color, b: Color, f: Float): Color {
    val g = f.coerceIn(0f, 1f)
    return Color(
        a.red + (b.red - a.red) * g,
        a.green + (b.green - a.green) * g,
        a.blue + (b.blue - a.blue) * g,
        1f
    )
}
