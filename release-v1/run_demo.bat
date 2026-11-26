@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%"
set "PYTHONDONTWRITEBYTECODE=1"
set "FAILED=0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo Install Python 3.10 or newer and try again.
    exit /b 2
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.10 or newer is required.
    exit /b 2
)

echo ============================================================
echo OrderCheck release-v1 demo
echo ============================================================
call :run "normal order" "demo\order_ok.txt" "PASS" 0
call :run "missing Material" "demo\order_missing.txt" "REVIEW" 1
call :run "TBD placeholder" "demo\order_tbd.txt" "REVIEW" 1
call :run "duplicate key" "demo\order_duplicate.txt" "REVIEW" 1
call :run "unknown key" "demo\order_unknown.txt" "REVIEW" 1
call :run "unparsable line" "demo\order_bad_line.txt" "REVIEW" 1
call :run "invalid values" "demo\order_invalid_values.txt" "REVIEW" 1
call :run "non-finite Flow" "demo\order_nonfinite.txt" "REVIEW" 1
call :run "empty order" "demo\order_empty.txt" "REVIEW" 1
call :run "non-TXT input" "demo\order_not_txt.dat" "BLOCK" 2
call :run "non-UTF8 input" "demo\bad_utf8.txt" "BLOCK" 2

echo.
echo --- version binding demo ---
python demo\versioning_demo.py
if errorlevel 1 (
    set "FAILED=1"
    echo [MISMATCH] versioning demo returned a non-zero exit code.
)

echo.
if "%FAILED%"=="1" (
    echo RESULT: FAILED
) else (
    echo RESULT: OK
)
if /i not "%~1"=="/nopause" pause
exit /b %FAILED%

:run
set "LABEL=%~1"
set "FILE=%~2"
set "EXPECTED=%~3"
set "EXPECTED_EXIT=%~4"
echo.
echo [%LABEL%] expected %EXPECTED% / exit %EXPECTED_EXIT%
python -m ordercheck "%FILE%"
set "ACTUAL_EXIT=%ERRORLEVEL%"
echo exit=%ACTUAL_EXIT%
if not "%ACTUAL_EXIT%"=="%EXPECTED_EXIT%" (
    set "FAILED=1"
    echo [MISMATCH] expected exit %EXPECTED_EXIT%, got %ACTUAL_EXIT%
)
exit /b 0
