@echo off
setlocal

rem se-buddy launcher (Windows). Not the program itself - it bootstraps or
rem repairs the vendored venv, then execs into it (spec Sec.5.1).

for %%I in ("%~dp0..") do set "ROOT=%%~fI"

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set "SYSTEM_PYTHON=python"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "SYSTEM_PYTHON=py"
    ) else (
        echo se-buddy: no python found on PATH 1>&2
        exit /b 1
    )
)

set "VENV_PYTHON="
for /f "usebackq delims=" %%P in (`%SYSTEM_PYTHON% "%ROOT%\bin\_bootstrap.py"`) do set "VENV_PYTHON=%%P"

if "%VENV_PYTHON%"=="" (
    echo se-buddy: bootstrap failed - see the message above 1>&2
    exit /b 1
)

set "PYTHONPATH=%ROOT%\src;%PYTHONPATH%"
"%VENV_PYTHON%" -m se_buddy %*
exit /b %ERRORLEVEL%
