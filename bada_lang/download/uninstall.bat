@echo off
rem  Remove the mayu key bindings (HKCU\Software\Mayu) and the physical
rem  Scancode Map remap (HKLM).  Run as administrator for the HKLM part.
setlocal
echo === Madotsukai (mayu) uninstaller ===
echo Stopping the mayu remapper ...
taskkill /im mayu.exe /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v mayu /f >nul 2>&1
reg import "%~dp0uninstall.reg"
echo Removed.  Sign out and back in to drop the physical remap.
pause
