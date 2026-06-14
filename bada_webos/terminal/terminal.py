"""Terminal — bundles bash, vim and emacs into one BadaWebOS app.

A terminal session owns a :class:`VFS` and a :class:`Shell`; running ``vim`` or
``emacs`` opens an editor session bound to the same VFS, so files created with
bash are edited by the editors and vice-versa.  Everything is recorded in a
transcript that renders to ASCII or to an HTML terminal window for the desktop.
"""

from __future__ import annotations

from html import escape

from .editors import EmacsSession, VimSession
from .shell import Shell
from .vfs import VFS


class Terminal:
    def __init__(self, vfs: VFS | None = None):
        self.shell = Shell(vfs)
        self.vfs = self.shell.vfs
        self.transcript: list[tuple[str, str, str]] = []   # prompt, cmd, out
        self.editors: list = []

    # -- prompt ------------------------------------------------------------
    def prompt(self) -> str:
        cwd = self.vfs.cwd.replace(self.shell.env["HOME"], "~")
        return f"{self.shell.env['USER']}@webos:{cwd}$ "

    # -- bash --------------------------------------------------------------
    def bash(self, line: str) -> str:
        prompt = self.prompt()
        out = self.shell.run(line)
        req = self.shell.launch_request
        if req is not None:
            if req.program == "vim":
                self.open_vim(req.filename)
                out = f"[vim] editing {req.filename or 'noname.txt'}\n"
            elif req.program == "emacs":
                self.open_emacs(req.filename)
                out = f"[emacs] editing {req.filename or '*scratch*'}\n"
        if out == "\x0c":                 # `clear`
            self.transcript.clear()
            return ""
        self.transcript.append((prompt, line, out))
        return out

    def run_script(self, lines: list[str]) -> str:
        return "".join(self.bash(l) for l in lines)

    # -- interactive REPL (real character input) --------------------------
    def interactive(self, instream=None, out=None, force_line: bool = False):
        """A read-eval-print loop with real keyboard input.  ``vim``/``emacs``
        drop into an interactive editor (curses on a tty, line-input
        otherwise) so you can type characters straight into the file."""
        import sys

        from .editors import EmacsSession, VimSession
        from .interactive import run_emacs, run_vim

        instream = instream or sys.stdin
        out = out or sys.stdout
        out.write("BadaWebOS terminal — 'help' for apps, 'exit' to quit.\n")
        while True:
            out.write(self.prompt())
            out.flush()
            raw = instream.readline()
            if not raw:                       # EOF
                break
            line = raw.rstrip("\n")
            if line.strip() in ("exit", "logout"):
                break
            prompt = self.prompt()
            result = self.shell.run(line)
            req = self.shell.launch_request
            if req is not None:
                if req.program == "vim":
                    sess = VimSession(self.vfs, req.filename)
                    self.editors.append(("vim", sess))
                    run_vim(sess, instream=instream, out=out,
                            force_line=force_line)
                else:
                    sess = EmacsSession(self.vfs, req.filename)
                    self.editors.append(("emacs", sess))
                    run_emacs(sess, instream=instream, out=out,
                              force_line=force_line)
                self.transcript.append(
                    (prompt, line, f"[{req.program}] {req.filename}"))
                continue
            if result == "\x0c":              # clear
                self.transcript.clear()
                continue
            self.transcript.append((prompt, line, result))
            if result:
                out.write(result if result.endswith("\n") else result + "\n")
        out.write("logout\n")

    # -- editors -----------------------------------------------------------
    def open_vim(self, filename: str | None,
                 script: list[str] | None = None) -> VimSession:
        sess = VimSession(self.vfs, filename)
        if script:
            sess.feed(script)
        self.editors.append(("vim", sess))
        return sess

    def open_emacs(self, filename: str | None,
                   script: list[str] | None = None) -> EmacsSession:
        sess = EmacsSession(self.vfs, filename)
        if script:
            sess.feed(script)
        self.editors.append(("emacs", sess))
        return sess

    # -- renderers ---------------------------------------------------------
    def render_ascii(self) -> str:
        out = []
        for prompt, cmd, result in self.transcript:
            out.append(prompt + cmd)
            if result:
                out.append(result.rstrip("\n"))
        return "\n".join(out)

    def render_html(self) -> str:
        rows = []
        for prompt, cmd, result in self.transcript:
            rows.append(f'<div class="t-cmd"><span class="t-prompt">'
                        f'{escape(prompt)}</span>{escape(cmd)}</div>')
            if result:
                rows.append(f'<pre class="t-out">{escape(result.rstrip())}'
                            f'</pre>')
        apps = ", ".join(f"{kind}:{s.filename}" for kind, s in self.editors)
        footer = (f'<div class="t-foot">editors open — {escape(apps)}</div>'
                  if self.editors else "")
        return (f'<div class="terminal">{"".join(rows)}{footer}</div>')
