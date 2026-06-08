package com.bada.biofeedback.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner
import com.bada.biofeedback.ui.ScreenHeader
import com.bada.biofeedback.ui.SectionCard

private data class Analyte(
    val name: String, val unit: String,
    val min: Float, val max: Float,    // slider range
    val refLo: Float, val refHi: Float // reference interval
)

@Composable
fun VitalsScreen(nav: NavController) {
    var systolic by remember { mutableFloatStateOf(118f) }
    var diastolic by remember { mutableFloatStateOf(76f) }

    val analytes = remember {
        listOf(
            Analyte("ヘモグロビン Hb", "g/dL", 5f, 20f, 13.0f, 17.0f),
            Analyte("白血球 WBC", "10³/µL", 1f, 20f, 3.5f, 9.0f),
            Analyte("赤血球 RBC", "10⁶/µL", 2f, 7f, 4.2f, 5.5f),
            Analyte("血小板 PLT", "10³/µL", 50f, 500f, 150f, 350f),
            Analyte("血糖 Glucose", "mg/dL", 40f, 300f, 70f, 110f),
            Analyte("ヘマトクリット Ht", "%", 20f, 60f, 40f, 50f),
        )
    }
    val values = remember { analytes.map { mutableFloatStateOf((it.refLo + it.refHi) / 2f) } }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("血液成分・血圧", BadaColors.Cyan) { nav.popBackStack() }
        DisclaimerBanner(
            "値はあなたの手入力（または初期サンプル）です。スマホでは血液・血圧を実測できません。" +
            "実測には採血検査・カフ式血圧計が必要です。判断は医療機関で。"
        )

        SectionCard("血圧 (手入力)", BadaColors.Cyan) {
            val cat = bpCategory(systolic.toInt(), diastolic.toInt())
            Text("${systolic.toInt()} / ${diastolic.toInt()} mmHg",
                color = cat.second, fontWeight = FontWeight.Bold, fontSize = 34.sp)
            Text(cat.first, color = cat.second, fontSize = 14.sp)
            Text("収縮期 Systolic: ${systolic.toInt()}", color = BadaColors.TextDim, fontSize = 12.sp)
            Slider(value = systolic, onValueChange = { systolic = it }, valueRange = 80f..200f)
            Text("拡張期 Diastolic: ${diastolic.toInt()}", color = BadaColors.TextDim, fontSize = 12.sp)
            Slider(value = diastolic, onValueChange = { diastolic = it }, valueRange = 40f..130f)
        }

        SectionCard("血液成分 (手入力)", BadaColors.Cyan) {
            for (i in analytes.indices) {
                val a = analytes[i]
                val v by values[i]
                val inRange = v in a.refLo..a.refHi
                val color = if (inRange) BadaColors.Cyan else BadaColors.Warn
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(a.name, color = BadaColors.Text, fontSize = 14.sp)
                    Text("${"%.1f".format(v)} ${a.unit}", color = color, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
                Text("基準 ${a.refLo}–${a.refHi} ${a.unit}  ${if (inRange) "範囲内" else "範囲外"}",
                    color = BadaColors.TextDim, fontSize = 11.sp)
                Slider(
                    value = v,
                    onValueChange = { values[i].floatValue = it },
                    valueRange = a.min..a.max,
                    modifier = Modifier.padding(bottom = 6.dp)
                )
            }
        }
    }
}

private fun bpCategory(sys: Int, dia: Int): Pair<String, Color> = when {
    sys < 90 || dia < 60 -> "低血圧の範囲" to BadaColors.Warn
    sys < 120 && dia < 80 -> "正常域" to BadaColors.Cyan
    sys < 130 && dia < 80 -> "正常高値" to BadaColors.Cyan
    sys < 140 || dia < 90 -> "高値血圧" to BadaColors.Warn
    else -> "高血圧の範囲（受診の目安）" to Color(0xFFE0604A)
}
