package com.bada.oracle

import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.concurrent.thread
import kotlin.math.PI
import kotlin.math.sin

private val Bg = Color(0xFF060410)
private val Violet = Color(0xFF9060D0)
private val Gold = Color(0xFFC8A44A)
private val Cyan = Color(0xFF40B8C0)
private val TextC = Color(0xFFE6EAF0)
private val Dim = Color(0xFF8A93A0)
private val Warn = Color(0xFFE0A24A)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        OracleEngine.load(applicationContext)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Violet, background = Bg, surface = Color(0xFF120C22),
                    onBackground = TextC, onSurface = TextC
                )
            ) {
                Surface(Modifier.fillMaxSize(), color = Bg) { OracleScreen() }
            }
        }
    }
}

@Composable
private fun OracleScreen() {
    val context = LocalContext.current
    var question by remember { mutableStateOf("") }
    var reading by remember { mutableStateOf<OracleEngine.Reading?>(null) }
    var taps by remember { mutableLongStateOf(0L) }
    var t by remember { mutableFloatStateOf(0f) }

    LaunchedEffect(Unit) {
        val start = withFrameNanos { it }
        while (true) { val now = withFrameNanos { it }; t = (now - start) / 1_000_000_000f }
    }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Text("Bada Oracle", color = Gold, fontWeight = FontWeight.Bold, fontSize = 28.sp,
            modifier = Modifier.padding(top = 14.dp))
        Text("Γ(s) · 大域的部分積分多様体 · 手続き的託宣ジェネレーター",
            color = Dim, fontSize = 11.sp)

        Card(
            shape = RoundedCornerShape(10.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF1A130A)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                "⚠ これは娯楽・内省のための生成アートです。アカシックレコードへのアクセスや" +
                "未来の予知ではありません。生成される言葉は手続き的に合成されたもので、" +
                "健康・お金・進路など重要な判断の根拠には使わないでください。",
                color = Warn, fontSize = 12.sp, modifier = Modifier.padding(12.dp)
            )
        }

        // animated ring
        Box(Modifier.fillMaxWidth().aspectRatio(1.3f)) {
            Canvas(Modifier.fillMaxSize()) {
                val cx = size.width / 2f; val cy = size.height / 2f
                val base = size.minDimension / 2f * 0.7f
                for (k in 0 until 4) {
                    val rr = base * (0.5f + 0.16f * k) * (1f + 0.03f * sin(t * (0.7f + 0.2f * k)))
                    val alpha = 0.25f - 0.05f * k
                    drawCircle(Violet.copy(alpha = alpha), rr, Offset(cx, cy), style = Stroke(2f))
                }
                drawCircle(
                    brush = Brush.radialGradient(
                        listOf(Cyan.copy(alpha = 0.5f + 0.2f * sin(t)), Color.Transparent),
                        center = Offset(cx, cy), radius = base * 0.6f
                    ),
                    radius = base * 0.6f, center = Offset(cx, cy)
                )
            }
        }

        OutlinedTextField(
            value = question,
            onValueChange = { question = it },
            label = { Text("いま心にあること（任意）", color = Dim) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
            modifier = Modifier.fillMaxWidth()
        )

        Button(
            onClick = {
                taps += 1
                val r = OracleEngine.generate(question, taps xor (t.toRawBits().toLong()))
                reading = r
                playChime(440.0 + (r.gamma * 30.0))
            },
            colors = ButtonDefaults.buttonColors(containerColor = Violet),
            modifier = Modifier.fillMaxWidth()
        ) { Text("受信する", color = Bg, fontWeight = FontWeight.Bold, fontSize = 16.sp) }

        reading?.let { r ->
            Card(
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF120C22)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(r.message, color = TextC, fontSize = 18.sp, lineHeight = 28.sp)
                    Text(
                        "seed ${r.seedHex} · Γ=${"%.4f".format(r.gamma)} · S=${"%.4f".format(r.entropy)} bits",
                        color = Dim, fontSize = 11.sp
                    )
                }
            }
            Text("※ 生成アートです。もう一度押すと別の言葉が出ます（予知ではありません）。",
                color = Dim, fontSize = 11.sp)
        }

        Text("© Masaaki Yamaguchi · 山口雅旭 · Bada Language",
            color = Dim, fontSize = 10.sp, modifier = Modifier.padding(top = 8.dp))
    }
}

/** Play a short, soft biofeedback chime (fire and forget). */
private fun playChime(freq: Double) {
    thread(name = "OracleChime") {
        val sr = 44100
        val durMs = 1200
        val n = sr * durMs / 1000
        val buf = ShortArray(n)
        for (i in 0 until n) {
            val tt = i.toDouble() / sr
            val env = Math.exp(-3.0 * tt) // gentle decay
            val s = sin(2 * PI * freq * tt) * 0.6 + sin(2 * PI * freq * 2 * tt) * 0.2
            buf[i] = (s * env * Short.MAX_VALUE * 0.5).toInt().toShort()
        }
        val at = AudioTrack(
            AudioManager.STREAM_MUSIC, sr,
            AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT,
            n * 2, AudioTrack.MODE_STATIC
        )
        at.write(buf, 0, n)
        at.play()
        Thread.sleep((durMs + 100).toLong())
        try { at.stop() } catch (_: Exception) {}
        at.release()
    }
}
