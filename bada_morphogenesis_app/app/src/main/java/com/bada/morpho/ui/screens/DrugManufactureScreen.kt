package com.bada.morpho.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.morpho.lang.ProtocolRepository
import com.bada.morpho.sim.DrugBatch
import com.bada.morpho.sim.LineageTree
import com.bada.morpho.sim.ReactionDiffusion
import com.bada.morpho.ui.DisclaimerBanner
import com.bada.morpho.ui.MorphoColors
import com.bada.morpho.ui.ScreenHeader
import com.bada.morpho.ui.SectionCard

@Composable
fun DrugManufactureScreen(nav: NavController) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val protocols = remember { ProtocolRepository.load(context) }
    var selected by remember { mutableStateOf(protocols.firstOrNull()) }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("薬製造シミュレーション", MorphoColors.Gold) { nav.popBackStack() }
        DisclaimerBanner(
            "下の収率・純度・力価・規格合否はトイモデルのシミュレーション値です。" +
            "実在の医薬品製造・品質判定・治療効果を示すものでは一切ありません。"
        )

        LazyRow(Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(protocols) { p ->
                val sel = p.id == selected?.id
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = if (sel) MorphoColors.Gold.copy(alpha = 0.22f) else MorphoColors.Surface
                    ),
                    onClick = { selected = p }
                ) {
                    Text(p.label, color = if (sel) MorphoColors.Gold else MorphoColors.Text,
                        fontSize = 13.sp, modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp))
                }
            }
        }

        selected?.let { p ->
            val result = remember(p.id) {
                val rd = ReactionDiffusion(80)
                rd.feed = p.feed.toFloat()
                rd.kill = p.kill.toFloat()
                rd.fieldStrength = p.fieldStrength.toFloat()
                rd.step(400)
                val frac = rd.differentiatedFraction()
                val tree = LineageTree(p.cuspA, p.cuspB, p.branchProb).also { it.generate() }
                DrugBatch.evaluate(
                    counts = tree.population(p.target),
                    targetType = p.target,
                    fieldStrength = p.fieldStrength,
                    differentiatedFraction = frac.toDouble(),
                    drugName = p.drug
                )
            }

            SectionCard("候補薬: ${result.drugName}", MorphoColors.Gold) {
                Text("目的細胞: ${result.targetType}", color = MorphoColors.Text, fontSize = 14.sp)
                Text(p.note, color = MorphoColors.TextDim, fontSize = 12.sp)
            }

            SectionCard("バッチ・シミュレーション結果", MorphoColors.Gold) {
                metric("収率 Yield", "${result.yieldPct} %")
                metric("純度 Purity", "${result.purityPct} %")
                metric("生存率 Viability", "${result.viabilityPct} %")
                metric("力価 Titer", "${result.titer} a.u.")
                metric("目的細胞数 / 総数", "${result.targetCount} / ${result.totalCells}")
                Row(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("規格判定", color = MorphoColors.Text, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    Text(
                        if (result.passSpec) "PASS ✓" else "FAIL ✗",
                        color = if (result.passSpec) MorphoColors.Green else MorphoColors.Danger,
                        fontWeight = FontWeight.Bold, fontSize = 18.sp
                    )
                }
                Text(
                    "規格: 純度≥75% かつ 生存率≥80%（シミュレーション上の閾値）",
                    color = MorphoColors.TextDim, fontSize = 11.sp
                )
            }
        }
    }
}

@Composable
private fun metric(label: String, value: String) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = MorphoColors.Text, fontSize = 14.sp)
        Text(value, color = MorphoColors.Gold, fontWeight = FontWeight.Bold, fontSize = 14.sp)
    }
}
