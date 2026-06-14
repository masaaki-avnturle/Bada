package com.bada.morpho.ui.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.bada.morpho.lang.MorphMath
import com.bada.morpho.ui.DisclaimerBanner
import com.bada.morpho.ui.MorphoColors
import com.bada.morpho.ui.ScreenHeader
import com.bada.morpho.ui.SectionCard

@Composable
fun CatastropheScreen(nav: NavController) {
    var a by remember { mutableFloatStateOf(-1.2f) }
    var b by remember { mutableFloatStateOf(0.0f) }

    val bistable = MorphMath.isBistable(a.toDouble(), b.toDouble())
    val stable = MorphMath.stableStates(a.toDouble(), b.toDouble())

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        ScreenHeader("カタストロフィ分岐", MorphoColors.Violet) { nav.popBackStack() }
        DisclaimerBanner(
            "Thom のカスプ・カタストロフィ V(x)=x⁴/4+a·x²/2+b·x で、細胞運命の" +
            "「不分岐(単安定)→分岐(双安定)」を表現します。発生生物学の局所分解の概念モデルです。"
        )

        SectionCard("ポテンシャル V(x) と平衡点", MorphoColors.Violet) {
            Canvas(Modifier.fillMaxWidth().height(220.dp)) {
                val w = size.width; val h = size.height
                val xMin = -2.2; val xMax = 2.2
                // sample potential
                var vMin = Double.MAX_VALUE; var vMax = -Double.MAX_VALUE
                val samples = 200
                val vs = DoubleArray(samples)
                for (i in 0 until samples) {
                    val x = xMin + (xMax - xMin) * i / (samples - 1)
                    val v = MorphMath.cuspPotential(x, a.toDouble(), b.toDouble())
                    vs[i] = v; if (v < vMin) vMin = v; if (v > vMax) vMax = v
                }
                val range = (vMax - vMin).coerceAtLeast(1e-6)
                fun sx(x: Double) = (((x - xMin) / (xMax - xMin)) * w).toFloat()
                fun sy(v: Double) = (h - ((v - vMin) / range) * h * 0.9 - h * 0.05).toFloat()

                val path = Path()
                for (i in 0 until samples) {
                    val x = xMin + (xMax - xMin) * i / (samples - 1)
                    val px = sx(x); val py = sy(vs[i])
                    if (i == 0) path.moveTo(px, py) else path.lineTo(px, py)
                }
                drawPath(path, MorphoColors.Violet, style = Stroke(3f))

                // equilibria
                val roots = MorphMath.cubicRealRoots(a.toDouble(), b.toDouble())
                for (x in roots) {
                    val stableEq = 3.0 * x * x + a > 0.0
                    val px = sx(x); val py = sy(MorphMath.cuspPotential(x, a.toDouble(), b.toDouble()))
                    if (stableEq) drawCircle(MorphoColors.Green, 9f, Offset(px, py))
                    else drawCircle(MorphoColors.Danger, 7f, Offset(px, py), style = Stroke(2.5f))
                }
            }
            Text(
                if (bistable) "状態: 双安定（分岐） — 2つの細胞運命が共存" else "状態: 単安定（不分岐）",
                color = if (bistable) MorphoColors.Green else MorphoColors.TextDim,
                fontWeight = FontWeight.Bold, fontSize = 14.sp
            )
            Text("安定平衡点 x = " + stable.joinToString(", ") { "%.2f".format(it) },
                color = MorphoColors.TextDim, fontSize = 12.sp)
            Text("● 緑=安定（細胞運命）  ○ 赤=不安定（分水嶺）", color = MorphoColors.TextDim, fontSize = 11.sp)
        }

        SectionCard("制御平面 (a, b) とカスプ", MorphoColors.Violet) {
            Canvas(Modifier.fillMaxWidth().height(200.dp)) {
                val w = size.width; val h = size.height
                val aMin = -2.0; val aMax = 1.0; val bMin = -1.5; val bMax = 1.5
                fun px(bb: Double) = (((bb - bMin) / (bMax - bMin)) * w).toFloat()
                fun py(aa: Double) = (((aa - aMin) / (aMax - aMin)) * h).toFloat()
                // cusp curve: 4a^3 + 27b^2 = 0  => b = ±sqrt(-4a^3/27), a<0
                val left = Path(); val right = Path()
                var started = false
                var aa = aMin
                while (aa <= 0.0) {
                    val rhs = -4.0 * aa * aa * aa / 27.0
                    if (rhs >= 0) {
                        val bb = Math.sqrt(rhs)
                        val lx = px(-bb); val rx = px(bb); val yy = py(aa)
                        if (!started) { left.moveTo(lx, yy); right.moveTo(rx, yy); started = true }
                        else { left.lineTo(lx, yy); right.lineTo(rx, yy) }
                    }
                    aa += 0.02
                }
                drawPath(left, MorphoColors.Gold, style = Stroke(2.5f))
                drawPath(right, MorphoColors.Gold, style = Stroke(2.5f))
                // current point
                drawCircle(MorphoColors.Green, 8f, Offset(px(b.toDouble()), py(a.toDouble())))
            }
            Text("a (← 負ほど分岐しやすい) = ${"%.2f".format(a)}", color = MorphoColors.Text, fontSize = 13.sp)
            Slider(value = a, onValueChange = { a = it }, valueRange = -2f..1f)
            Text("b (← 非対称性) = ${"%.2f".format(b)}", color = MorphoColors.Text, fontSize = 13.sp)
            Slider(value = b, onValueChange = { b = it }, valueRange = -1.5f..1.5f)
            Text("金色の曲線の内側が双安定（分岐）領域です。", color = MorphoColors.TextDim, fontSize = 11.sp)
        }
    }
}
