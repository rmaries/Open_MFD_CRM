#!/bin/bash

echo "Starting Linux Build Process..."

# 1. Ensure dependencies
pip install pyinstaller streamlit

# 2. Run PyInstaller
pyinstaller --onefile \
    --add-data "src:src" \
    --add-data "open_mfd.db:." \
    --name "OpenMFD_CRM_Linux" \
    src/app.py

echo "Build complete! Check the 'dist' folder."
