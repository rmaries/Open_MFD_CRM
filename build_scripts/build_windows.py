import subprocess
import os
import shutil

def build_windows():
    print("Starting Windows Build Process...")
    
    # 1. Ensure pyinstaller is installed
    subprocess.run(["pip", "install", "pyinstaller", "streamlit"], check=True)

def build_windows():
    print("Starting Windows Build Process...")
    
    # 1. Ensure dependencies
    print("Checking and installing requirements...")
    try:
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: Some requirements failed to install. Attempting to build anyway...")

    # 2. Build command
    # We use run_app.py as the entry point
    # --collect-all is used to ensure metadata and submodules are included
    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--collect-all", "streamlit",
        "--collect-all", "pandas",
        "--collect-all", "numpy_financial",
        "--add-data", "src;src",
        "--add-data", "open_mfd.db;.",
        "--add-data", "USER_GUIDE.md;.",
        "--name", "OpenMFD_CRM",
        "run_app.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print("\nSUCCESS: Build complete! Your executable is in the 'dist' folder.")
        print("Note: When running for the first time, it might take a few seconds to unpack.")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Build failed with return code {e.returncode}")

if __name__ == "__main__":
    build_windows()
