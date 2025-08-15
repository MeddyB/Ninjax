@echo off
echo ========================================
echo Demarrage Service Axiom Trade
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
echo Demarrage du service AxiomTradeService...
sc start "AxiomTradeService"

if %errorlevel% equ 0 (
    echo Service demarre avec succes.
) else (
    echo ERREUR: Impossible de demarrer le service.
    echo.
    echo Verification si le service existe...
    sc query "AxiomTradeService" >nul 2>&1
    if %errorlevel% neq 0 (
        echo Le service AxiomTradeService n'est pas installe.
        echo Voulez-vous l'installer maintenant ? (O/N)
        set /p INSTALL_CHOICE=
        if /i "%INSTALL_CHOICE%"=="O" (
            echo Installation du service...
            python flask_service_fixed.py install
            if %errorlevel% equ 0 (
                echo Service installe. Tentative de demarrage...
                sc start "AxiomTradeService"
            )
        )
    ) else (
        echo Le service existe mais ne demarre pas.
        echo Verifiez les logs Windows Event Viewer ou les logs du service.
        echo.
        echo Affichage du statut detaille:
        sc query "AxiomTradeService"
    )
)

echo.
echo Verification du statut...
timeout /t 3 >nul
sc query "AxiomTradeService" | findstr "STATE"

echo.
echo Test de connectivite...
timeout /t 5 >nul
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo Service accessible sur http://localhost:5000
) else (
    echo Service non accessible sur le port 5000
    echo Le service peut prendre plus de temps a demarrer
    echo Ou verifiez si le port 5000 est libre:
    netstat -an | findstr :5000
)

echo.
echo ========================================
echo Operation terminee
echo ========================================
pause