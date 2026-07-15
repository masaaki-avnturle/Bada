@echo off
rem ============================================================================
rem  Madotsukai (mayu) - Emacs + vim key bindings for Windows 10 / 11.
rem  Registers the key bindings into the Windows registry.
rem
rem  Usage:   install.bat           (Windows 11)
rem           install.bat win10     (Windows 10)
rem  Run as administrator to also apply the physical CapsLock -> Ctrl remap.
rem ============================================================================
setlocal
set HKCU=windows11.reg
if /I "%~1"=="win10" set HKCU=windows10.reg

echo === Madotsukai (mayu) keybinding installer ===
echo.
echo Importing Emacs + vim key bindings -> HKCU\Software\Mayu  (%HKCU%)
reg import "%~dp0%HKCU%"
echo.

echo Applying physical remap (CapsLock -^> Left Ctrl) -> HKLM Scancode Map ...
net session >nul 2>&1
if %errorlevel%==0 (
  reg import "%~dp0scancode-capslock-ctrl.reg"
  echo   installed - sign out and back in ^(or reboot^) to activate.
) else (
  echo   SKIPPED: not running as administrator.
  echo   Right-click install.bat -^> "Run as administrator" to enable it.
)
echo.
echo Edit keybindings.mayu and re-run to change your bindings.
echo Run uninstall.bat to remove everything.
pause
