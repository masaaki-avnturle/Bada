# 窓使いの憂鬱 — mayu keybindings for Windows 10 / 11

Emacs **and** vim key bindings, written in the **Bada** language, registered
into the **Windows Registry**, and editable by you. Download the files in this
folder and run the installer.

## Download & run (this is the part that actually works)

**`mayu.exe` is the resident program that makes the keys work.** It installs a
low-level keyboard hook and rewrites your Emacs/vim chords into real keystrokes
in every application. No Python, no admin.

1. Download **`mayu.exe`** and **`keybindings.mayu`** into the same folder:
   - <https://github.com/masaaki-avnturle/Bada/releases/download/mayu-latest/mayu.exe>
   - <https://github.com/masaaki-avnturle/Bada/releases/download/mayu-latest/keybindings.mayu>
2. Double-click **`mayu.exe`** — a console shows *"mayu is running"*.
3. Open Notepad and try: **C-a** = line start, **C-e** = line end,
   **C-f/C-b/C-n/C-p** = arrows, **C-k** = kill line, **C-y** = yank,
   **C-x C-s** = save. Close the console to stop.

Prefer the bundle? Grab the zip and run `install.bat` (it starts mayu.exe and
offers to auto-start it at sign-in):

> **https://github.com/masaaki-avnturle/Bada/releases/download/mayu-latest/madotsukai_windows.zip**

No Python? `mayu.exe` needs none. With Python installed you can instead run
`python mayu_agent.py` (or `run_mayu.bat`) — same remapper, from source.

## Notepad — Emacs or vim

Both work in Notepad (and any text field). Pick one:

**Emacs** (default): run `mayu.exe`.

| key | does | key | does |
|-----|------|-----|------|
| C-a / C-e | line start / end | C-k | kill (cut) to end of line |
| C-f / C-b | char right / left | C-y | yank (paste) |
| C-n / C-p | line down / up | C-SPC | set mark, then move to select |
| M-f / M-b | word right / left | C-w / M-w | cut / copy region |
| C-d | delete char | C-x C-s | save |

`C-SPC` sets the mark; then `C-f/C-n/…` **select** text, and `C-w` cuts /
`M-w` copies it — real Emacs region editing inside Notepad.

**vim** (modal): run `mayu.exe --vim` (or double-click `run_mayu_vim.bat`).
Starts in NORMAL mode:

| key | does | key | does |
|-----|------|-----|------|
| h j k l | move | i / a | insert before / after |
| w / b | word fwd / back | o / O | open line below / above |
| 0 / $ | line start / end | x | delete char |
| gg / G | top / bottom | dd | delete (cut) line |
| yy / p | copy line / paste | u | undo |
| **ESC** | back to NORMAL | A / I | append-EOL / insert-BOL |

The console window shows `-- INSERT --` / `-- NORMAL --` as you switch. Close
it to stop. (Run either mode — they can't both be active at once, since both
remap the same keys.)

This package registers key combinations into the registry two ways:

| where | what | needs admin? | applied by |
|-------|------|--------------|------------|
| **`mayu.exe`** (the keyboard hook) | the Emacs/vim **chord map** (C-a → line start, C-k → kill line, C-x C-s → save, …) | no | **`mayu.exe`** — a resident keyboard hook |
| `HKEY_CURRENT_USER\Software\Mayu\<os>` | the same config, also stored in the registry | no | `mayu.exe` / the Bada tool |
| `HKEY_LOCAL_MACHINE\...\Keyboard Layout` → **`Scancode Map`** | a **genuine physical remap** (CapsLock → Ctrl) | yes | **Windows itself**, at the driver level |

`mayu.exe` is the working remapper: it hooks the keyboard and rewrites chords
live, so the Emacs/vim keys work in any app. The `Scancode Map` is the real
mechanism Windows 10/11 use to remap whole physical keys from the registry
(import + sign out; no program running). The `HKCU\Software\Mayu` keys are the
same chord map stored in the registry for reference / other agents.

## Files

| file | what it is |
|------|-----------|
| **`mayu.exe`** | **the working remapper — double-click to run.** Hooks the keyboard and rewrites Emacs/vim chords into real keystrokes. No Python. |
| `keybindings.mayu` | the **editable** config (Emacs + vim + per-app). Edit, then restart `mayu.exe`. |
| `mayu_agent.py` | the same remapper as source (run with `python mayu_agent.py` if you have Python) |
| `run_mayu.bat` | convenience launcher (uses `mayu.exe` if present, else Python) |
| `windows11.reg` / `windows10.reg` | the bindings stored in `HKCU\Software\Mayu\<os>` |
| `scancode-capslock-ctrl.reg` | the genuine physical remap **CapsLock → Left Ctrl** (`HKLM`) |
| `uninstall.reg` | removes the registry entries |
| `install.bat` / `install.ps1` | import the `.reg` files, start `mayu.exe`, offer auto-start |
| `uninstall.bat` | stop mayu, remove autostart, undo the registry entries |
| `mayu.pyz` | the Bada config tool (compile the config, print the registry tree, export `.reg`) — needs Python 3 |

## Install

**Windows 11** (double-click, or):

```bat
install.bat
```

**Windows 10:**

```bat
install.bat win10
```

To also apply the physical **CapsLock → Ctrl** remap, right-click
`install.bat` → **Run as administrator** (or run `install.ps1`, which elevates
for you). Sign out and back in for the physical remap to take effect.

Prefer PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1          # Windows 11
powershell -ExecutionPolicy Bypass -File install.ps1 -Win10   # Windows 10
```

## Edit your own bindings

Open **`keybindings.mayu`** in any editor. The syntax is a small DSL:

```
os win11                       # or: os win10
define MOD = C

keymap emacs {
  key $MOD-a -> move-beginning-of-line
  key C-k    -> kill-line
  key C-x C-s -> save-buffer
}

keymap vim-normal {
  key h -> cursor-left
  key d d -> delete-line
}

app "Notepad" {                # per-application, matched by exe / window class
  exe notepad.exe
  class Notepad
  base emacs
  key C-k -> send S-End Delete  # send raw keystrokes
  key F5  -> type "%date% %time%"
}
```

Then regenerate the `.reg` files with the bundled tool and re-run the installer:

```bash
python mayu.pyz            # opens the mayu CLI; `reg` prints the tree, `export out.reg` writes it
```

or, from the full Bada source repo:

```bash
./bada run apps/mayu_pack.bada    # rewrites windows11.reg / windows10.reg / scancode / uninstall
```

## Uninstall

```bat
uninstall.bat
```

or import `uninstall.reg`. Sign out and back in to drop the physical remap.

## How it works (and honest scope)

- **`mayu.exe`** installs a Windows low-level keyboard hook (`WH_KEYBOARD_LL`)
  and, for each chord it recognises, suppresses the original key and injects the
  mapped keystrokes with `SendInput` — exactly how AutoHotkey / yamy work. Each
  Emacs/vim command maps to the Windows keystroke that performs it
  (`C-a`→Home, `C-k`→Shift+End then Cut, `M-f`→Ctrl+Right, …), so the bindings
  work in ordinary apps like Notepad, browsers and editors. Per-application
  bindings match the focused window's class.
- The **physical remap** (`Scancode Map`) is applied by Windows itself with no
  program running — but it can only swap whole physical keys (CapsLock→Ctrl,
  Esc↔CapsLock, disable a key), not chords. Use it together with `mayu.exe`.
- The `HKCU\Software\Mayu` registry keys store the same chord map for reference.

Limitations: `mayu.exe` translates chords to standard editing keystrokes, so a
binding works wherever that keystroke works (most text fields). Modal vim
insert/normal switching is best-effort. Edit `keybindings.mayu` to customise.

Built with the Bada language (a custom compiler + VM) plus a pure-`ctypes`
keyboard hook. See the repository root for the full source, the mayu GUI editor
(`apps/mayu.bada`), and the yamy `.mayu` engine (`apps/yamy.bada`).
