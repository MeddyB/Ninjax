@echo off
echo ========================================
echo Mise a Jour Service Axiom Trade
echo ========================================

REM Verification des privileges administrateur
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Ce script doit etre execute en tant qu'administrateur.
    pause
    exit /b 1
)

cd /d "%~dp0.."

echo.
echo 1. Arret du service...
sc stop "AxiomTradeService"

echo.
echo 2. Mise a jour de la configuration...
set PYTHON_PATH=%CD%\venv\Scripts\python.exe
set SCRIPT_PATH=%CD%\flask_simple.py

sc config "AxiomTradeService" binPath= "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\""

echo.
echo 3. Redemarrage du service...
sc start "AxiomTradeService"

echo.
echo ========================================
echo Mise a jour terminee
echo ========================================
pause