#!/bin/bash
echo "=========================================================="
echo "   PULM-AI: Explainable Chest X-Ray & Oncology Suite"
echo "            30-Second Fast Start Launcher"
echo "=========================================================="
echo ""

cd "$(dirname "$0")"

echo "[1/2] Verifying Python Dependencies..."
pip install -r requirements.txt --quiet --disable-pip-version-check

echo "[2/2] Launching PACS Clinical Dashboard..."
streamlit run app.py --server.headless=true
