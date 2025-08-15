@echo off
echo ========================================
echo Arret Service Axiom Trade
echo ========================================

REM Verification des privileges administrateur
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Ce script doit etre execute en tant qu'administrateur.
    echo Clic droit sur le fichier et "Executer en tant qu'administrateur"
    pause
    exit /b 1
)

echo.
echo Arret du service AxiomTradeService...
sc stop "AxiomTradeService"

if %errorlevel% equ 0 (
    echo ✅ Service arrete avec succes.
) else (
    echo ⚠️  Le service etait deja arrete ou n'existe pas.
)

echo.
echo Verification du statut...
timeout /t 2 >nul
sc query "AxiomTradeService" | findstr "STATE"

echo.
echo Verification du port 5000...
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Des processus utilisent encore le port 5000
    echo Processus detectes:
    netstat -ano | findstr :5000
) else (
    echo ✅ Port 5000 libre
)

echo.
echo ========================================
echo Operation terminee
echo ========================================
pause