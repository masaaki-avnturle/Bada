package com.bada.morpho.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.morpho.lang.ProtocolRepository
import com.bada.morpho.sim.LineageTree
import com.bada.morpho.ui.DisclaimerBanner
import com.bada.morpho.ui.MorphoColors
import com.bada.morpho.ui.ScreenHeader
import com.bada.morpho.ui.SectionCard

@Composable
fun LineageScreen(nav: NavController) {
    val context = LocalContext.current
    val protocols = remember { ProtocolRepository.load(context) }
    var selected by remember { mutableStateOf(protocols.firstOrNull()) }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("iPS細胞 分岐シミュレーション", MorphoColors.Green) { nav.popBackStack() }
        DisclaimerBanner(
            "1個のiPS細胞から、カスプ双安定＋確率的分枝で系統樹を生成します。" +
            "数学モデルであり、実際の培養・分化プロトコルではありません。"
        )

        LazyRow(Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(protocols) { p ->
                val sel = p.id == selected?.id
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = if (sel) MorphoColors.Green.copy(alpha = 0.22f) else MorphoColors.Surface
                    ),
                    onClick = { selected = p }
                ) {
                    Text(p.label, color = if (sel) MorphoColors.Green else MorphoColors.Text,
                        fontSize = 13.sp, modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp))
                }
            }
        }

        selected?.let { p ->
            val tree = remember(p.id) {
                LineageTree(p.cuspA, p.cuspB, p.branchProb).also { it.generate() }
            }
            val byId = remember(p.id) { tree.nodes.associateBy { it.id } }

            SectionCard("系統樹 (${p.label})", MorphoColors.Green) {
                Canvas(Modifier.fillMaxWidth().height(360.dp)) {
                    val w = size.width; val h = size.height
                    val pad = 16f
                    fun px(nx: Float) = pad + nx * (w - 2 * pad)
                    fun py(ny: Float) = pad + ny * (h - 2 * pad)
                    // edges
                    for (node in tree.nodes) {
                        val parent = byId[node.parent] ?: continue
                        drawLine(
                            MorphoColors.TextDim.copy(alpha = 0.6f),
                            Offset(px(parent.x), py(parent.y)),
                            Offset(px(node.x), py(node.y)), 2f
                        )
                    }
                    // nodes
                    for (node in tree.nodes) {
                        val c = when {
                            node.depth == 0 -> MorphoColors.Gold
                            node.terminal && node.fate == p.target -> MorphoColors.Green
                            node.terminal -> MorphoColors.Violet
                            else -> MorphoColors.Text.copy(alpha = 0.7f)
                        }
                        val r = if (node.depth == 0) 9f else if (node.terminal) 6f else 4f
                        drawCircle(c, r, Offset(px(node.x), py(node.y)))
                    }
                }
                Text("● 金=iPS  ● 緑=目的(${p.target})  ● 紫=その他終端", color = MorphoColors.TextDim, fontSize = 11.sp)
            }

            SectionCard("終端細胞タイプ 構成 (増殖モデル)", MorphoColors.Green) {
                val counts = tree.population(p.target).entries.sortedByDescending { it.value }
                val total = counts.sumOf { it.value }.coerceAtLeast(1)
                for ((type, cnt) in counts) {
                    val frac = cnt.toFloat() / total
                    val isTarget = type == p.target
                    Text(
                        "$type : $cnt 個 (${"%.0f".format(frac * 100)}%)" + if (isTarget) "  ◀ 目的" else "",
                        color = if (isTarget) MorphoColors.Green else MorphoColors.Text,
                        fontWeight = if (isTarget) FontWeight.Bold else FontWeight.Normal,
                        fontSize = 13.sp
                    )
                    Canvas(Modifier.fillMaxWidth().height(8.dp).padding(vertical = 1.dp)) {
                        drawRect(MorphoColors.Surface, size = size)
                        drawRect(
                            if (isTarget) MorphoColors.Green else MorphoColors.Violet,
                            size = size.copy(width = size.width * frac)
                        )
                    }
                }
            }
        }
    }
}
