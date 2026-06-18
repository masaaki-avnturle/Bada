package com.omega.silenttalk

import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * SilentCodec — 「言葉を使わず信号で伝える」無音通信のコーデック。
 *
 * 各文字を、ガンマ熱多様体 T'(γ) で変調した「熱・神経パルス列」へ符号化する。
 * γ を 1.0 から 0.02 刻みで進め、各文字コードを基底核伝播の末端出力に乗せて
 * パルス強度(深部体温オフセット)に写像する。復号は逆写像で行う。
 *
 * これは可逆な教育用エンコーディングであり、実際の医療信号ではない。
 */
object SilentCodec {

    data class Pulse(
        val gamma: Double,      // 変調に使った γ
        val tempC: Double,      // パルスの深部体温[°C]表現
        val ir: Double,         // 同時刻の赤外線センサー読み(付属センサー)
        val code: Int           // 元の文字コード
    )

    private const val GAMMA0 = 1.0
    private const val DG = 0.02
    private const val BASE = 36.0
    private const val SPAN = 0.02   // 1コードあたりの体温オフセット係数

    /** テキスト -> 無音パルス列 */
    fun encode(text: String): List<Pulse> {
        val out = ArrayList<Pulse>(text.length)
        var g = GAMMA0
        for ((i, ch) in text.withIndex()) {
            val code = ch.code
            // ガンマ熱多様体エネルギーで搬送波を作り、文字コードを温度オフセットに乗せる
            val carrier = NeuroThermal.thermalEnergy(g, g + 0.5, 64)
            val temp = BASE + SPAN * code + 0.001 * carrier
            val rng = kotlin.random.Random(0x5E7 + i)        // 決定的(再現可能)
            val ir = NeuroThermal.irSensor(temp, 0.97, 25.0, 0.0, rng)
            out.add(Pulse(g, temp, ir, code))
            g += DG
        }
        return out
    }

    /** 無音パルス列 -> テキスト（温度オフセットから文字コードを復元） */
    fun decode(pulses: List<Pulse>): String {
        val sb = StringBuilder(pulses.size)
        for (p in pulses) {
            val carrier = NeuroThermal.thermalEnergy(p.gamma, p.gamma + 0.5, 64)
            val code = ((p.tempC - BASE - 0.001 * carrier) / SPAN).roundToInt()
            if (code in 0..0x10FFFF) sb.appendCodePoint(code)
        }
        return sb.toString()
    }

    /** パルス列を画面表示・共有用の文字列にシリアライズ */
    fun serialize(pulses: List<Pulse>): String =
        pulses.joinToString("\n") { p ->
            "γ=%.3f  T=%.4f°C  IR=%.4f°C  [%d]".format(p.gamma, p.tempC, p.ir, p.code)
        }

    /** 復号が元テキストと一致するか検証（往復テスト） */
    fun verify(text: String): Boolean = decode(encode(text)) == text

    /** パルス列の平均深部体温（ライブ表示の補助） */
    fun meanTemp(pulses: List<Pulse>): Double =
        if (pulses.isEmpty()) BASE else pulses.sumOf { it.tempC } / pulses.size

    /** 2つのパルス列の温度差ノルム（信号類似度の目安） */
    fun distance(a: List<Pulse>, b: List<Pulse>): Double {
        val n = minOf(a.size, b.size)
        var s = 0.0
        for (i in 0 until n) s += abs(a[i].tempC - b[i].tempC)
        return s
    }
}
