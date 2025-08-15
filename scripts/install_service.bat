@echo off
echo ========================================
echo Installation Service Axiom Trade
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
echo 1. Installation du service...
venv\Scripts\python.exe src\backend_api\flask_service.py install

if %errorlevel% equ 0 (
    echo ✅ Service installe avec succes.
) else (
    echo ❌ ERREUR: Echec de l'installation.
    pause
    exit /b 1
)

echo.
echo 2. Configuration pour demarrage automatique...
sc config "AxiomTradeService" start= auto

echo.
echo 3. Demarrage du service...
sc start "AxiomTradeService"

echo.
echo ========================================
echo Installation terminee
echo ========================================
echo.
echo Service "AxiomTradeService" installe et demarre.
echo Test: http://localhost:5000/health
echo.
pause