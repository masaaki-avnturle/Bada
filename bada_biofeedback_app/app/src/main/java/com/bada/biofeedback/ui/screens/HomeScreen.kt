package com.bada.biofeedback.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.biofeedback.ui.BadaColors
import com.bada.biofeedback.ui.DisclaimerBanner

private data class MenuItem(val route: String, val title: String, val subtitle: String, val accent: Color)

@Composable
fun HomeScreen(nav: NavController) {
    val items = listOf(
        MenuItem("brain", "脳トポグラフィー", "EEGトポマップ (シミュレーション)", BadaColors.Cyan),
        MenuItem("imaging", "fMRI / MRI ビューア", "断層スライス (シミュレーション)", BadaColors.Violet),
        MenuItem("eeg", "脳波計 (EEG)", "多チャンネル波形 (シミュレーション)", BadaColors.Cyan),
        MenuItem("ecg", "心電図 (ECG) + 心拍", "PPG実測オプション付き", BadaColors.Gold),
        MenuItem("meds", "薬バイオフィードバック", "“ほっとする” 音風景 + 部位ハイライト", BadaColors.Gold),
        MenuItem("silent", "サイレントトーク", "熱エントロピー/赤外線 コンセプト (デモ)", BadaColors.Violet),
        MenuItem("vitals", "血液成分・血圧", "手入力 + シミュレーション表示", BadaColors.Cyan),
    )

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(8.dp),
        verticalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        Text(
            "Bada Biofeedback",
            color = BadaColors.Gold,
            fontWeight = FontWeight.Bold,
            fontSize = 26.sp,
            modifier = Modifier.padding(start = 12.dp, top = 18.dp)
        )
        Text(
            "Γ(s)=β(p,q)/log x · 大域的部分積分多様体 · 熱エントロピー envelope",
            color = BadaColors.TextDim,
            fontSize = 11.sp,
            modifier = Modifier.padding(start = 12.dp, bottom = 6.dp)
        )

        DisclaimerBanner(
            "本アプリは教育・リラクゼーション用のシミュレーションです。脳波・MRI・血液・血圧・思考の" +
            "実測は行いません。薬効の再現や医療・投薬の代替ではありません。体調の判断・診断には使えません。"
        )

        for (item in items) {
            Card(
                modifier = Modifier.fillMaxWidth().padding(8.dp),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = BadaColors.Surface),
                onClick = { nav.navigate(item.route) }
            ) {
                Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
                    Text(item.title, color = item.accent, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Text(item.subtitle, color = BadaColors.TextDim, fontSize = 12.sp)
                }
            }
        }

        Text(
            "© Masaaki Yamaguchi · 山口雅旭 · Bada Language",
            color = BadaColors.TextDim,
            fontSize = 10.sp,
            modifier = Modifier.padding(12.dp)
        )
    }
}
