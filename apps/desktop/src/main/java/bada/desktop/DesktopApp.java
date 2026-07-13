package bada.desktop;

import bada.quantum.SpaceTelegraph;

import javax.swing.*;
import java.awt.*;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

/**
 * Bada Space Telegraph — Windows/desktop front end.
 *
 * Run with no arguments to open the Swing GUI (this is how the packaged .exe
 * launches). Pass a message on the command line for a one-shot console report:
 *
 *   BadaTelegraph "HELLO SPACE"
 */
public final class DesktopApp {

    public static void main(String[] args) {
        // Console output as UTF-8 so the Japanese report renders correctly.
        System.setOut(new PrintStream(System.out, true, StandardCharsets.UTF_8));

        boolean headless = GraphicsEnvironment.isHeadless();
        String message = String.join(" ", args).trim();

        if (headless || (!message.isEmpty() && !message.equals("--gui"))) {
            if (message.isEmpty() || message.equals("--gui")) message = "HELLO SPACE";
            System.out.println(new SpaceTelegraph("GaAs", 4.0, 3).render(message));
            return;
        }
        SwingUtilities.invokeLater(DesktopApp::buildGui);
    }

    private static void buildGui() {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) { }

        JFrame frame = new JFrame("Bada 量子もつれ・汎用電信通信機 — Space Telegraph");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(820, 640);
        frame.setLayout(new BorderLayout(8, 8));

        // ---- controls -------------------------------------------------------
        JPanel top = new JPanel(new BorderLayout(6, 6));
        top.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));

        JLabel prompt = new JLabel("メッセージ (message):");
        JTextField input = new JTextField("QUANTUM HELLO FROM EARTH");

        JPanel opts = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 0));
        JComboBox<String> material = new JComboBox<>(new String[]{"GaAs", "InAs", "InGaAs", "Si", "diamond(NV)"});
        JSpinner temp = new JSpinner(new SpinnerNumberModel(4.0, 0.1, 400.0, 1.0));
        JSpinner redundancy = new JSpinner(new SpinnerNumberModel(3, 1, 11, 2));
        opts.add(new JLabel("材料:")); opts.add(material);
        opts.add(new JLabel("温度K:")); opts.add(temp);
        opts.add(new JLabel("冗長度:")); opts.add(redundancy);

        JButton send = new JButton("送信・証明 (Transmit & Prove)");

        JPanel inRow = new JPanel(new BorderLayout(6, 6));
        inRow.add(prompt, BorderLayout.WEST);
        inRow.add(input, BorderLayout.CENTER);
        inRow.add(send, BorderLayout.EAST);

        top.add(inRow, BorderLayout.NORTH);
        top.add(opts, BorderLayout.SOUTH);

        // ---- output ---------------------------------------------------------
        JTextArea output = new JTextArea();
        output.setEditable(false);
        output.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        output.setMargin(new Insets(10, 12, 10, 12));
        JScrollPane scroll = new JScrollPane(output);
        scroll.setBorder(BorderFactory.createEmptyBorder(8, 10, 10, 10));

        Runnable run = () -> {
            String msg = input.getText().trim();
            if (msg.isEmpty()) msg = "HELLO SPACE";
            SpaceTelegraph tg = new SpaceTelegraph(
                    (String) material.getSelectedItem(),
                    ((Number) temp.getValue()).doubleValue(),
                    ((Number) redundancy.getValue()).intValue());
            output.setText(tg.render(msg));
            output.setCaretPosition(0);
        };
        send.addActionListener(e -> run.run());
        input.addActionListener(e -> run.run());

        frame.add(top, BorderLayout.NORTH);
        frame.add(scroll, BorderLayout.CENTER);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
        run.run(); // render once on startup
    }
}
