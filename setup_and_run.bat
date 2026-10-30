@echo off
title PULM-AI Quick Launcher
echo ==========================================================
echo    PULM-AI: Explainable Chest X-Ray & Oncology Suite
echo             30-Second Fast Start Launcher
echo ==========================================================
echo.

cd /d "%~dp0"

echo [1/2] Verifying Python Dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] Launching PACS Clinical Dashboard...
streamlit run app.py --server.headless=true
pause
