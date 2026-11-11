@echo off
rem ============================================================================
rem  Start mayu in VIM mode - modal vim keybindings in every text field
rem  (Notepad, edit boxes, ...).  Starts in NORMAL mode.
rem
rem    h j k l   move          i a o   insert (ESC returns to NORMAL)
rem    w b       word          x       delete char     dd  cut line
rem    yy        copy line     p       paste           u   undo
rem    0 $       line ends     gg G    top / bottom
rem
rem  Uses mayu.exe if present (no Python), else Python 3.
rem ============================================================================
cd /d "%~dp0"
where mayu.exe >nul 2>&1
if %errorlevel%==0 (
  start "mayu (vim)" mayu.exe --vim
  echo Started mayu.exe in VIM mode. Close its window to stop.
  goto :eof
)
python mayu_agent.py --vim
