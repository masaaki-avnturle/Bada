package bada.desktop;

import bada.coder.Coder;
import bada.mind.MindReader;
import bada.silent.SilentTalk;
import bada.silent.Whisper;
import bada.silent.BadaSyntax;
import bada.silent.Platex;
import bada.qc.PseudoQC;
import bada.quantum.SpaceTelegraph;

import javax.swing.*;
import java.awt.*;
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

    // A reusable ウィスパード英語 (whisper English) button for every engine field.
    // Prompts for whispered (voiceless, vowel-reduced) English fragments and fills
    // the field with the reconstructed full English, above silent-talk precision.
    private static JButton whisperButton(javax.swing.text.JTextComponent field) {
        JButton b = new JButton("🔉 ウィスパード英語");
        b.setToolTipText("発声せず、母音を落としたウィスパード英語を入力して完全な英語に復元します（silent-talk 超え精度）");
        b.addActionListener(e -> {
            String cue = (String) JOptionPane.showInputDialog(field,
                    "ウィスパード英語（母音を落として, 例: qntm lght wv）:", "🔉 ウィスパード英語 (Whisper EN)",
                    JOptionPane.PLAIN_MESSAGE, null, null, "");
            if (cue == null) return; // cancelled
            Whisper.Result r = Whisper.verbalizeEn(cue); // 英語モードに固定
            field.setText(r.text);
            field.setCaretPosition(0);
            JOptionPane.showMessageDialog(field,
                    String.format("ウィスパード英語を復元しました。%nprecision %.1f%%  >  silent-talk %.1f%%",
                            r.precision * 100, SilentTalk.SILENT_TALK_BASELINE * 100),
                    "🔉 ウィスパード英語", JOptionPane.INFORMATION_MESSAGE);
        });
        return b;
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
