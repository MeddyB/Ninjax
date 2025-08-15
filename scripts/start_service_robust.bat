@echo off
echo ========================================
echo Demarrage Service Axiom Trade - Version Robuste
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
echo 1. Verification de l'existence du service...
sc query "AxiomTradeService" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Service AxiomTradeService non trouve.
    echo Installez d'abord le service avec install_service_clean.bat
    pause
    exit /b 1
)

echo ✅ Service trouve.

echo.
echo 2. Verification du statut actuel...
for /f "tokens=4" %%i in ('sc query "AxiomTradeService" ^| findstr "STATE"') do set SERVICE_STATE=%%i
echo Statut actuel: %SERVICE_STATE%

if "%SERVICE_STATE%"=="RUNNING" (
    echo ✅ Service deja en cours d'execution.
    goto :test_connectivity
)

echo.
echo 3. Tentative de demarrage du service...
echo Cela peut prendre jusqu'a 60 secondes...

REM Utiliser net start au lieu de sc start (parfois plus fiable)
net start "AxiomTradeService"

if %errorlevel% equ 0 (
    echo ✅ Service demarre avec net start.
    goto :verify_status
) else (
    echo ⚠️  net start a echoue, tentative avec sc start...
    sc start "AxiomTradeService"
    
    if %errorlevel% equ 0 (
        echo ✅ Service demarre avec sc start.
    ) else (
        echo ❌ ERREUR: Impossible de demarrer le service.
        echo.
        echo Tentatives de diagnostic:
        echo 1. Verifiez les logs Windows Event Viewer
        echo 2. Essayez de demarrer depuis le Gestionnaire de Services
        echo 3. Verifiez que Python et Flask sont installes
        goto :end_with_error
    )
)

:verify_status
echo.
echo 4. Verification du statut apres demarrage...
timeout /t 5 >nul

for /f "tokens=4" %%i in ('sc query "AxiomTradeService" ^| findstr "STATE"') do set NEW_STATE=%%i
echo Nouveau statut: %NEW_STATE%

if "%NEW_STATE%"=="RUNNING" (
    echo ✅ Service confirme en cours d'execution.
) else (
    echo ❌ Service non confirme comme en cours d'execution.
    echo Statut: %NEW_STATE%
)

:test_connectivity
echo.
echo 5. Test de connectivite...
echo Attente de 10 secondes pour que Flask soit pret...
timeout /t 10 >nul

curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Service accessible sur http://localhost:5000/health
    curl -s http://localhost:5000/health
) else (
    echo ⚠️  Service non accessible sur le port 5000
    echo Le service peut prendre plus de temps a demarrer Flask
    echo Verifiez manuellement: http://localhost:5000/health
)

echo.
echo ========================================
echo Operation terminee avec succes
echo ========================================
pause
exit /b 0

:end_with_error
echo.
echo ========================================
echo Operation terminee avec erreurs
echo ========================================
pause
exit /b 1