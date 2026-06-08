package com.bada.biofeedback.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.biofeedback.lang.BadaMath
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner
import com.bada.biofeedback.ui.ScreenHeader
import com.bada.biofeedback.ui.SectionCard
import kotlin.math.sin

private val phraseBoard = listOf(
    "はい", "いいえ", "ありがとう", "助けて", "痛い", "水がほしい",
    "トイレ", "休みたい", "話したい", "大丈夫", "怖い", "嬉しい",
    "胸が苦しい", "頭が重い", "落ち着いた", "眠い"
)

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SilentTalkScreen(nav: NavController) {
    var message by remember { mutableStateOf("") }
    var t by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(Unit) {
        val start = withFrameNanos { it }
        while (true) {
            val now = withFrameNanos { it }
            t = (now - start) / 1_000_000_000f
        }
    }

    // conceptual "manifold integration" telemetry (procedural, not measured)
    val pBalance = (0.5 + 0.45 * sin(t * 0.4)).coerceIn(0.01, 0.99)
    val entropy = BadaMath.thermalEntropy(pBalance)
    val gammaVal = BadaMath.gammaEnvelope((pBalance * 4.0) + 0.1, 2.0, 0.6)
    val irTemp = 36.2 + 0.6 * sin(t * 0.2)

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("サイレントトーク", BadaColors.Violet) { nav.popBackStack() }
        DisclaimerBanner(
            "重要: これは思考を読み取る機能ではありません（現行技術では不可能です）。" +
            "声を出さずにタップで意思を伝える “無声コミュニケーション盤” です。下の数値は" +
            "ガンマ/オイラー定数/熱エントロピーの演出表示で、体の実測ではありません。"
        )

        SectionCard("無声メッセージ盤", BadaColors.Violet) {
            Text(
                if (message.isEmpty()) "（タップで言葉を選んでください）" else message,
                color = if (message.isEmpty()) BadaColors.TextDim else BadaColors.Text,
                fontSize = 22.sp, fontWeight = FontWeight.Bold
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                for (word in phraseBoard) {
                    AssistChip(
                        onClick = { message = if (message.isEmpty()) word else "$message $word" },
                        label = { Text(word, fontSize = 15.sp) }
                    )
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = { message = "" }) { Text("消去") }
                Button(
                    onClick = { /* message stays large on screen to "speak" silently */ },
                    colors = ButtonDefaults.buttonColors(containerColor = BadaColors.Violet)
                ) { Text("大きく表示", color = BadaColors.Bg) }
            }
        }

        SectionCard("多様体テレメトリ (演出)", BadaColors.Violet) {
            Text("大脳基底核チャネル: アクティブ（擬似）", color = BadaColors.Text, fontSize = 13.sp)
            Text("Γ envelope = ${"%.4f".format(gammaVal)}", color = BadaColors.TextDim, fontSize = 13.sp)
            Text("Euler γ = ${"%.6f".format(BadaMath.EULER_GAMMA)}", color = BadaColors.TextDim, fontSize = 13.sp)
            Text("熱エントロピー S = ${"%.4f".format(entropy)} bits", color = BadaColors.TextDim, fontSize = 13.sp)
            Text("赤外線(擬似)温度 = ${"%.1f".format(irTemp)} ℃", color = BadaColors.TextDim, fontSize = 13.sp)
            Text(
                "∬ 1/(x·log x)² dx_m の大域的部分積分多様体を envelope として可視化（概念表示）。",
                color = BadaColors.TextDim, fontSize = 11.sp
            )
        }
    }
}
