# ============================================================================
#  Madotsukai (mayu) - Emacs + vim key bindings for Windows 10 / 11.
#  Registers the key bindings into the Windows registry and (elevated) applies
#  the physical CapsLock -> Ctrl remap.
#
#  Usage:   powershell -ExecutionPolicy Bypass -File install.ps1
#           powershell -ExecutionPolicy Bypass -File install.ps1 -Win10
# ============================================================================
param([switch]$Win10)

$dir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$hkcu = if ($Win10) { 'windows10.reg' } else { 'windows11.reg' }

Write-Host '=== Madotsukai (mayu) keybinding installer ==='
Write-Host "Importing Emacs + vim key bindings -> HKCU\Software\Mayu  ($hkcu)"
reg import (Join-Path $dir $hkcu)

$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent() `
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$scReg = Join-Path $dir 'scancode-capslock-ctrl.reg'
Write-Host 'Applying physical remap (CapsLock -> Left Ctrl) -> HKLM Scancode Map ...'
if ($isAdmin) {
    reg import $scReg
    Write-Host '  installed - sign out and back in (or reboot) to activate.'
} else {
    Write-Host '  elevating for the HKLM remap ...'
    Start-Process powershell -Verb RunAs -ArgumentList `
        "-NoProfile -Command reg import `"$scReg`""
}

Write-Host ''
Write-Host 'Edit keybindings.mayu and re-run to change your bindings.'
Write-Host 'Run  reg import uninstall.reg  to remove everything.'
