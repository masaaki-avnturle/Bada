package com.omega.silenttalk

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import java.util.Locale

/**
 * SilentListener — 「聞き取り」チャネル。
 *
 * マイクから小声/ささやき(subvocalization に最も近い実用入力)を連続音声認識し、
 * 認識テキストをコールバックへ流す。聞き取り開始/停止でライフサイクルを制御する。
 *
 * 注意: 通常端末では純粋な「黙読(無発声)」や心象イメージを直接読むことはできない。
 * 本実装はマイク経由の小声を読み取る、実機で動作する近似である。
 */
class SilentListener(
    private val context: Context,
    private val onPartial: (String) -> Unit,
    private val onFinal: (String) -> Unit,
    private val onStateChange: (Boolean) -> Unit,
    private val onError: (String) -> Unit
) {
    private var recognizer: SpeechRecognizer? = null
    @Volatile var listening = false
        private set
    private var wantContinuous = false

    fun isAvailable(): Boolean = SpeechRecognizer.isRecognitionAvailable(context)

    fun start() {
        if (!isAvailable()) { onError("音声認識が利用できません"); return }
        wantContinuous = true
        beginSession()
    }

    fun stop() {
        wantContinuous = false
        listening = false
        recognizer?.let {
            try { it.stopListening() } catch (_: Exception) {}
            try { it.destroy() } catch (_: Exception) {}
        }
        recognizer = null
        onStateChange(false)
    }

    private fun beginSession() {
        recognizer?.destroy()
        recognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
            setRecognitionListener(handler)
        }
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
        }
        try {
            recognizer?.startListening(intent)
            listening = true
            onStateChange(true)
        } catch (e: Exception) {
            onError("開始失敗: ${e.message}")
        }
    }

    /** 連続聞き取り: 1セッション終了後、停止要求がなければ再開する */
    private fun restartIfWanted() {
        if (wantContinuous) beginSession() else { listening = false; onStateChange(false) }
    }

    private val handler = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {}

        override fun onError(error: Int) {
            // タイムアウト/無音などは連続聞き取りのため静かに再開
            when (error) {
                SpeechRecognizer.ERROR_NO_MATCH,
                SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> restartIfWanted()
                SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> restartIfWanted()
                else -> {
                    onError("認識エラー($error)")
                    restartIfWanted()
                }
            }
        }

        override fun onResults(results: Bundle?) {
            val text = results
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull().orEmpty()
            if (text.isNotBlank()) onFinal(text)
            restartIfWanted()
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val text = partialResults
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull().orEmpty()
            if (text.isNotBlank()) onPartial(text)
        }

        override fun onEvent(eventType: Int, params: Bundle?) {}
    }
}
