package com.bada.morpho.ui.screens

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
import com.bada.morpho.ui.DisclaimerBanner
import com.bada.morpho.ui.MorphoColors

private data class Item(val route: String, val title: String, val sub: String, val accent: Color)

@Composable
fun HomeScreen(nav: NavController) {
    val items = listOf(
        Item("field", "形態形成場 (反応拡散)", "円形容器内 Gray–Scott / Turing パターン", MorphoColors.Green),
        Item("catastrophe", "カタストロフィ分岐", "Thom カスプ：不分岐→分岐の双安定", MorphoColors.Violet),
        Item("lineage", "iPS細胞 分岐シミュレーション", "確率的分枝で系統樹を生成", MorphoColors.Green),
        Item("drug", "薬製造シミュレーション", "収率・純度・力価・規格合否を算出", MorphoColors.Gold),
    )
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(8.dp),
        verticalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        Text("Bada Morphogenesis", color = MorphoColors.Green, fontWeight = FontWeight.Bold,
            fontSize = 26.sp, modifier = Modifier.padding(start = 12.dp, top = 18.dp))
        Text("カタストロフィ理論 × 反応拡散 形態形成場 × iPS分岐 シミュレーション",
            color = MorphoColors.TextDim, fontSize = 11.sp, modifier = Modifier.padding(start = 12.dp, bottom = 6.dp))

        DisclaimerBanner(
            "本アプリは数学シミュレーション/可視化の教育デモです。反重力・逆流電磁気の実機ではなく、" +
            "実在の細胞培養や医薬品製造でもありません。出力値はトイモデルの参考値で、医療・製造の根拠には使えません。"
        )

        for (it in items) {
            Card(
                modifier = Modifier.fillMaxWidth().padding(8.dp),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = MorphoColors.Surface),
                onClick = { nav.navigate(it.route) }
            ) {
                Column(Modifier.fillMaxWidth().padding(16.dp)) {
                    Text(it.title, color = it.accent, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Text(it.sub, color = MorphoColors.TextDim, fontSize = 12.sp)
                }
            }
        }
        Text("© Masaaki Yamaguchi · 山口雅旭 · Bada Language",
            color = MorphoColors.TextDim, fontSize = 10.sp, modifier = Modifier.padding(12.dp))
    }
}
