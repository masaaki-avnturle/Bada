# 窓使いの憂鬱 — mayu keybindings for Windows 10 / 11

Emacs **and** vim key bindings, written in the **Bada** language, registered
into the **Windows Registry**, and editable by you. Download the files in this
folder and run the installer.

## Download (one click)

Grab the packaged `.zip` from the repository's **Releases** page:

> **https://github.com/masaaki-avnturle/Bada/releases/download/mayu-latest/madotsukai_windows.zip**

(Or browse <https://github.com/masaaki-avnturle/Bada/releases> and pick
*窓使いの憂鬱 mayu — Windows 10/11 keybindings*.) Unzip and run `install.bat`.
Every file below is also attached to that release individually.

This package registers key combinations into the registry two ways:

| where | what | needs admin? | applied by |
|-------|------|--------------|------------|
| `HKEY_CURRENT_USER\Software\Mayu\<os>` | the Emacs/vim **key-binding config** (chord → command, per application) | no | a mayu-style agent / the Bada tool |
| `HKEY_LOCAL_MACHINE\...\Keyboard Layout` → **`Scancode Map`** | a **genuine physical remap** (CapsLock → Ctrl) | yes | **Windows itself**, at the driver level |

The `Scancode Map` part is the real mechanism Windows 10 and 11 use to remap
keys from the registry — after you import it and sign out, the OS obeys it with
no program running. The `HKCU\Software\Mayu` part is the full Emacs/vim chord
map (C-a, C-k, C-x C-s, dd, yy, …) that the Bada mayu tool reads.

## Files

| file | what it is |
|------|-----------|
| `keybindings.mayu` | the **editable** key-binding config (Emacs + vim + per-app). Edit this. |
| `windows11.reg` | the key bindings compiled for Windows 11 (`HKCU\Software\Mayu\win11`) |
| `windows10.reg` | the same for Windows 10 (`HKCU\Software\Mayu\win10`) |
| `scancode-capslock-ctrl.reg` | the genuine physical remap **CapsLock → Left Ctrl** (`HKLM`) |
| `uninstall.reg` | removes both of the above |
| `install.bat` / `install.ps1` | import the right files for your Windows version |
| `uninstall.bat` | undo everything |
| `mayu.pyz` | the portable mayu tool (compile the config, print the registry tree, export `.reg`) — needs Python 3 |

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

## Scope / honesty

- The **physical remap** (`Scancode Map`) is applied by Windows itself and needs
  no running program — but it can only swap whole physical keys (CapsLock→Ctrl,
  Esc↔CapsLock, disable a key, …), not chords.
- The **Emacs/vim chord map** (`C-k → kill-line`, `dd → delete-line`, …) lives in
  `HKCU\Software\Mayu` and is interpreted by the mayu tool / a resident agent —
  the same division of labour as the original 窓使いの憂鬱 / yamy.

Built with the Bada language (a custom compiler + VM). See the repository root
for the full source, the mayu GUI editor (`apps/mayu.bada`), and the yamy
`.mayu` engine (`apps/yamy.bada`).
