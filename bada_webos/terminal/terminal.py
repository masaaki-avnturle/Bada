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
