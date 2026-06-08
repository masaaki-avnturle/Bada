package com.bada.biofeedback.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.biofeedback.audio.ToneSynth
import com.bada.biofeedback.lang.BadaMath
import com.bada.biofeedback.lang.BadaPreset
import com.bada.biofeedback.lang.BodyRegion
import com.bada.biofeedback.lang.PresetRepository
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner
import com.bada.biofeedback.ui.ScreenHeader
import com.bada.biofeedback.ui.parseHex

@Composable
fun MedicationScreen(nav: NavController) {
    val context = LocalContext.current
    val presets = remember { PresetRepository.load(context) }
    var selected by remember { mutableStateOf(presets.firstOrNull()) }
    var playing by remember { mutableStateOf(false) }
    val synth = remember { ToneSynth() }
    var t by remember { mutableFloatStateOf(0f) }

    LaunchedEffect(Unit) {
        val start = withFrameNanos { it }
        while (true) {
            val now = withFrameNanos { it }
            t = (now - start) / 1_000_000_000f
        }
    }
    DisposableEffect(Unit) { onDispose { synth.stop() } }

    val accent = selected?.let { parseHex(it.colorHex) } ?: BadaColors.Gold

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("薬バイオフィードバック", BadaColors.Gold) {
            synth.stop(); nav.popBackStack()
        }
        DisclaimerBanner(
            "これは薬効を再現・代替するものではありません。各プリセットは “その薬の名にちなんだ" +
            "ほっとする音風景と部位” です。処方は必ず主治医の指示に従ってください。"
        )

        // preset chips
        LazyRow(
            modifier = Modifier.fillMaxWidth().padding(8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(presets) { p ->
                val isSel = p.id == selected?.id
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = if (isSel) parseHex(p.colorHex).copy(alpha = 0.25f) else BadaColors.Surface
                    ),
                    onClick = {
                        selected = p
                        if (playing) synth.start(p)
                    }
                ) {
                    Text(
                        p.label,
                        color = if (isSel) parseHex(p.colorHex) else BadaColors.Text,
                        fontSize = 13.sp,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp)
                    )
                }
            }
        }

        selected?.let { p ->
            // body + breathing visualisation
            val env = BadaMath.sessionEnvelope(t.toDouble(), 180.0).toFloat()
            Box(Modifier.fillMaxWidth().aspectRatio(0.75f)) {
                Canvas(Modifier.fillMaxSize()) {
                    val w = size.width
                    val h = size.height
                    // simple body silhouette
                    val cx = w / 2f
                    drawCircle(BadaColors.Surface, h * 0.08f, Offset(cx, h * 0.12f)) // head
                    drawRoundRect(
                        BadaColors.Surface,
                        topLeft = Offset(cx - w * 0.18f, h * 0.20f),
                        size = androidx.compose.ui.geometry.Size(w * 0.36f, h * 0.42f),
                        cornerRadius = androidx.compose.ui.geometry.CornerRadius(w * 0.10f)
                    )

                    // target-region "ほっと" glow, breathing with the envelope
                    val region = BodyRegion.of(p.region)
                    val gx = cx + (region.nx - 0.5f) * w * 0.7f
                    val gy = h * (0.05f + region.ny * 0.75f)
                    val breath = 0.6f + 0.4f * env
                    val glow = parseHex(p.colorHex)
                    drawCircle(
                        brush = Brush.radialGradient(
                            colors = listOf(glow.copy(alpha = 0.6f * breath), Color.Transparent),
                            center = Offset(gx, gy),
                            radius = w * 0.42f * breath
                        ),
                        radius = w * 0.42f * breath,
                        center = Offset(gx, gy)
                    )
                    drawCircle(glow.copy(alpha = 0.9f), w * 0.012f, Offset(gx, gy))
                }
            }

            Card(
                modifier = Modifier.fillMaxWidth().padding(8.dp),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = BadaColors.Surface)
            ) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(p.label, color = accent, fontWeight = FontWeight.Bold, fontSize = 22.sp)
                    Text("ほっとする部位: ${BodyRegion.of(p.region).label}", color = BadaColors.Text, fontSize = 14.sp)
                    Text("感覚: ${p.feeling}", color = BadaColors.Text, fontSize = 14.sp)
                    Text(p.narration, color = BadaColors.TextDim, fontSize = 13.sp)
                    Text(
                        "音: ${p.baseHz.toInt()}Hz / 呼吸 ${"%.1f".format(p.beatHz)}Hz / 波形 ${p.waveform}",
                        color = BadaColors.TextDim, fontSize = 11.sp
                    )
                }
            }

            Button(
                onClick = {
                    if (playing) { synth.stop(); playing = false }
                    else { synth.start(p); playing = true }
                },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
                colors = ButtonDefaults.buttonColors(containerColor = accent)
            ) {
                Text(if (playing) "停止" else "音風景を再生", color = BadaColors.Bg, fontWeight = FontWeight.Bold)
            }
            Text(
                "ヘッドフォン推奨。音と部位のハイライトに合わせ、ゆっくり呼吸してください。",
                color = BadaColors.TextDim, fontSize = 11.sp,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
            )
        }
    }
}
