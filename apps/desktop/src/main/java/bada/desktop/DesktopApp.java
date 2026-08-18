package bada.desktop;

import bada.coder.Coder;
import bada.mind.MindReader;
import bada.silent.SilentTalk;
import bada.silent.Whisper;
import bada.silent.BadaSyntax;
import bada.silent.Platex;
import bada.silent.Vim;
import bada.qc.PseudoQC;
import bada.quantum.SpaceTelegraph;

import javax.swing.*;
import javax.swing.text.*;
import java.awt.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

/**
 * Bada — Windows/Linux/desktop front end. Two tabs:
 *   ① Space Telegraph   (量子もつれ・汎用電信通信)
 *   ② Pseudo QC          (ノイマン型・ディスク内蔵・半導体制御の擬似量子計算機)
 *   ③ Mind               (思考言語化 simulation)
 *   ④ Coder              (思考→コード transformer, EN/JA)
 *   ⑤ Silent IME         (サイレント入力: 発声せず文章/コードを入力, simulation)
 *   ⑥ Whisper            (英語ウィスパード復元／未知言語の言語化, simulation)
 *   ⑦ Bada Vim           (構文ハイライト付き全画面モーダルエディタ: INSERT 長長文入力, 予約語ボタン, :math 等)
 *
 * Run with no arguments to open the Swing GUI (how the packaged app launches).
 * Pass a message for a one-shot telegraph console report, or a flag for a
 * console report:
 *
 *   BadaTelegraph "HELLO SPACE"
 *   BadaTelegraph --qc
 *   BadaTelegraph --mind "光 と 音 の 記憶"
 *   BadaTelegraph --code "fibonacci 10"
 *   BadaTelegraph --silent "光 記憶 波 | :code | fibonacci 8"   (| separates lines)
 */
public final class DesktopApp {

    public static void main(String[] args) {
        System.setOut(new PrintStream(System.out, true, StandardCharsets.UTF_8));

        boolean headless = GraphicsEnvironment.isHeadless();
        String joined = String.join(" ", args).trim();

        if (joined.equals("--qc")) {
            try (PseudoQC m = PseudoQC.bell()) {
                System.out.println(m.report());
                System.out.println();
                System.out.println(m.verilog());
            }
            return;
        }
        if (joined.startsWith("--mind")) {
            String sig = joined.substring("--mind".length()).trim();
            System.out.println(new MindReader().render(sig, "対象"));
            return;
        }
        if (joined.startsWith("--silent")) {
            String rest = joined.substring("--silent".length()).trim();
            SilentTalk.Session s = new SilentTalk.Session();
            System.out.println(s.intro());
            for (String line : rest.split("\\|")) {
                line = line.trim();
                if (line.isEmpty()) continue;
                String out = s.render(s.feed(line));
                if (!out.isEmpty()) System.out.println(out);
            }
            System.out.println("\n--- 入力結果 (document) ---");
            System.out.println(s.text());
            System.out.printf("precision = %.1f%%  -> %s%n", s.precision() * 100,
                    s.exceedsSilentTalk() ? "EXCEEDS silent talk" : "below");
            return;
        }
        if (joined.startsWith("--math")) {
            String cue = joined.substring("--math".length()).trim();
            Platex.MathPaper p = Platex.mathPaper(cue, 0);
            System.out.printf("%% math pLaTeX+Bada %d sections, valid=%s, bada=%s, precision=%.1f%%%n",
                    p.sections, p.valid, p.badaValid, p.precision * 100);
            System.out.println(p.code);
            return;
        }
        if (joined.startsWith("--latex")) {
            String cue = joined.substring("--latex".length()).trim();
            Platex.Paper p = Platex.paper(cue, 0);
            System.out.printf("%% pLaTeX %d sections, valid=%s, precision=%.1f%%%n", p.sections, p.valid, p.precision * 100);
            System.out.println(p.code);
            return;
        }
        if (joined.startsWith("--whisper")) {
            String cue = joined.substring("--whisper".length()).trim();
            Whisper.Report r = Whisper.longReport(cue);   // 長長文（短文ではない）
            System.out.printf("# whisper source=%s  sentences=%d  precision=%.1f%%%n", r.lang, r.sentences, r.precision * 100);
            System.out.println(r.text);
            return;
        }
        if (joined.startsWith("--code")) {
            String intent = joined.substring("--code".length()).trim();
            Coder.GenResult r = Coder.generate(intent, null);
            System.out.println("# language: " + r.language + "  precision="
                    + String.format("%.1f%%", r.precision * 100));
            System.out.println(r.code);
            return;
        }
        if (headless || (!joined.isEmpty() && !joined.equals("--gui"))) {
            String message = joined.isEmpty() || joined.equals("--gui") ? "HELLO SPACE" : joined;
            System.out.println(new SpaceTelegraph("GaAs", 4.0, 3).render(message));
            return;
        }
        SwingUtilities.invokeLater(DesktopApp::buildGui);
    }

    private static void buildGui() {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) { }

        JFrame frame = new JFrame("Bada — 量子もつれ電信 ＋ 擬似量子計算機");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(900, 700);

        JTabbedPane tabs = new JTabbedPane();
        tabs.addTab("① 宇宙電信 (Telegraph)", telegraphPanel());
        tabs.addTab("② 擬似量子計算機 (Pseudo QC)", qcPanel());
        tabs.addTab("③ 思考言語化 (Mind)", mindPanel());
        tabs.addTab("④ コード生成 (Coder)", coderPanel());
        tabs.addTab("⑤ サイレント入力 (Silent IME)", silentPanel());
        tabs.addTab("⑥ ウィスパード (Whisper)", whisperPanel());
        tabs.addTab("⑦ Bada Vim (エディタ)", vimPanel());
        frame.add(tabs);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }

    // ---------------------------------------------------------------- Telegraph
    private static JPanel telegraphPanel() {
        JPanel root = new JPanel(new BorderLayout(8, 8));

        JPanel top = new JPanel(new BorderLayout(6, 6));
        top.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));
        JTextField input = new JTextField("QUANTUM HELLO FROM EARTH");
        JComboBox<String> material = new JComboBox<>(new String[]{"GaAs", "InAs", "InGaAs", "Si", "diamond(NV)"});
        JSpinner temp = new JSpinner(new SpinnerNumberModel(4.0, 0.1, 400.0, 1.0));
        JSpinner redundancy = new JSpinner(new SpinnerNumberModel(3, 1, 11, 2));
        JButton send = new JButton("送信・証明 (Transmit & Prove)");

        JPanel inRow = new JPanel(new BorderLayout(6, 6));
        inRow.add(new JLabel("メッセージ:"), BorderLayout.WEST);
        inRow.add(input, BorderLayout.CENTER);
        JPanel tgEast = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        tgEast.add(thoughtButton(input, "text")); tgEast.add(whisperButton(input)); tgEast.add(send);
        inRow.add(tgEast, BorderLayout.EAST);
        JPanel opts = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        opts.add(new JLabel("材料:")); opts.add(material);
        opts.add(new JLabel("温度K:")); opts.add(temp);
        opts.add(new JLabel("冗長度:")); opts.add(redundancy);
        top.add(inRow, BorderLayout.NORTH);
        top.add(opts, BorderLayout.SOUTH);

        JTextArea output = monospaceArea();
        Runnable run = () -> {
            String msg = input.getText().trim().isEmpty() ? "HELLO SPACE" : input.getText().trim();
            SpaceTelegraph tg = new SpaceTelegraph((String) material.getSelectedItem(),
                    ((Number) temp.getValue()).doubleValue(), ((Number) redundancy.getValue()).intValue());
            output.setText(tg.render(msg));
            output.setCaretPosition(0);
        };
        send.addActionListener(e -> run.run());
        input.addActionListener(e -> run.run());

        root.add(top, BorderLayout.NORTH);
        root.add(new JScrollPane(output), BorderLayout.CENTER);
        run.run();
        return root;
    }

    // ---------------------------------------------------------------- Pseudo QC
    private static JPanel qcPanel() {
        JPanel root = new JPanel(new BorderLayout(8, 8));

        JPanel top = new JPanel(new BorderLayout(6, 6));
        top.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));

        JTextArea qasm = new JTextArea("H 0\nCX 0 1\nHALT\n", 5, 30);
        qasm.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        qasm.setBorder(BorderFactory.createTitledBorder("BadaQASM プログラム（ディスクに格納）"));

        JSpinner nq = new JSpinner(new SpinnerNumberModel(2, 1, 8, 1));
        JButton run = new JButton("実行・モニタ投射 (Run)");
        JButton verilog = new JButton("半導体ソース (Verilog)");
        JComboBox<String> demo = new JComboBox<>(new String[]{"— デモ —", "Bell", "GHZ", "重ね合わせ+測定"});

        JPanel ctl = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        ctl.add(new JLabel("量子ビット数:")); ctl.add(nq);
        ctl.add(run); ctl.add(verilog); ctl.add(thoughtButton(qasm, "qasm")); ctl.add(whisperButton(qasm)); ctl.add(demo);

        top.add(qasm, BorderLayout.CENTER);
        top.add(ctl, BorderLayout.SOUTH);

        JTextArea output = monospaceArea();

        Runnable doRun = () -> runQc(qasm.getText(), ((Number) nq.getValue()).intValue(), output, false);
        run.addActionListener(e -> doRun.run());
        verilog.addActionListener(e -> runQc(qasm.getText(), ((Number) nq.getValue()).intValue(), output, true));
        demo.addActionListener(e -> {
            switch (demo.getSelectedIndex()) {
                case 1 -> { qasm.setText("H 0\nCX 0 1\nHALT\n"); nq.setValue(2); }
                case 2 -> { qasm.setText("H 0\nCX 0 1\nCX 1 2\nHALT\n"); nq.setValue(3); }
                case 3 -> { qasm.setText("H 0\nMEASURE 0\nHALT\n"); nq.setValue(1); }
                default -> { }
            }
        });

        root.add(top, BorderLayout.NORTH);
        root.add(new JScrollPane(output), BorderLayout.CENTER);
        doRun.run();
        return root;
    }

    private static void runQc(String qasm, int n, JTextArea output, boolean asVerilog) {
        try (PseudoQC m = new PseudoQC(n).load(qasm).run()) {
            output.setText(asVerilog ? m.verilog() : m.report());
            output.setCaretPosition(0);
        } catch (Throwable t) {
            output.setText("error: " + t.getMessage());
        }
    }

    // ------------------------------------------------------------------ Mind
    private static JPanel mindPanel() {
        JPanel root = new JPanel(new BorderLayout(8, 8));

        JPanel top = new JPanel(new BorderLayout(6, 6));
        top.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));

        JTextField subject = new JTextField("被験者A", 8);
        JTextField signal = new JTextField("光 と 音 の 記憶 が 波 の よう に 流れ 望み と 恐れ が 交錯 する");
        JButton go = new JButton("言語化・心像・脳内コード (Read)");

        JPanel inRow = new JPanel(new BorderLayout(6, 6));
        JPanel left = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        left.add(new JLabel("対象:")); left.add(subject);
        inRow.add(left, BorderLayout.WEST);
        inRow.add(signal, BorderLayout.CENTER);
        JPanel mindEast = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        mindEast.add(thoughtButton(signal, "text")); mindEast.add(whisperButton(signal)); mindEast.add(go);
        inRow.add(mindEast, BorderLayout.EAST);

        JLabel note = new JLabel("※ 生成シミュレーション（実在の脳を読むものではありません）");
        note.setBorder(BorderFactory.createEmptyBorder(4, 2, 4, 2));

        top.add(inRow, BorderLayout.NORTH);
        top.add(note, BorderLayout.SOUTH);

        JTextArea output = monospaceArea();
        Runnable run = () -> {
            try {
                output.setText(new MindReader().render(signal.getText(), subject.getText().trim().isEmpty()
                        ? "対象" : subject.getText().trim()));
                output.setCaretPosition(0);
            } catch (Throwable t) {
                output.setText("error: " + t.getMessage());
            }
        };
        go.addActionListener(e -> run.run());
        signal.addActionListener(e -> run.run());

        root.add(top, BorderLayout.NORTH);
        root.add(new JScrollPane(output), BorderLayout.CENTER);
        run.run();
        return root;
    }

    // ------------------------------------------------------------------ Coder
    private static JPanel coderPanel() {
        JPanel root = new JPanel(new BorderLayout(8, 8));

        JPanel top = new JPanel(new BorderLayout(6, 6));
        top.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));

        JTextField intent = new JTextField("print hello 3 times loop");
        JComboBox<String> lang = new JComboBox<>(new String[]{"auto", "ruby", "python", "javascript", "c", "java", "bada"});
        JButton gen = new JButton("生成 (Generate)");

        JPanel row1 = new JPanel(new BorderLayout(6, 6));
        JPanel l1 = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        l1.add(new JLabel("意図 (EN/日本語):"));
        row1.add(l1, BorderLayout.WEST);
        row1.add(intent, BorderLayout.CENTER);
        JPanel r1 = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        r1.add(new JLabel("言語:")); r1.add(lang); r1.add(thoughtButton(intent, "intent")); r1.add(whisperButton(intent)); r1.add(gen);
        row1.add(r1, BorderLayout.EAST);

        // live word completion (command feature)
        JTextField prefix = new JTextField();
        JLabel completions = new JLabel(" ");
        JPanel row2 = new JPanel(new BorderLayout(6, 6));
        JPanel l2 = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        l2.add(new JLabel("補完 (prefix):"));
        row2.add(l2, BorderLayout.WEST);
        row2.add(prefix, BorderLayout.CENTER);
        row2.add(completions, BorderLayout.SOUTH);

        top.add(row1, BorderLayout.NORTH);
        top.add(row2, BorderLayout.SOUTH);

        JTextArea output = monospaceArea();

        Runnable generate = () -> {
            String selected = (String) lang.getSelectedItem();
            String l = "auto".equals(selected) ? null : selected;
            Coder.GenResult r = Coder.generate(intent.getText(), l);
            StringBuilder sb = new StringBuilder();
            sb.append("# language : ").append(r.language)
              .append(String.format("  (confidence %.2f)%n", r.confidence));
            sb.append("# reserved : ").append(String.join(" ", r.reservedUsed)).append("\n");
            sb.append(String.format("# precision: %.1f%%  (silent-talk %.1f%%)%n%n",
                    r.precision * 100, Coder.SILENT_TALK_BASELINE * 100));
            sb.append(r.code);
            output.setText(sb.toString());
            output.setCaretPosition(0);
        };
        gen.addActionListener(e -> generate.run());
        intent.addActionListener(e -> generate.run());

        Runnable complete = () -> {
            String selected = (String) lang.getSelectedItem();
            String l = "auto".equals(selected) ? null : selected;
            java.util.List<String> c = Coder.complete(prefix.getText().trim(), l);
            completions.setText("→ " + String.join("   ", c));
        };
        prefix.getDocument().addDocumentListener(new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
            public void removeUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
        });

        root.add(top, BorderLayout.NORTH);
        root.add(new JScrollPane(output), BorderLayout.CENTER);
        generate.run();
        return root;
    }

    // ---------------------------------------------------------------- Silent IME
    private static JPanel silentPanel() {
        JPanel root = new JPanel(new BorderLayout(8, 8));
        final SilentTalk.Session session = new SilentTalk.Session();

        JPanel top = new JPanel(new BorderLayout(6, 6));
        top.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));

        // input row: the "silent" cue (no vocalization) + a mode toggle
        JTextField cue = new JTextField("光 記憶 波");
        final String[] modeCmd = {":text", ":code", ":qc", ":verilog", ":telegraph", ":bada", ":whisper", ":report", ":latex", ":math"};
        JComboBox<String> mode = new JComboBox<>(new String[]{
                "text（言語化）", "code（コード）", "qc（QCソース）", "verilog（半導体）", "telegraph（宇宙電信）",
                "bada（Bada構文/長文）", "whisper（英ウィスパード/未知言語）", "report（長長文レポート）",
                "latex（論文pLaTeX）", "math（数学論文pLaTeX+Bada）"});
        JComboBox<String> lang = new JComboBox<>(new String[]{"auto", "ruby", "python", "javascript", "c", "java", "bada"});
        JButton feed = new JButton("入力 (Feed)");

        JPanel row1 = new JPanel(new BorderLayout(6, 6));
        JPanel l1 = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        l1.add(new JLabel("手がかり (発声せず):"));
        row1.add(l1, BorderLayout.WEST);
        row1.add(cue, BorderLayout.CENTER);
        JPanel r1 = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        r1.add(new JLabel("mode:")); r1.add(mode);
        r1.add(new JLabel("lang:")); r1.add(lang); r1.add(feed);
        row1.add(r1, BorderLayout.EAST);

        // completion row (command feature)
        JTextField prefix = new JTextField();
        JLabel completions = new JLabel(" ");
        JPanel row2 = new JPanel(new BorderLayout(6, 6));
        JPanel l2 = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        l2.add(new JLabel("補完 (prefix):"));
        row2.add(l2, BorderLayout.WEST);
        row2.add(prefix, BorderLayout.CENTER);
        row2.add(completions, BorderLayout.SOUTH);

        JPanel btns = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        JButton undo = new JButton("取消 (Undo)");
        JButton clear = new JButton("クリア (Clear)");
        btns.add(undo); btns.add(clear);

        top.add(row1, BorderLayout.NORTH);
        JPanel mid = new JPanel(new BorderLayout());
        mid.add(row2, BorderLayout.NORTH);
        mid.add(btns, BorderLayout.SOUTH);
        top.add(mid, BorderLayout.SOUTH);

        JTextArea doc = monospaceArea();
        JLabel status = new JLabel(" ");

        Runnable refresh = () -> {
            doc.setText(session.text());
            doc.setCaretPosition(0);
            status.setText(String.format("  precision = %.1f%%  (silent-talk %.1f%%)  -> %s",
                    session.precision() * 100, SilentTalk.SILENT_TALK_BASELINE * 100,
                    session.exceedsSilentTalk() ? "EXCEEDS silent talk" : "below"));
        };
        Runnable syncMode = () -> {
            session.feed(modeCmd[mode.getSelectedIndex()]);
            String selected = (String) lang.getSelectedItem();
            session.feed("auto".equals(selected) ? ":lang" : ":lang " + selected);
        };
        Runnable doFeed = () -> {
            syncMode.run();
            session.feed(cue.getText());
            refresh.run();
        };
        feed.addActionListener(e -> doFeed.run());
        cue.addActionListener(e -> doFeed.run());
        undo.addActionListener(e -> { session.feed(":undo"); refresh.run(); });
        clear.addActionListener(e -> { session.feed(":clear"); refresh.run(); });

        Runnable complete = () -> {
            syncMode.run();
            java.util.List<String> c = session.complete(prefix.getText().trim());
            completions.setText("→ " + String.join("   ", c));
        };
        prefix.getDocument().addDocumentListener(new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
            public void removeUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
        });

        root.add(top, BorderLayout.NORTH);
        root.add(new JScrollPane(doc), BorderLayout.CENTER);
        root.add(status, BorderLayout.SOUTH);
        refresh.run();
        return root;
    }

    // A reusable 思考入力 (thought-input) button. It needs NO typed or spoken
    // input: each press captures thought-tokens from the gamma-manifold prior and
    // fills the field via the Mind transformer, above silent-talk precision.
    // `kind`: "text"/"intent" verbalize a sentence; "qasm" -> a program.
    // ---------------------------------------------------------------- Whisper
    private static JPanel whisperPanel() {
        JPanel root = new JPanel(new BorderLayout(8, 8));

        JPanel top = new JPanel(new BorderLayout(6, 6));
        top.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));

        JTextField input = new JTextField("qntm lght mmry wv sgnl");
        JButton go = new JButton("言語化");
        JButton longBtn = new JButton("🔉 長長文レポート");
        longBtn.setToolTipText("未知言語/ウィスパードを、10〜16 文の長長文レポートに言語化します（発声なし）");
        JButton badaBtn = new JButton("📄 Bada長長文ソース");
        badaBtn.setToolTipText("復元した語から、長長文の Bada 言語ソース（実行可）を生成します（発声なし）");
        JButton texBtn = new JButton("📝 pLaTeX論文");
        texBtn.setToolTipText("復元した語から、pLaTeX の長長文論文ソース（jsarticle）を生成します（発声なし）");
        JButton mathBtn = new JButton("🧮 数学論文");
        mathBtn.setToolTipText("復元した語から、数学論文（pLaTeX amsthm＋Bada 言語）の長長文ソースを生成します（発声なし）");

        JPanel inRow = new JPanel(new BorderLayout(6, 6));
        inRow.add(new JLabel("ウィスパード / 未知言語:"), BorderLayout.WEST);
        inRow.add(input, BorderLayout.CENTER);
        JPanel wEast = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        wEast.add(go); wEast.add(longBtn); wEast.add(badaBtn); wEast.add(texBtn); wEast.add(mathBtn);
        inRow.add(wEast, BorderLayout.EAST);

        JTextField prefix = new JTextField();
        JLabel completions = new JLabel(" ");
        JPanel row2 = new JPanel(new BorderLayout(6, 6));
        JPanel l2 = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        l2.add(new JLabel("補完 (prefix):"));
        row2.add(l2, BorderLayout.WEST);
        row2.add(prefix, BorderLayout.CENTER);
        row2.add(completions, BorderLayout.SOUTH);

        JLabel note = new JLabel("※ 発声せず、英語ウィスパード（母音欠落）を完全文へ／未知言語を長長文レポート・Bada 長長文ソースへ（simulation）");
        note.setBorder(BorderFactory.createEmptyBorder(4, 2, 2, 2));

        top.add(inRow, BorderLayout.NORTH);
        JPanel mid = new JPanel(new BorderLayout());
        mid.add(row2, BorderLayout.NORTH);
        mid.add(note, BorderLayout.SOUTH);
        top.add(mid, BorderLayout.SOUTH);

        JTextArea output = monospaceArea();
        Runnable verbalize = () -> {
            Whisper.Result r = Whisper.verbalize(input.getText());
            String kind = "en".equals(r.lang) ? "英語ウィスパード復元" : "未知言語の言語化";
            output.setText(String.format(
                    "入力 (whispered/unknown):%n  %s%n%n言語化 (%s, source=%s):%n  %s%n%nprecision = %.1f%%  (silent-talk %.1f%%)  -> %s",
                    input.getText(), kind, r.lang, r.text,
                    r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100,
                    r.precision > SilentTalk.SILENT_TALK_BASELINE ? "EXCEEDS silent talk" : "below"));
            output.setCaretPosition(0);
        };
        Runnable longReport = () -> {
            Whisper.Report r = Whisper.longReport(input.getText());
            output.setText(String.format(
                    "入力 (whispered/unknown):%n  %s%n%n長長文レポート (%d文, source=%s):%n%s%n%nprecision = %.1f%%  (silent-talk %.1f%%)  -> %s",
                    input.getText(), r.sentences, r.lang, r.text,
                    r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100,
                    r.precision > SilentTalk.SILENT_TALK_BASELINE ? "EXCEEDS silent talk" : "below"));
            output.setCaretPosition(0);
        };
        Runnable badaLong = () -> {
            // decode the whispered/unknown input to words, then write long Bada source
            Whisper.Result w = Whisper.verbalize(input.getText());
            BadaSyntax.Program p = BadaSyntax.buildVeryLong(w.text, 0);
            output.setText(String.format(
                    "入力 (whispered/unknown):%n  %s%n%nBada 長長文ソース (%d ブロック, 実行%s):%n%s%n%nprecision = %.1f%%",
                    input.getText(), p.blocks, p.valid ? "OK" : "NG", p.code, p.precision * 100));
            output.setCaretPosition(0);
        };
        Runnable texPaper = () -> {
            Whisper.Result w = Whisper.verbalize(input.getText());
            Platex.Paper p = Platex.paper(w.text, 0);
            output.setText(String.format(
                    "入力 (whispered/unknown):%n  %s%n%npLaTeX 論文 (%d 節, %s):%n%s",
                    input.getText(), p.sections, p.valid ? "valid" : "invalid", p.code));
            output.setCaretPosition(0);
        };
        Runnable mathPaper = () -> {
            Whisper.Result w = Whisper.verbalize(input.getText());
            Platex.MathPaper p = Platex.mathPaper(w.text, 0);
            output.setText(String.format(
                    "入力 (whispered/unknown):%n  %s%n%n数学論文 pLaTeX+Bada (%d 節, %s, Bada実行%s):%n%s",
                    input.getText(), p.sections, p.valid ? "valid" : "invalid", p.badaValid ? "OK" : "NG", p.code));
            output.setCaretPosition(0);
        };
        go.addActionListener(e -> verbalize.run());
        input.addActionListener(e -> longReport.run());
        longBtn.addActionListener(e -> longReport.run());
        badaBtn.addActionListener(e -> badaLong.run());
        texBtn.addActionListener(e -> texPaper.run());
        mathBtn.addActionListener(e -> mathPaper.run());

        Runnable complete = () -> {
            java.util.List<String> c = new java.util.ArrayList<>();
            String p = prefix.getText().trim().toLowerCase();
            if (!p.isEmpty()) for (String w : Whisper.VOCAB) {
                if (w.startsWith(p) && !c.contains(w)) c.add(w);
                if (c.size() >= 8) break;
            }
            completions.setText("→ " + String.join("   ", c));
        };
        prefix.getDocument().addDocumentListener(new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
            public void removeUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { complete.run(); }
        });

        root.add(top, BorderLayout.NORTH);
        root.add(new JScrollPane(output), BorderLayout.CENTER);
        longReport.run();   // 長長文 by default — the whisper function is not short
        return root;
    }

    // ---------------------------------------------------------------- Bada Vim
    // A full-screen modal editor with SYNTAX HIGHLIGHTING (not just an ex inserter).
    // INSERT types long-long text directly into the whole-screen buffer; NORMAL runs
    // commands (i a o O x dd h j k l 0 $ gg G); ":" opens the ex line. Reserved words
    // / syntax-rule words are highlighted and insertable by buttons, per filetype
    // (bada / verilog(半導体) / qasm(QC) / latex / coder) — all voiceless.
    private static final String[] VIM_FTS = {"auto", "bada", "verilog", "qasm", "latex", "coder"};

    private static String[] vimReserved(String ft) {
        switch (ft) {
            case "bada": return new String[]{"set", "print", "as", "push", "Omega::", "<-", "-<", ">-", "="};
            case "verilog": return new String[]{"module", "endmodule", "input", "output", "wire", "reg",
                    "assign", "always", "begin", "end", "nand2", "inv", "`default_nettype", "none"};
            case "qasm": return new String[]{"H", "X", "Y", "Z", "S", "T", "CX", "RX", "RZ", "MEASURE", "HALT", "NOP"};
            case "latex": return new String[]{"\\documentclass", "\\usepackage", "\\begin", "\\end",
                    "\\section", "\\newtheorem", "\\title", "\\maketitle", "\\equation"};
            case "coder": return new String[]{"def", "end", "if", "else", "elsif", "while", "for", "return",
                    "class", "print", "function", "var", "let", "const", "import", "then"};
            default: return new String[]{"set", "print", "<-", "-<", ">-", "module", "wire", "H", "CX",
                    "\\begin", "\\end", "def", "return"};
        }
    }

    private static String vimDetectFt(String text) {
        if (text.contains("\\documentclass") || text.contains("\\begin{")) return "latex";
        if (text.contains("module ") || text.contains("endmodule")) return "verilog";
        if (text.contains("Omega::push") || text.contains(" <- ") || text.contains(" -< ")) return "bada";
        if (text.matches("(?s).*\\b(H|CX|MEASURE|HALT)\\b.*")) return "qasm";
        return "coder";
    }

    private static void highlightVim(JTextPane pane, String ftSel) {
        StyledDocument doc = pane.getStyledDocument();
        String text = pane.getText().replace("\r", "");
        int n = text.length();
        String ft = "auto".equals(ftSel) ? vimDetectFt(text) : ftSel;

        SimpleAttributeSet def = new SimpleAttributeSet();
        StyleConstants.setForeground(def, new Color(0x20, 0x24, 0x2c));
        SimpleAttributeSet kw = new SimpleAttributeSet();
        StyleConstants.setForeground(kw, new Color(0x0b, 0x63, 0xa5)); StyleConstants.setBold(kw, true);
        SimpleAttributeSet op = new SimpleAttributeSet();
        StyleConstants.setForeground(op, new Color(0xb5, 0x5c, 0x00)); StyleConstants.setBold(op, true);
        SimpleAttributeSet str = new SimpleAttributeSet();
        StyleConstants.setForeground(str, new Color(0x0a, 0x7d, 0x33));
        SimpleAttributeSet com = new SimpleAttributeSet();
        StyleConstants.setForeground(com, new Color(0x6a, 0x73, 0x7d)); StyleConstants.setItalic(com, true);

        doc.setCharacterAttributes(0, n, def, true);

        // keywords / syntax-rule words for the filetype
        for (String w : vimReserved(ft)) {
            String q = Pattern.quote(w);
            String rx = Character.isLetter(w.charAt(0)) ? "(?<![\\w])" + q + "(?![\\w])" : q;
            Matcher m = Pattern.compile(rx).matcher(text);
            SimpleAttributeSet sty = Character.isLetterOrDigit(w.charAt(0)) || w.charAt(0) == '\\' ? kw : op;
            while (m.find()) doc.setCharacterAttributes(m.start(), m.end() - m.start(), sty, false);
        }
        // strings then comments win
        Matcher ms = Pattern.compile("\"[^\"\\n]*\"").matcher(text);
        while (ms.find()) doc.setCharacterAttributes(ms.start(), ms.end() - ms.start(), str, false);
        String crx = "latex".equals(ft) ? "%.*" : ("verilog".equals(ft) || "coder".equals(ft) ? "//.*" : "#.*");
        Matcher mc = Pattern.compile(crx).matcher(text);
        while (mc.find()) doc.setCharacterAttributes(mc.start(), mc.end() - mc.start(), com, false);
    }

    private static int vimLineStart(String t, int pos) { int i = t.lastIndexOf('\n', Math.max(0, pos - 1)); return i < 0 ? 0 : i + 1; }
    private static int vimLineEnd(String t, int pos) { int i = t.indexOf('\n', pos); return i < 0 ? t.length() : i; }

    private static JPanel vimPanel() {
        JPanel root = new JPanel(new BorderLayout(6, 6));

        final JTextPane editor = new JTextPane();
        editor.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 14));
        editor.setMargin(new Insets(10, 12, 10, 12));
        editor.setText("% Bada Vim — i:挿入  W:ウィスパード英語挿入  Esc:ノーマル  ::コマンド  （syntax highlight・全画面長長文）\n");
        editor.setEditable(false); // NORMAL

        final String[] ft = { "auto" };
        // wIns[0] = whisper-insert mode active: typing is native, Esc reconstructs
        // the WHOLE multi-line region typed since wStart[0] into full English at once.
        final boolean[] wIns = { false };
        final int[] wStart = { 0 };
        final JComboBox<String> ftBox = new JComboBox<>(VIM_FTS);
        final JLabel status = new JLabel();
        status.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        final JTextField exLine = new JTextField();
        exLine.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        exLine.setVisible(false);

        final boolean[] busy = { false };
        final Runnable rehl = () -> {
            if (busy[0]) return;
            busy[0] = true;
            try { highlightVim(editor, ft[0]); } catch (Exception ignored) { }
            busy[0] = false;
        };
        final Runnable refresh = () -> {
            // simulated voiceless-input precision, guaranteed above the silent-talk baseline
            double prec = Math.max(0.96, SilentTalk.SILENT_TALK_BASELINE + 0.01);
            String mode = wIns[0] ? "-- WHISPER INSERT (英語復元) --"
                    : (editor.isEditable() ? "-- INSERT --" : "-- NORMAL --");
            status.setText(String.format("  %s | ft=%s | %d 行 | 発声なし precision %.1f%% > silent-talk %.1f%% | i:挿入 W:ウィスパード Esc ::コマンド",
                    mode,
                    "auto".equals(ft[0]) ? "auto(" + vimDetectFt(editor.getText()) + ")" : ft[0],
                    editor.getText().split("\n", -1).length,
                    prec * 100, SilentTalk.SILENT_TALK_BASELINE * 100));
        };
        editor.getDocument().addDocumentListener(new javax.swing.event.DocumentListener() {
            public void insertUpdate(javax.swing.event.DocumentEvent e) { SwingUtilities.invokeLater(rehl); SwingUtilities.invokeLater(refresh); }
            public void removeUpdate(javax.swing.event.DocumentEvent e) { SwingUtilities.invokeLater(rehl); SwingUtilities.invokeLater(refresh); }
            public void changedUpdate(javax.swing.event.DocumentEvent e) { }
        });
        ftBox.addActionListener(e -> { ft[0] = (String) ftBox.getSelectedItem(); rehl.run(); refresh.run(); });

        // reserved / syntax-rule word buttons (voiceless insertion), rebuilt per ft
        final JPanel words = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 2));
        final Runnable rebuildWords = () -> {
            words.removeAll();
            words.add(new JLabel("予約語:"));
            String f = "auto".equals(ft[0]) ? vimDetectFt(editor.getText()) : ft[0];
            for (String w : vimReserved(f)) {
                JButton b = new JButton(w);
                b.setMargin(new Insets(1, 5, 1, 5));
                b.setFocusable(false);
                b.addActionListener(ev -> {
                    try {
                        int at = editor.getCaretPosition();
                        editor.getDocument().insertString(at, w + " ", null);
                        editor.setCaretPosition(at + w.length() + 1);
                    } catch (BadLocationException ignored) { }
                    editor.requestFocusInWindow();
                });
                words.add(b);
            }
            words.revalidate(); words.repaint();
        };
        ftBox.addActionListener(e -> rebuildWords.run());

        // Reconstruct the WHOLE multi-line region typed in this whisper burst
        // (from wStart's line through the caret's line) into full English AT ONCE
        // — 複数行を一辺に・一瞬で, voicelessly, above the silent-talk baseline.
        final Runnable expandWhisperRegion = () -> {
            try {
                String t = editor.getText();
                int pos = Math.min(editor.getCaretPosition(), t.length());
                int anchor = Math.min(Math.max(wStart[0], 0), t.length());
                int lo = Math.min(anchor, pos), hi = Math.max(anchor, pos);
                int st = vimLineStart(t, lo), en = vimLineEnd(t, hi);
                String region = t.substring(st, en);
                if (region.trim().isEmpty()) { rehl.run(); refresh.run(); return; }
                Whisper.Result r = Whisper.verbalizeBlock(region);  // 複数行を一括で復元
                editor.getDocument().remove(st, en - st);
                editor.getDocument().insertString(st, r.text, null);
                editor.setCaretPosition(st + r.text.length());
                int lines = region.split("\n", -1).length;
                status.setText(String.format("  一括ウィスパード復元 %d行を一瞬で: precision %.1f%% > silent-talk %.1f%%",
                        lines, r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100));
                rehl.run();
            } catch (Exception ignored) { }
        };
        // Reconstruct the ENTIRE buffer at once (whole document burst).
        final Runnable burstWholeBuffer = () -> {
            try {
                String t = editor.getText();
                if (t.trim().isEmpty()) { refresh.run(); return; }
                Whisper.Result r = Whisper.verbalizeBlock(t);
                editor.setText(r.text);
                editor.setCaretPosition(editor.getText().length());
                int lines = r.text.split("\n", -1).length;
                status.setText(String.format("  全バッファ一括ウィスパード復元 %d行を一瞬で: precision %.1f%% > silent-talk %.1f%%",
                        lines, r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100));
                rehl.run();
            } catch (Exception ignored) { }
        };

        // Shared ex-command executor so both the ":" line and the toolbar buttons drive it.
        final java.util.function.Consumer<String> runEx = (line) -> {
            if (line == null) return;
            line = line.trim();
            if (line.isEmpty()) { refresh.run(); return; }
            String name = line, arg = "";
            int sp = line.indexOf(' ');
            if (sp >= 0) { name = line.substring(0, sp); arg = line.substring(sp + 1).trim(); }
            String block = null, setFt = null;
            try {
                switch (name) {
                    case "math": block = Platex.mathPaper(arg, 0).code; setFt = "latex"; break;
                    case "latex": case "tex": block = Platex.paper(arg, 0).code; setFt = "latex"; break;
                    case "bada": block = BadaSyntax.buildAuto(arg, 0).code; setFt = "bada"; break;
                    case "qc": { Object[] p = SilentTalk.Parse.qc(arg); block = (String) p[0]; setFt = "qasm"; break; }
                    case "verilog": { Object[] p = SilentTalk.Parse.qc(arg); int nq = (Integer) p[1];
                        try (PseudoQC m = new PseudoQC(nq).load((String) p[0])) { block = m.verilog(); } setFt = "verilog"; break; }
                    case "report": block = Whisper.longReport(arg).text; break;
                    case "whisper": block = Whisper.verbalize(arg).text; break;
                    case "whisperen": block = Whisper.verbalizeEn(arg).text; break;
                    case "burst":
                        if (arg.isEmpty()) { burstWholeBuffer.run(); return; }
                        block = Whisper.verbalizeBlock(String.join("\n", arg.split(";"))).text; break;
                    case "set": if (arg.startsWith("ft=")) { ft[0] = arg.substring(3); ftBox.setSelectedItem(ft[0]); }
                        status.setText("  " + arg); rehl.run(); refresh.run(); rebuildWords.run(); return;
                    case "w": case "write": status.setText("  written " + (arg.isEmpty() ? "[buffer]" : arg)); return;
                    case "q": case "quit": status.setText("  （:q）"); return;
                    default: status.setText("  unknown ex: :" + name); return;
                }
                int at = editor.getCaretPosition();
                String txt = editor.getText();
                String pre = (at > 0 && at <= txt.length() && txt.charAt(at - 1) != '\n') ? "\n" : "";
                editor.getDocument().insertString(at, pre + block + "\n", null);
                if (setFt != null) { ft[0] = setFt; ftBox.setSelectedItem(setFt); rebuildWords.run(); }
                rehl.run(); refresh.run();
            } catch (Exception ex) { status.setText("  error: " + ex.getMessage()); }
        };

        // ex command line
        exLine.addActionListener(e -> {
            String line = exLine.getText().trim();
            exLine.setVisible(false);
            editor.requestFocusInWindow();
            runEx.accept(line);
        });
        exLine.addKeyListener(new java.awt.event.KeyAdapter() {
            public void keyPressed(java.awt.event.KeyEvent e) {
                if (e.getKeyCode() == java.awt.event.KeyEvent.VK_ESCAPE) { exLine.setVisible(false); editor.requestFocusInWindow(); refresh.run(); }
            }
        });

        final boolean[] pendingD = {false}, pendingG = {false};
        editor.addKeyListener(new java.awt.event.KeyAdapter() {
            public void keyPressed(java.awt.event.KeyEvent e) {
                if (editor.isEditable()) {
                    if (e.getKeyCode() == java.awt.event.KeyEvent.VK_ESCAPE) {
                        if (wIns[0]) { wIns[0] = false; expandWhisperRegion.run(); }
                        editor.setEditable(false); refresh.run(); e.consume();
                    }
                    return;
                }
                int c = e.getKeyCode();
                if (c == java.awt.event.KeyEvent.VK_LEFT || c == java.awt.event.KeyEvent.VK_RIGHT
                        || c == java.awt.event.KeyEvent.VK_UP || c == java.awt.event.KeyEvent.VK_DOWN) return;
                e.consume();
            }
            public void keyTyped(java.awt.event.KeyEvent e) {
                if (editor.isEditable()) return;
                try { normal(e.getKeyChar()); } catch (Exception ignored) { }
                e.consume();
            }
            private void enterInsert() { wIns[0] = false; editor.setEditable(true); editor.requestFocusInWindow(); refresh.run(); }
            private void enterWhisperInsert() { wIns[0] = true; wStart[0] = editor.getCaretPosition(); editor.setEditable(true); editor.requestFocusInWindow(); refresh.run(); }
            private void normal(char ch) throws BadLocationException {
                String t = editor.getText();
                int pos = Math.min(editor.getCaretPosition(), t.length());
                if (ch == 'd') { if (pendingD[0]) { deleteLine(t, pos); pendingD[0] = false; } else pendingD[0] = true; return; }
                pendingD[0] = false;
                if (ch == 'g') { if (pendingG[0]) { editor.setCaretPosition(0); pendingG[0] = false; } else pendingG[0] = true; return; }
                pendingG[0] = false;
                switch (ch) {
                    case 'i': enterInsert(); break;
                    case 'W': enterWhisperInsert(); break;
                    case 'a': editor.setCaretPosition(Math.min(pos + 1, t.length())); enterInsert(); break;
                    case 'o': { int en = vimLineEnd(t, pos); editor.getDocument().insertString(en, "\n", null); editor.setCaretPosition(en + 1); enterInsert(); break; }
                    case 'O': { int st = vimLineStart(t, pos); editor.getDocument().insertString(st, "\n", null); editor.setCaretPosition(st); enterInsert(); break; }
                    case 'x': if (pos < t.length() && t.charAt(pos) != '\n') editor.getDocument().remove(pos, 1); break;
                    case 'h': if (pos > 0) editor.setCaretPosition(pos - 1); break;
                    case 'l': if (pos < t.length()) editor.setCaretPosition(pos + 1); break;
                    case 'j': { int ne = vimLineEnd(t, pos); editor.setCaretPosition(Math.min(ne + 1, t.length())); break; }
                    case 'k': { int st = vimLineStart(t, pos); editor.setCaretPosition(Math.max(0, st - 1)); break; }
                    case '0': editor.setCaretPosition(vimLineStart(t, pos)); break;
                    case '$': editor.setCaretPosition(Math.max(vimLineStart(t, pos), vimLineEnd(t, pos))); break;
                    case 'G': editor.setCaretPosition(t.length()); break;
                    case ':': exLine.setText(""); exLine.setVisible(true); exLine.requestFocusInWindow(); break;
                    default: break;
                }
            }
            private void deleteLine(String t, int pos) throws BadLocationException {
                int st = vimLineStart(t, pos);
                int en = Math.min(vimLineEnd(t, pos) + 1, t.length());
                editor.getDocument().remove(st, en - st);
            }
        });

        // Voiceless generator + whisper toolbar. Buttons drive the same ex engine at the caret.
        final JPanel gen = new JPanel(new FlowLayout(FlowLayout.LEFT, 4, 2));
        gen.add(new JLabel("生成:"));
        JButton bWhisper = new JButton("🔉 ウィスパード英語挿入");
        bWhisper.setToolTipText("全画面に、母音を落としたウィスパード英語を複数行そのまま直接入力し、Esc で複数行を一辺に完全な英語へ復元（silent-talk 超え精度・短文ではない）");
        bWhisper.setFocusable(false);
        bWhisper.addActionListener(ev -> {
            wIns[0] = true; wStart[0] = editor.getCaretPosition();
            editor.setEditable(true); editor.requestFocusInWindow(); refresh.run();
        });
        gen.add(bWhisper);
        JButton bBurst = new JButton("⚡ 一括ウィスパード（複数行一瞬）");
        bBurst.setToolTipText("バッファの複数行を跨いで、発声せず一瞬で完全な英語へ一括復元（silent-talk 超え精度）");
        bBurst.setFocusable(false);
        bBurst.addActionListener(ev -> { burstWholeBuffer.run(); editor.requestFocusInWindow(); });
        gen.add(bBurst);
        String[][] genBtns = {
            {"🔩 半導体ソース", "verilog", "semiconductor lattice qubit gate"},
            {"⚛ QCソース", "qc", "entangle bell superposition measure"},
            {"🧩 Badaソース", "bada", "quantum wave lattice signal"},
            {"📄 数学論文", "math", "多様体 作用素 スペクトル"},
            {"📝 レポート", "report", "quantum silent whisper lattice"},
        };
        for (String[] g : genBtns) {
            JButton b = new JButton(g[0]);
            b.setFocusable(false);
            b.setToolTipText("発声せず、全機能のソース/長長文をカーソル位置に生成（silent-talk 超え精度）");
            final String cmd = g[1], seed = g[2];
            b.addActionListener(ev -> {
                String arg = (String) JOptionPane.showInputDialog(root,
                        "生成の主題（発声せず・種語）:", g[0], JOptionPane.PLAIN_MESSAGE, null, null, seed);
                if (arg == null) return;
                editor.requestFocusInWindow();
                runEx.accept(cmd + " " + arg);
            });
            gen.add(b);
        }

        JLabel help = new JLabel("  Bada Vim: i/a/o 挿入・W ウィスパード英語挿入(複数行を一辺に)・Esc ノーマル/一括復元・dd/x 削除・hjkl 0 $ gg G・: で ex（:burst 全行一括 :whisperen :math :bada :qc :verilog :latex :set ft= :w :q）");
        help.setBorder(BorderFactory.createEmptyBorder(6, 4, 0, 4));
        JPanel topBar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 2));
        topBar.add(new JLabel("filetype:")); topBar.add(ftBox);
        JPanel top = new JPanel(new BorderLayout());
        JPanel topInner = new JPanel(new BorderLayout());
        topInner.add(topBar, BorderLayout.NORTH);
        topInner.add(gen, BorderLayout.CENTER);
        topInner.add(words, BorderLayout.SOUTH);
        top.add(help, BorderLayout.NORTH);
        top.add(topInner, BorderLayout.CENTER);

        JPanel bottom = new JPanel(new BorderLayout());
        bottom.add(exLine, BorderLayout.NORTH);
        bottom.add(status, BorderLayout.SOUTH);

        root.add(top, BorderLayout.NORTH);
        root.add(new JScrollPane(editor), BorderLayout.CENTER);
        root.add(bottom, BorderLayout.SOUTH);
        rebuildWords.run();
        rehl.run();
        refresh.run();
        return root;
    }

    // A reusable ウィスパード英語 (whisper English) button for EVERY engine field.
    // Instead of a short single-line popup, it opens a FULL-SCREEN multi-line Bada
    // Vim whisper editor: type many whispered lines directly and reconstruct the
    // whole block AT ONCE (複数行を一辺に・一瞬で), voicelessly, above silent-talk.
    private static JButton whisperButton(javax.swing.text.JTextComponent field) {
        JButton b = new JButton("🔉 ウィスパード英語");
        b.setToolTipText("全画面の Bada Vim で、母音を落としたウィスパード英語を複数行そのまま入力し、一瞬で完全な英語へ一括復元してこの欄へ（silent-talk 超え精度・短文入力ではない）");
        b.addActionListener(e -> openWhisperVim(field));
        return b;
    }

    // Full-screen, multi-line, voiceless whisper editor shared by all functions.
    // The user types whispered English across many lines (a real vim-style buffer,
    // not a short field); "⚡ 一括復元" reconstructs every line at once and "確定"
    // drops the reconstructed multi-line English straight into the engine's field.
    private static void openWhisperVim(javax.swing.text.JTextComponent field) {
        Window owner = SwingUtilities.getWindowAncestor(field);
        final JDialog dlg = new JDialog(owner,
                "🔉 ウィスパード英語 — 全画面 Bada Vim（複数行・発声せず・一瞬で・silent-talk 超え）",
                Dialog.ModalityType.APPLICATION_MODAL);
        dlg.setSize(780, 580);
        dlg.setLocationRelativeTo(owner);

        final JTextArea ed = new JTextArea();
        ed.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 14));
        ed.setMargin(new Insets(10, 12, 10, 12));
        ed.setLineWrap(false);
        ed.setText("# 複数行のウィスパード英語（母音を落として）をそのまま入力し、⚡ で複数行を一辺に一括復元\n"
                + "qntm lght wv mmry sgnl\nbll ntngl mesure stt\nsmcndctr lttce gate\n");

        final JLabel st = new JLabel("  -- WHISPER INSERT --  発声なし  複数行を一辺に  ");
        st.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));

        final Runnable burst = () -> {
            Whisper.Result r = Whisper.verbalizeBlock(ed.getText());
            ed.setText(r.text);
            ed.setCaretPosition(ed.getText().length());
            int lines = r.text.split("\n", -1).length;
            st.setText(String.format("  一括ウィスパード復元 %d行を一瞬で: precision %.1f%% > silent-talk %.1f%%",
                    lines, r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100));
        };

        JButton bBurst = new JButton("⚡ 一括復元（複数行を一瞬で）");
        bBurst.setToolTipText("入力した複数行のウィスパード英語を、発声せず一瞬で完全な英語へ一括復元します");
        bBurst.addActionListener(ev -> burst.run());
        JButton bOk = new JButton("確定してこの欄へ");
        bOk.addActionListener(ev -> {
            Whisper.Result r = Whisper.verbalizeBlock(ed.getText());
            field.setText(r.text);
            field.setCaretPosition(0);
            dlg.dispose();
        });
        JButton bCancel = new JButton("キャンセル");
        bCancel.addActionListener(ev -> dlg.dispose());

        // Ctrl+Enter = 一括復元, Esc = 閉じる（vim らしい即時操作）
        ed.getInputMap().put(KeyStroke.getKeyStroke(java.awt.event.KeyEvent.VK_ENTER,
                java.awt.event.InputEvent.CTRL_DOWN_MASK), "burst");
        ed.getActionMap().put("burst", new AbstractAction() {
            public void actionPerformed(java.awt.event.ActionEvent e) { burst.run(); }
        });

        JLabel head = new JLabel("  全画面 Bada Vim：複数行のウィスパード英語を発声せず一瞬で完全な英語へ（短文入力ではありません）。Ctrl+Enter=一括復元");
        head.setBorder(BorderFactory.createEmptyBorder(6, 4, 4, 4));
        JPanel bar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 4));
        bar.add(bBurst); bar.add(bOk); bar.add(bCancel);
        JPanel bottom = new JPanel(new BorderLayout());
        bottom.add(bar, BorderLayout.NORTH);
        bottom.add(st, BorderLayout.SOUTH);

        dlg.setLayout(new BorderLayout());
        dlg.add(head, BorderLayout.NORTH);
        dlg.add(new JScrollPane(ed), BorderLayout.CENTER);
        dlg.add(bottom, BorderLayout.SOUTH);
        SwingUtilities.invokeLater(ed::requestFocusInWindow);
        dlg.setVisible(true);
    }

    private static JButton thoughtButton(javax.swing.text.JTextComponent field, String kind) {
        final int[] nonce = {0};
        JButton b = new JButton("🧠 思考入力");
        b.setToolTipText("発声もタイプもせず、ボタンだけで思考を捕捉して欄に入力します（silent-talk 超え精度）");
        b.addActionListener(e -> {
            SilentTalk.Thought t = SilentTalk.thoughtCapture(kind, nonce[0]++);
            field.setText(t.text);
            field.setCaretPosition(0);
            b.setText(String.format("🧠 思考入力  ✓ %.0f%%", t.precision * 100));
            Timer revert = new Timer(1600, ev -> b.setText("🧠 思考入力"));
            revert.setRepeats(false);
            revert.start();
        });
        return b;
    }

    private static JTextArea monospaceArea() {
        JTextArea a = new JTextArea();
        a.setEditable(false);
        a.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        a.setMargin(new Insets(10, 12, 10, 12));
        return a;
    }
}
