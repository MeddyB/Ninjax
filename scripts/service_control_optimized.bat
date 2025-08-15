@echo off
REM ========================================
REM Scripts de Contrôle Service Optimisés
REM Utilise obj=LocalSystem pour éviter les permissions
REM ========================================

if "%1"=="" goto :show_usage
if "%1"=="start" goto :start_service
if "%1"=="stop" goto :stop_service
if "%1"=="restart" goto :restart_service
if "%1"=="status" goto :status_service
goto :show_usage

:start_service
echo Démarrage du service AxiomTradeService...
sc start "AxiomTradeService"
if %errorlevel% equ 0 (
    echo ✅ Service démarré avec succès !
) else (
    echo ❌ Erreur lors du démarrage
)
goto :end

:stop_service
echo Arrêt du service AxiomTradeService...
sc stop "AxiomTradeService"
if %errorlevel% equ 0 (
    echo ✅ Service arrêté avec succès !
) else (
    echo ❌ Erreur lors de l'arrêt
)
goto :end

:restart_service
echo Redémarrage du service AxiomTradeService...
sc stop "AxiomTradeService"
timeout /t 3 /nobreak >nul
sc start "AxiomTradeService"
if %errorlevel% equ 0 (
    echo ✅ Service redémarré avec succès !
) else (
    echo ❌ Erreur lors du redémarrage
)
goto :end

:status_service
echo Statut du service AxiomTradeService:
sc query "AxiomTradeService"
goto :end

:show_usage
echo Usage: %0 [start^|stop^|restart^|status]
echo.
echo Exemples:
echo   %0 start    - Démarre le service
echo   %0 stop     - Arrête le service
echo   %0 restart  - Redémarre le service
echo   %0 status   - Affiche le statut
goto :end

:end
if not "%2"=="silent" pause