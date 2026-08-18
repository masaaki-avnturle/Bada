package bada.silent;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Bada Vim — an embedded vi-like modal editor over a multi-line buffer (NOT
 * short-text). Normal-mode motions/edits (i a o O dd x h j k l 0 $ gg G) plus ex
 * commands (:w :q :d :math :bada :latex :report :whisper :set) that embed the
 * generators — e.g. {@code :math 多様体 量子} inserts a long-long math paper.
 * Mirrors {@code Bada::SilentTalk::Vim}.
 */
public final class Vim {
    private final List<String> buffer = new ArrayList<>();
    private int row = 0, col = 0, nonce = 0;
    private String filename = null;
    private boolean saved = true;

    public static final class R {
        public final String msg;
        public final boolean quit;
        R(String msg, boolean quit) { this.msg = msg; this.quit = quit; }
    }

    public Vim() { this(""); }
    public Vim(String text) {
        if (text == null || text.isEmpty()) buffer.add("");
        else buffer.addAll(Arrays.asList(text.split("\n", -1)));
    }

    public String text() { return String.join("\n", buffer); }
    public int lineCount() { return buffer.size(); }
    public int row() { return row; }
    public int col() { return col; }
    public String filename() { return filename; }
    public boolean saved() { return saved; }

    public String status() {
        return String.format("[%s] %s %d行 (%d,%d)", filename == null ? "[No Name]" : filename,
                saved ? "" : "[+]", lineCount(), row + 1, col + 1);
    }

    /** Process one input line: ex command (":…") or a normal-mode command. */
    public R feed(String line) {
        if (line == null) return new R("", false);
        if (line.startsWith(":")) return ex(line.substring(1));
        if (line.isEmpty()) return new R("", false);

        char cmd = line.charAt(0);
        String rest = line.substring(1);
        if (line.equals("dd")) { deleteLine(); return touched("削除"); }
        if (line.equals("gg")) { row = 0; col = 0; return new R("top", false); }
        switch (cmd) {
            case 'i': insertText(rest); return touched("挿入");
            case 'a': col = Math.min(col + 1, cur().length()); insertText(rest); return touched("追記");
            case 'o': openBelow(rest); return touched("行追加");
            case 'O': openAbove(rest); return touched("行追加");
            case 'x': deleteChar(); return touched("削除");
            case 'G': row = buffer.size() - 1; col = 0; return new R("bottom", false);
            case '0': col = 0; return new R("", false);
            case '$': col = Math.max(cur().length() - 1, 0); return new R("", false);
            case 'h': col = Math.max(col - 1, 0); return new R("", false);
            case 'l': col = Math.min(col + 1, cur().length()); return new R("", false);
            case 'j': row = Math.min(row + 1, buffer.size() - 1); clampCol(); return new R("", false);
            case 'k': row = Math.max(row - 1, 0); clampCol(); return new R("", false);
            default: return new R("?" + cmd, false);
        }
    }

    /** Ex command handling (the ":" command line). */
    public R ex(String cmd) {
        String s = cmd == null ? "" : cmd.strip();
        int sp = s.indexOf(' ');
        String name = sp < 0 ? s : s.substring(0, sp);
        String arg = sp < 0 ? "" : s.substring(sp + 1).strip();
        switch (name) {
            case "w": case "write":
                saved = true; if (!arg.isEmpty()) filename = arg; return new R("written " + filename, false);
            case "q": case "quit": return new R("quit", true);
            case "wq": case "x": saved = true; return new R("written", true);
            case "d": case "delete": deleteLine(); return touched("削除");
            case "%d": buffer.clear(); buffer.add(""); row = 0; col = 0; return touched("全消去");
            case "set": return new R("set " + arg, false);
            case "bada": insertBlock(BadaSyntax.buildAuto(arg, bump()).code); return touched("Bada挿入");
            case "math": insertBlock(Platex.mathPaper(arg, bump()).code); return touched("数学論文挿入");
            case "latex": case "tex": insertBlock(Platex.paper(arg, bump()).code); return touched("論文挿入");
            case "report": insertBlock(Whisper.longReport(arg).text); return touched("レポート挿入");
            case "whisper": insertBlock(Whisper.verbalize(arg).text); return touched("言語化挿入");
            default: return new R("unknown ex: :" + name, false);
        }
    }

    // ---- internals ----------------------------------------------------------
    private int bump() { return ++nonce; }
    private String cur() { return row < buffer.size() ? buffer.get(row) : ""; }
    private void clampCol() { col = Math.min(col, Math.max(cur().length() - 1, 0)); }
    private R touched(String msg) { saved = false; return new R(msg, false); }

    private void insertText(String t) {
        String c = cur();
        String head = c.substring(0, Math.min(col, c.length()));
        String tail = c.substring(Math.min(col, c.length()));
        String[] parts = t.split("\n", -1);
        if (parts.length == 1) {
            buffer.set(row, head + t + tail);
            col += t.length();
        } else {
            List<String> nl = new ArrayList<>();
            nl.add(head + parts[0]);
            for (int i = 1; i < parts.length - 1; i++) nl.add(parts[i]);
            nl.add(parts[parts.length - 1] + tail);
            buffer.remove(row);
            buffer.addAll(row, nl);
            row += parts.length - 1;
            col = parts[parts.length - 1].length();
        }
    }

    private void openBelow(String t) { buffer.add(row + 1, ""); row += 1; col = 0; insertText(t); }
    private void openAbove(String t) { buffer.add(row, ""); col = 0; insertText(t); }

    private void deleteLine() {
        buffer.remove(row);
        if (buffer.isEmpty()) buffer.add("");
        row = Math.min(row, buffer.size() - 1);
        col = 0;
    }

    private void deleteChar() {
        String c = cur();
        if (c.isEmpty()) return;
        int cc = Math.min(col, c.length() - 1);
        buffer.set(row, c.substring(0, cc) + c.substring(cc + 1));
        clampCol();
    }

    private void insertBlock(String block) {
        String[] lines = block.split("\n", -1);
        buffer.addAll(row + 1, Arrays.asList(lines));
        row += lines.length;
        col = buffer.get(row).length();
    }
}
