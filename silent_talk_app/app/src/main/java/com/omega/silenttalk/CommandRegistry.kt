package com.omega.silenttalk

import java.util.Locale

/**
 * CommandRegistry — 合言葉(フレーズ) → コマンド の対応表。
 *
 * Silent Talk が聞き取った（黙読/小声を音声認識した）フレーズを正規化し、
 * 登録された合言葉に一致したらコマンドを返す。
 */
object CommandRegistry {

    data class Command(
        val id: String,
        val phrases: List<String>,   // 合言葉（複数の言い回し）
        val description: String
    )

    /** 起動・停止の合言葉（リスナー制御用） */
    val WAKE_PHRASES = listOf("聞き取り開始", "サイレント開始", "start listening", "silent start")
    val SLEEP_PHRASES = listOf("聞き取り停止", "サイレント停止", "stop listening", "silent stop")

    val commands: List<Command> = listOf(
        Command("encode",  listOf("符号化", "信号化", "encode"),       "現在のテキストを無音信号へ符号化"),
        Command("decode",  listOf("復号", "デコード", "decode"),         "直近の信号を復号"),
        Command("clear",   listOf("クリア", "消去", "clear"),           "入力と出力をクリア"),
        Command("keyboard",listOf("キーボード", "入力切替", "keyboard"), "Silent Talk キーボードに切替"),
        Command("sensor",  listOf("センサー", "温度", "sensor"),         "センサーバーを即時更新"),
        Command("help",    listOf("ヘルプ", "助けて", "help", "コマンド"),"使える合言葉を表示")
    )

    private fun normalize(s: String): String =
        s.trim().lowercase(Locale.getDefault())
            .replace("[\\s　,.。、！!？?]+".toRegex(), "")

    private fun matchesAny(text: String, phrases: List<String>): Boolean {
        val n = normalize(text)
        return phrases.any { n.contains(normalize(it)) }
    }

    fun isWake(text: String): Boolean = matchesAny(text, WAKE_PHRASES)
    fun isSleep(text: String): Boolean = matchesAny(text, SLEEP_PHRASES)

    /** フレーズに一致するコマンドを返す（なければ null）。 */
    fun match(text: String): Command? =
        commands.firstOrNull { matchesAny(text, it.phrases) }

    fun helpText(): String = buildString {
        append("合言葉(コマンド):\n")
        append("・起動: ${WAKE_PHRASES.joinToString(" / ")}\n")
        append("・停止: ${SLEEP_PHRASES.joinToString(" / ")}\n")
        for (c in commands)
            append("・${c.phrases.joinToString(" / ")} → ${c.description}\n")
    }
}
