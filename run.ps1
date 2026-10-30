# PULM-AI PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  PULM-AI: Deep DenseNet-121 + Grad-CAM Explainable AI" -ForegroundColor Green
Write-Host "  6th Semester Capstone Project Launcher" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
streamlit run app.py
