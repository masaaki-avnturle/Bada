package com.yamaguchi.bada.desktop

import com.yamaguchi.bada.engine.Predictor
import java.awt.BorderLayout
import java.awt.Color
import java.awt.Dimension
import java.awt.FlowLayout
import java.awt.Font
import java.awt.GridLayout
import javax.swing.BorderFactory
import javax.swing.JButton
import javax.swing.JFileChooser
import javax.swing.JFrame
import javax.swing.JLabel
import javax.swing.JMenu
import javax.swing.JMenuBar
import javax.swing.JMenuItem
import javax.swing.JPanel
import javax.swing.JScrollPane
import javax.swing.JTextArea
import javax.swing.SwingUtilities
import javax.swing.event.DocumentEvent
import javax.swing.event.DocumentListener

/**
 * NoemaKey — 未知事前予知 予測入力 (Windows desktop app).
 *
 * A compact 60% on-screen keyboard with an English/Japanese word-completion +
 * next-word look-ahead bar driven by the Unknown-Prior Engine
 * (com.yamaguchi.bada.engine.Predictor). Load any number of text files to train
 * the predictor; it also learns online from what you type (the append-only
 * reviser loop).
 */
object Theme {
    val BG = Color(0x04, 0x06, 0x0A)
    val PANEL = Color(0x0B, 0x10, 0x18)
    val KEY = Color(0x1A, 0x1F, 0x2A)
    val KEY_ACCENT = Color(0x2A, 0x22, 0x14)
    val GOLD = Color(0xC8, 0xA4, 0x4A)
    val BLUE = Color(0x4A, 0x80, 0xD0)
    val TEXT = Color(0xE6, 0xEA, 0xF0)
    val MUTED = Color(0x8A, 0x94, 0xA4)
}

class NoemaKeyApp {
    private val predictor = Predictor()
    private val editor = JTextArea()
    private val suggestionBar = JPanel(FlowLayout(FlowLayout.LEFT, 6, 4))
    private val statusLabel = JLabel()
    private var shift = false
    lateinit var frame: JFrame
        private set

    /** Test hook: fill the editor so the candidate row renders (screenshots). */
    fun demoFill(text: String) {
        editor.text = text
        editor.caretPosition = text.length
        refreshSuggestions()
    }

    fun show() {
        seedCorpus()

        frame = JFrame("NoemaKey — 未知事前予知 予測入力")
        frame.defaultCloseOperation = JFrame.EXIT_ON_CLOSE
        frame.background = Theme.BG
        frame.jMenuBar = buildMenu(frame)

        val root = JPanel(BorderLayout(0, 6))
        root.background = Theme.BG
        root.border = BorderFactory.createEmptyBorder(10, 10, 10, 10)

        // Header
        val header = JLabel("NoemaKey  ·  未知事前予知エンジン 単語補完・先読み (英語 / 日本語)")
        header.foreground = Theme.GOLD
        header.font = Font(Font.SANS_SERIF, Font.BOLD, 15)
        root.add(header, BorderLayout.NORTH)

        // Center: the editor.
        val center = JPanel(BorderLayout(0, 6))
        center.background = Theme.BG
        editor.background = Theme.PANEL
        editor.foreground = Theme.TEXT
        editor.caretColor = Theme.GOLD
        editor.font = Font(Font.MONOSPACED, Font.PLAIN, 16)
        editor.lineWrap = true
        editor.wrapStyleWord = true
        editor.border = BorderFactory.createEmptyBorder(8, 8, 8, 8)
        val scroll = JScrollPane(editor)
        scroll.preferredSize = Dimension(820, 200)
        scroll.border = BorderFactory.createLineBorder(Theme.KEY)
        center.add(scroll, BorderLayout.CENTER)
        root.add(center, BorderLayout.CENTER)

        // South: [ candidate row (directly above the keyboard) ] + keyboard + status
        val south = JPanel(BorderLayout(0, 4))
        south.background = Theme.BG
        south.add(buildCandidateRow(), BorderLayout.NORTH)
        south.add(buildKeyboard(), BorderLayout.CENTER)
        statusLabel.foreground = Theme.MUTED
        statusLabel.font = Font(Font.SANS_SERIF, Font.PLAIN, 12)
        south.add(statusLabel, BorderLayout.SOUTH)
        root.add(south, BorderLayout.SOUTH)

        editor.document.addDocumentListener(object : DocumentListener {
            override fun insertUpdate(e: DocumentEvent) = refreshSuggestions()
            override fun removeUpdate(e: DocumentEvent) = refreshSuggestions()
            override fun changedUpdate(e: DocumentEvent) = refreshSuggestions()
        })

        frame.contentPane = root
        frame.pack()
        frame.setLocationRelativeTo(null)
        frame.isVisible = true
        refreshStatus()
        refreshSuggestions()
    }

    /**
     * The word-completion candidate row that sits directly on top of the
     * keyboard. Candidates are clickable to insert them.
     */
    private fun buildCandidateRow(): JPanel {
        val row = JPanel(BorderLayout())
        row.background = Theme.PANEL
        // a thin gold rule separates the candidate row from the keys below
        row.border = BorderFactory.createMatteBorder(1, 0, 1, 0, Theme.GOLD)

        val caption = JLabel("  単語補完候補（クリックで入力）")
        caption.foreground = Theme.BLUE
        caption.font = Font(Font.SANS_SERIF, Font.BOLD, 11)
        row.add(caption, BorderLayout.WEST)

        suggestionBar.background = Theme.PANEL
        suggestionBar.border = BorderFactory.createEmptyBorder(2, 4, 2, 4)
        val scroll = JScrollPane(
            suggestionBar,
            JScrollPane.VERTICAL_SCROLLBAR_NEVER,
            JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED
        )
        scroll.border = null
        scroll.background = Theme.PANEL
        scroll.preferredSize = Dimension(820, 46)
        row.add(scroll, BorderLayout.CENTER)
        return row
    }

    // ---- prediction --------------------------------------------------------

    private fun refreshSuggestions() {
        suggestionBar.removeAll()
        val left = editor.text.substring(0, editor.caretPosition.coerceAtMost(editor.text.length))
        val suggestions = predictor.suggest(left, 8)
        if (suggestions.isEmpty()) {
            val l = JLabel("（候補なし — コーパスを読み込むと精度が上がります）")
            l.foreground = Theme.MUTED
            suggestionBar.add(l)
        } else {
            val kind = suggestions.first().kind
            val tag = JLabel(if (kind == "complete") "補完▸" else "先読み▸")
            tag.foreground = Theme.BLUE
            tag.font = Font(Font.SANS_SERIF, Font.BOLD, 12)
            suggestionBar.add(tag)
            for (s in suggestions) {
                val b = JButton("${s.word}  %.0f%%".format(s.probability * 100))
                styleChip(b)
                b.addActionListener { applySuggestion(left, s.word) }
                suggestionBar.add(b)
            }
        }
        suggestionBar.revalidate()
        suggestionBar.repaint()
    }

    /** Insert a chosen suggestion: replace the trailing partial word (if any). */
    private fun applySuggestion(left: String, word: String) {
        val m = Regex("([A-Za-z0-9'\\-]+|[\\u3040-\\u309F\\u30A0-\\u30FF\\u4E00-\\u9FFF\\u3005\\u30FC]+)$").find(left)
        val doc = editor.document
        val caret = editor.caretPosition
        if (m != null) {
            val start = caret - m.value.length
            doc.remove(start, m.value.length)
            doc.insertString(start, "$word ", null)
        } else {
            doc.insertString(caret, "$word ", null)
        }
        predictor.observe(word)
        editor.requestFocus()
        refreshStatus()
    }

    private fun insert(text: String) {
        val doc = editor.document
        doc.insertString(editor.caretPosition, text, null)
        editor.requestFocus()
    }

    private fun backspace() {
        val caret = editor.caretPosition
        if (caret > 0) editor.document.remove(caret - 1, 1)
        editor.requestFocus()
    }

    // ---- corpus ------------------------------------------------------------

    private fun seedCorpus() {
        // bundled resources/corpus/*.txt
        listOf("seed_en.txt", "seed_ja.txt").forEach { name ->
            javaClass.getResourceAsStream("/corpus/$name")?.bufferedReader()?.use {
                predictor.train(it.readText())
            }
        }
    }

    private fun loadFiles(frame: JFrame) {
        val chooser = JFileChooser()
        chooser.isMultiSelectionEnabled = true
        chooser.dialogTitle = "コーパスを読み込む（複数選択可）"
        if (chooser.showOpenDialog(frame) == JFileChooser.APPROVE_OPTION) {
            var n = 0
            for (f in chooser.selectedFiles) {
                try {
                    predictor.train(f.readText(Charsets.UTF_8)); n++
                } catch (_: Exception) { }
            }
            refreshStatus()
            statusLabel.text = "$n 件のファイルを取り込みました。" + statusText()
            refreshSuggestions()
        }
    }

    private fun statusText(): String =
        "  語彙 ${predictor.vocabularySize} · トークン ${predictor.tokenCount}"

    private fun refreshStatus() {
        statusLabel.text = "未知事前予知エンジン 予測入力 ·" + statusText() +
            "  ·  " + com.yamaguchi.bada.engine.CreditGuard.badge()
    }

    // ---- compact keyboard --------------------------------------------------

    private val rows = listOf(
        "Esc 1 2 3 4 5 6 7 8 9 0 - = \\ `",
        "Tab q w e r t y u i o p [ ] Del",
        "Ctrl a s d f g h j k l ; ' Enter",
        "Shift z x c v b n m , . / Shift Fn"
    )

    private fun buildKeyboard(): JPanel {
        val kb = JPanel(GridLayout(rows.size + 1, 1, 4, 4))
        kb.background = Theme.BG
        kb.border = BorderFactory.createEmptyBorder(6, 0, 0, 0)
        for (row in rows) {
            val rp = JPanel(FlowLayout(FlowLayout.CENTER, 4, 0))
            rp.background = Theme.BG
            for (key in row.split(" ")) rp.add(keyButton(key))
            kb.add(rp)
        }
        // bottom row: modifiers + space
        val bottom = JPanel(FlowLayout(FlowLayout.CENTER, 4, 0))
        bottom.background = Theme.BG
        listOf("Alt", "◇").forEach { bottom.add(keyButton(it)) }
        bottom.add(keyButton("Space", 320))
        listOf("◇", "Alt").forEach { bottom.add(keyButton(it)) }
        kb.add(bottom)
        return kb
    }

    private fun keyButton(label: String, width: Int = -1): JButton {
        val b = JButton(label)
        val special = label.length > 1 || label == "◇"
        b.background = if (special) Theme.KEY_ACCENT else Theme.KEY
        b.foreground = if (special) Theme.GOLD else Theme.TEXT
        b.isFocusable = false
        b.font = Font(Font.MONOSPACED, Font.PLAIN, 13)
        b.border = BorderFactory.createLineBorder(Theme.BG, 1)
        val w = when {
            width > 0 -> width
            special -> 58
            else -> 34
        }
        b.preferredSize = Dimension(w, 34)
        b.addActionListener { onKey(label) }
        return b
    }

    private fun onKey(label: String) {
        when (label) {
            "Space" -> { commitWordBeforeCaret(); insert(" ") }
            "Enter" -> { commitWordBeforeCaret(); insert("\n") }
            "Tab" -> insert("\t")
            "Del" -> backspace()
            "Shift" -> shift = !shift
            "Esc", "Ctrl", "Alt", "Fn", "◇" -> { /* modifier / no-op */ }
            else -> {
                val ch = if (label.length == 1 && label[0].isLetter()) {
                    if (shift) label.uppercase() else label.lowercase()
                } else label
                insert(ch)
                if (shift && ch.length == 1 && ch[0].isLetter()) shift = false
            }
        }
    }

    /** When a word boundary is typed, fold the just-finished word into the model. */
    private fun commitWordBeforeCaret() {
        val left = editor.text.substring(0, editor.caretPosition.coerceAtMost(editor.text.length))
        Regex("([A-Za-z0-9'\\-]+|[\\u3040-\\u309F\\u30A0-\\u30FF\\u4E00-\\u9FFF\\u3005\\u30FC]+)$")
            .find(left)?.let { predictor.observe(it.value) }
    }

    private fun styleChip(b: JButton) {
        b.background = Theme.KEY_ACCENT
        b.foreground = Theme.GOLD
        b.isFocusable = false
        b.font = Font(Font.SANS_SERIF, Font.PLAIN, 13)
        b.border = BorderFactory.createEmptyBorder(4, 10, 4, 10)
    }

    private fun buildMenu(frame: JFrame): JMenuBar {
        val bar = JMenuBar()
        val file = JMenu("ファイル")
        val load = JMenuItem("コーパス読み込み（複数選択）…")
        load.addActionListener { loadFiles(frame) }
        val clear = JMenuItem("エディタをクリア")
        clear.addActionListener { editor.text = ""; refreshSuggestions() }
        file.add(load); file.add(clear)
        bar.add(file)

        val credit = JMenu("クレジット保護")
        val show = JMenuItem("量子暗号クレジット（BB84）を表示・検証…")
        show.addActionListener {
            javax.swing.JOptionPane.showMessageDialog(
                frame,
                com.yamaguchi.bada.engine.CreditGuard.report(),
                "量子暗号クレジット保護",
                javax.swing.JOptionPane.INFORMATION_MESSAGE
            )
        }
        val stamp = JMenuItem("エディタ本文にクレジットシールを付与")
        stamp.addActionListener {
            editor.text = com.yamaguchi.bada.engine.CreditGuard.stamp(editor.text)
        }
        credit.add(show); credit.add(stamp)
        bar.add(credit)
        return bar
    }
}

fun main(args: Array<String>) {
    if (args.contains("--selftest")) {
        selfTest()
        return
    }
    val demoIdx = args.indexOf("--demo")
    if (demoIdx >= 0) {
        val out = args.getOrNull(demoIdx + 1) ?: "noemakey.png"
        val app = NoemaKeyApp()
        javax.swing.SwingUtilities.invokeAndWait {
            app.show()
            app.demoFill("the global man")
        }
        Thread.sleep(1200)
        val b = app.frame.bounds
        val img = java.awt.Robot().createScreenCapture(b)
        javax.imageio.ImageIO.write(img, "png", java.io.File(out))
        println("wrote $out (${b.width}x${b.height})")
        kotlin.system.exitProcess(0)
    }
    SwingUtilities.invokeLater { NoemaKeyApp().show() }
}

/** Headless verification of the EN/JA predictor (used in CI and locally). */
private fun selfTest() {
    val p = Predictor()
    listOf("seed_en.txt", "seed_ja.txt").forEach { name ->
        object {}.javaClass.getResourceAsStream("/corpus/$name")?.bufferedReader()?.use { p.train(it.readText()) }
    }
    println("vocab=${p.vocabularySize} tokens=${p.tokenCount}")
    println("complete('man')  -> " + p.complete("man").map { it.word })
    println("complete('多様')  -> " + p.complete("多様").map { it.word })
    println("next('the ')     -> " + p.suggest("the ").map { it.word })
    println("next('多様体 の ') -> " + p.suggest("多様体 の ").map { it.word })
    check(p.vocabularySize > 0) { "empty vocabulary" }
    check(p.complete("man").any { it.word.startsWith("man") }) { "completion failed" }

    // Quantum-crypto credit protection.
    val bb = com.yamaguchi.bada.engine.CreditGuard.bb84(256, 12345L)
    println("BB84: sent=${bb.sent} sifted=${bb.sifted} qber=${bb.qber} keyBytes=${bb.key.size}")
    val content = "generated by NoemaKey"
    val s = com.yamaguchi.bada.engine.CreditGuard.seal(content)
    val ok = com.yamaguchi.bada.engine.CreditGuard.verify(content, s)
    val tamper = com.yamaguchi.bada.engine.CreditGuard.verify(content + "x", s)
    println("fingerprint=${com.yamaguchi.bada.engine.CreditGuard.fingerprint()} verify=$ok tamperRejected=${!tamper}")
    check(bb.qber == 0.0) { "BB84 QBER should be 0 with no eavesdropper" }
    check(bb.key.size == 32) { "key must be 256-bit" }
    check(ok && !tamper) { "seal verify/tamper check failed" }
    println("SELFTEST OK")
}
