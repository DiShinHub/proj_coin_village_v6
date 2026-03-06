@echo off

cd ../../../desktop/webbot

set VENV_DIR=venv
set REQUIREMENTS=requirements.txt

echo.
echo [1] Check venv directory

if exist "%VENV_DIR%" (
    echo venv already exists
) else (
    echo venv not found. Creating...

    python -m pip install --upgrade pip
    python -m pip install virtualenv

    python -m virtualenv %VENV_DIR%
)

echo.
echo [2] Activate venv
call %VENV_DIR%\Scripts\activate

echo.
echo [3] Install requirements

if exist "%REQUIREMENTS%" (
    pip install -r %REQUIREMENTS%
) else (
    echo requirements.txt not found. Skipping.
)

echo.
echo Setup completed.

endlocal