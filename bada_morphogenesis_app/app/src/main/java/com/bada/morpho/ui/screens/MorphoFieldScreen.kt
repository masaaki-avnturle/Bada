package com.bada.morpho.ui.screens

import android.graphics.Bitmap
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.morpho.sim.ReactionDiffusion
import com.bada.morpho.ui.DisclaimerBanner
import com.bada.morpho.ui.MorphoColors
import com.bada.morpho.ui.ScreenHeader
import com.bada.morpho.ui.SectionCard

@Composable
fun MorphoFieldScreen(nav: NavController) {
    val rd = remember { ReactionDiffusion(96) }
    val bitmap = remember { Bitmap.createBitmap(rd.n, rd.n, Bitmap.Config.ARGB_8888) }
    val pixels = remember { IntArray(rd.n * rd.n) }
    var frame by remember { mutableIntStateOf(0) }

    var fieldStrength by remember { mutableFloatStateOf(0.3f) }
    var fieldX by remember { mutableFloatStateOf(0f) }
    var feed by remember { mutableFloatStateOf(0.037f) }
    var kill by remember { mutableFloatStateOf(0.060f) }

    LaunchedEffect(Unit) {
        while (true) {
            withFrameNanos { }
            rd.fieldStrength = fieldStrength
            rd.fieldX = fieldX
            rd.fieldY = 1f - kotlin.math.abs(fieldX) // gentle coupling
            rd.feed = feed
            rd.kill = kill
            rd.step(8)
            renderTo(rd, pixels, bitmap)
            frame++
        }
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("形態形成場 (反応拡散)", MorphoColors.Green) { nav.popBackStack() }
        DisclaimerBanner(
            "円形容器内の Gray–Scott 反応拡散系です。「場の強さ/向き」は抽象的な" +
            "シミュレーション・パラメータで、反重力や逆流電磁気の実機ではありません。"
        )

        SectionCard("円形容器 (Turing パターン)", MorphoColors.Green) {
            val tick = frame // read state to recompose each frame
            Box(Modifier.fillMaxWidth().aspectRatio(1f).padding(4.dp)) {
                Canvas(Modifier.fillMaxSize()) {
                    if (tick >= 0) {
                        drawImage(
                            image = bitmap.asImageBitmap(),
                            srcOffset = IntOffset.Zero,
                            srcSize = IntSize(rd.n, rd.n),
                            dstOffset = IntOffset.Zero,
                            dstSize = IntSize(size.width.toInt(), size.height.toInt())
                        )
                    }
                }
            }
            Text("分化領域: ${"%.1f".format(rd.differentiatedFraction() * 100)} %",
                color = MorphoColors.TextDim, fontSize = 12.sp)
        }

        SectionCard("場・反応パラメータ", MorphoColors.Green) {
            Text("場の強さ field_strength = ${"%.2f".format(fieldStrength)}", color = MorphoColors.Text, fontSize = 13.sp)
            Slider(value = fieldStrength, onValueChange = { fieldStrength = it })
            Text("場の向き field_x = ${"%.2f".format(fieldX)}", color = MorphoColors.Text, fontSize = 13.sp)
            Slider(value = fieldX, onValueChange = { fieldX = it }, valueRange = -1f..1f)
            Text("feed = ${"%.3f".format(feed)}", color = MorphoColors.Text, fontSize = 13.sp)
            Slider(value = feed, onValueChange = { feed = it }, valueRange = 0.02f..0.06f)
            Text("kill = ${"%.3f".format(kill)}", color = MorphoColors.Text, fontSize = 13.sp)
            Slider(value = kill, onValueChange = { kill = it }, valueRange = 0.05f..0.07f)
            Button(
                onClick = { rd.reset() },
                colors = ButtonDefaults.buttonColors(containerColor = MorphoColors.Green)
            ) { Text("容器をリセット", color = MorphoColors.Bg) }
        }
    }
}

private fun renderTo(rd: ReactionDiffusion, pixels: IntArray, bmp: Bitmap) {
    val n = rd.n
    for (y in 0 until n) for (x in 0 until n) {
        val i = y * n + x
        if (!rd.isInside(x, y)) {
            pixels[i] = 0xFF05080C.toInt()
        } else {
            val vv = rd.v[i].coerceIn(0f, 1f)
            // dark -> green -> gold
            val r = (vv * 200).toInt().coerceIn(0, 255)
            val g = (70 + vv * 160).toInt().coerceIn(0, 255)
            val b = (60 + (1f - vv) * 60).toInt().coerceIn(0, 255)
            pixels[i] = (0xFF shl 24) or (r shl 16) or (g shl 8) or b
        }
    }
    bmp.setPixels(pixels, 0, n, 0, 0, n, n)
}
