@echo off
rem AntiGravity OS -- boot the generative-AI OS init process (PID 1)
rem Works on Windows 10 / 11. Requires nothing but this folder.
cd /d "%~dp0"
echo.
bada.exe run agos.bada
echo.
echo ---- flight session complete (G1-G4 re-derived above) ----
pause
