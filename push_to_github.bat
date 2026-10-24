@echo off
TITLE AgentMail AI - Push to GitHub
COLOR 0B

echo ===============================================================================
echo Pushing AgentMail AI to:
echo https://github.com/suryakarthikeyan007/AgentMail-AI.git
echo ===============================================================================

cd /d "C:\Users\Pradeepa\Downloads\Agentic AI email"

"%LOCALAPPDATA%\Programs\Git\cmd\git.exe" push -u origin main

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo ===============================================================================
    echo [SUCCESS] Successfully uploaded to GitHub!
    echo ===============================================================================
    echo.
    echo NEXT STEP: Enable GitHub Pages Deployment
    echo 1. Open: https://github.com/suryakarthikeyan007/AgentMail-AI/settings/pages
    echo 2. Under 'Build and deployment' ^> 'Source', select 'GitHub Actions'.
    echo 3. Your dashboard will be live at:
    echo    https://suryakarthikeyan007.github.io/AgentMail-AI/
    echo ===============================================================================
) ELSE (
    echo.
    echo [NOTE] If a browser window opened, click 'Sign in with your browser' to authorize.
)

pause
