@echo off
SET CMD=%1
IF "%CMD%"=="" SET CMD=run
IF /I "%CMD%"=="build" (
  IF EXIST src\remapper.c (
    gcc -O2 -municode src\remapper.c src\emacs_bindings.c src\vim_bindings.c -o remapper.exe -luser32 -lpsapi
    IF %ERRORLEVEL% NEQ 0 ( echo Build failed & exit /b %ERRORLEVEL% ) ELSE ( echo Build succeeded )
  ) ELSE ( echo src\remapper.c not found & exit /b 2 )
) ELSE IF /I "%CMD%"=="run" (
  IF EXIST remapper.exe ( remapper.exe ) ELSE ( echo remapper.exe not found. Run "%~nx0 build" first. exit /b 3 )
) ELSE ( echo Usage: %~nx0 [build^|run^|build-and-run] & exit /b 1 )
