import os
import subprocess
import shutil
import urllib.request
import zipfile
import time

# Configuration
WINPYTHON_URL = "https://github.com/winpython/winpython/releases/download/17.2.20251222final/WinPython64-3.13.11.0dot.exe"
BUILD_DIR = "build_portable"
DIST_NAME = "Open-MFD-CRM-Portable"
FINAL_ZIP = f"dist/{DIST_NAME}.zip"

def build_portable():
    print(f"--- Starting Portable Build Process for {DIST_NAME} ---")
    
    # 1. Cleanup and Setup
    if os.path.exists(BUILD_DIR):
        print(f"Cleaning up old build directory: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)
    
    if not os.path.exists("dist"):
        os.makedirs("dist")

    portable_root = os.path.join(BUILD_DIR, DIST_NAME)
    os.makedirs(portable_root)
    
    # 2. Download WinPython
    winpython_exe = os.path.join(BUILD_DIR, "winpython_setup.exe")
    print(f"Downloading WinPython Zero from: {WINPYTHON_URL}")
    print("This may take a minute depending on your connection...")
    urllib.request.urlretrieve(WINPYTHON_URL, winpython_exe)
    
    # 3. Extract WinPython
    # WinPython installers are 7zip archives. Running with /S extracts to a folder next to it.
    # However, /D specifies the target directory.
    print("Extracting WinPython environment...")
    extract_path = os.path.abspath(os.path.join(BUILD_DIR, "winpython_extracted"))
    subprocess.run([winpython_exe, "/S", f"/D={extract_path}"], check=True)
    
    # Locate the python folder (it's usually 'python-3.x.x.amd64' or similar inside the extracted folder)
    extracted_contents = os.listdir(extract_path)
    python_folder_name = next((f for f in extracted_contents if f.startswith('python-')), None)
    
    if not python_folder_name:
        # Sometimes WinPython extracts directly or has a different structure
        # Let's look for python.exe
        for root, dirs, files in os.walk(extract_path):
            if "python.exe" in files:
                python_source = root
                break
        else:
            raise Exception("Could not find python.exe in extracted WinPython")
    else:
        python_source = os.path.join(extract_path, python_folder_name)

    # Move python to the portable root
    python_target = os.path.join(portable_root, "python-env")
    print(f"Moving Python environment to: {python_target}")
    shutil.move(python_source, python_target)
    
    # 4. Copy Application Code
    crm_code_path = os.path.join(portable_root, "crm_code")
    print(f"Copying CRM code to: {crm_code_path}")
    os.makedirs(crm_code_path)
    
    # Files/Dirs to copy
    to_copy = ["src", "run_app.py", "open_mfd.db", "requirements.txt", "USER_GUIDE.md"]
    for item in to_copy:
        if os.path.isdir(item):
            shutil.copytree(item, os.path.join(crm_code_path, item))
        elif os.path.exists(item):
            shutil.copy2(item, crm_code_path)

    # 5. Install Dependencies into Portable Env
    print("Installing dependencies into the portable environment...")
    python_exe = os.path.join(python_target, "python.exe")
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([python_exe, "-m", "pip", "install", "-r", os.path.join(crm_code_path, "requirements.txt")], check=True)
    
    # 6. Create Start_CRM.bat
    print("Creating Start_CRM.bat...")
    bat_content = """@echo off
setlocal
echo Launching Open-MFD CRM Portable...
cd /d "%~dp0"

:: Set paths relative to batch file location
set PYTHON_EXE="%~dp0python-env\\python.exe"
set APP_SCRIPT="%~dp0crm_code\\run_app.py"

:: Run the application
%PYTHON_EXE% %APP_SCRIPT%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo App closed with an error (Code: %ERRORLEVEL%)
    pause
)
endlocal
"""
    with open(os.path.join(portable_root, "Start_CRM.bat"), "w") as f:
        f.write(bat_content)

    # 7. Zip the whole thing
    print(f"Creating final distribution: {FINAL_ZIP}")
    if os.path.exists(FINAL_ZIP):
        os.remove(FINAL_ZIP)
        
    shutil.make_archive(os.path.splitext(FINAL_ZIP)[0], 'zip', BUILD_DIR, DIST_NAME)

    print("\n" + "="*40)
    print("SUCCESS: Portable build created!")
    print(f"Location: {os.path.abspath(FINAL_ZIP)}")
    print("="*40)

if __name__ == "__main__":
    try:
        build_portable()
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
