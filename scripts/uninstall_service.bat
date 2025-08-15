@echo off
echo ========================================
echo Desinstallation Service Axiom Trade
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
echo 1. Arret du service...
sc stop "AxiomTradeService" >nul 2>&1

echo.
echo 2. Suppression du service...
sc delete "AxiomTradeService"

if %errorlevel% equ 0 (
    echo ✅ Service supprime avec succes.
) else (
    echo ⚠️  Le service n'existait pas ou etait deja supprime.
)

echo.
echo 3. Verification...
sc query "AxiomTradeService" >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ Le service existe encore
) else (
    echo ✅ Service completement supprime
)

echo.
echo 4. Nettoyage des processus...
tasklist | findstr python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo Processus Python detectes:
    tasklist | findstr python.exe
    echo.
    echo Pour arreter manuellement: taskkill /f /im python.exe
) else (
    echo ✅ Aucun processus Python detecte
)

echo.
echo ========================================
echo Desinstallation terminee
echo ========================================
pause