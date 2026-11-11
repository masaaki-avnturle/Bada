@echo off
rem ============================================================================
rem  Start the mayu keyboard remapper (the resident agent that actually makes
rem  the Emacs / vim key bindings work in every application).
rem
rem  Two ways to run:
rem    * mayu.exe            - double-click, no Python needed (from the Release)
rem    * run_mayu.bat        - this script, needs Python 3 installed
rem
rem  Usage:  run_mayu.bat                (Emacs keymap)
rem          run_mayu.bat --keymap vim-normal
rem  A console window stays open; press Ctrl-C in it to stop remapping.
rem ============================================================================
cd /d "%~dp0"
where mayu.exe >nul 2>&1
if %errorlevel%==0 (
  start "mayu" mayu.exe %*
  echo Started mayu.exe - Emacs/vim keys are now active. Close its window to stop.
  goto :eof
)
python mayu_agent.py %*
