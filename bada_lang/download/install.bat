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

echo Starting the mayu remapper ^(this is what makes the keys actually work^)...
set LAUNCH=
if exist "%~dp0mayu.exe" set LAUNCH="%~dp0mayu.exe"
if not defined LAUNCH (
  where python >nul 2>&1 && set LAUNCH=python "%~dp0mayu_agent.py"
)
if defined LAUNCH (
  start "mayu" %LAUNCH%
  echo   mayu is running - Emacs/vim keys now work in every app.
  echo.
  choice /m "Start mayu automatically when you sign in"
  if not errorlevel 2 (
    reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v mayu /t REG_SZ /d %LAUNCH% /f
    echo   autostart enabled ^(HKCU\...\Run\mayu^).
  )
) else (
  echo   Could not find mayu.exe or Python. Download mayu.exe from the
  echo   Releases page, put it in this folder, and run it.
)
echo.
echo Edit keybindings.mayu and restart mayu to change your bindings.
echo Run uninstall.bat to remove everything.
pause
