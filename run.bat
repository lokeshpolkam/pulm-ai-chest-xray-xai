@echo off
title PULM-AI: Explainable Chest Radiograph Diagnostic Platform
echo ========================================================
echo   PULM-AI: Deep DenseNet-121 + Grad-CAM Explainable AI
echo   6th Semester Capstone Project Launcher
echo ========================================================
echo Starting Streamlit Application on http://localhost:8501 ...
cd /d "%~dp0"
streamlit run app.py
pause
