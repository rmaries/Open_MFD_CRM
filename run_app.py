import streamlit.web.cli as stcli
import os, sys
import subprocess
import time
import threading

def resolve_path(path):
    # This handles the temp directory where PyInstaller unpacks resources
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, path)

def launch_app_window():
    """Wait for the server to start and then launch the browser in app mode."""
    # Give the streamlit server time to start up
    time.sleep(5)
    url = "http://localhost:8501"
    
    # Try Edge (usually present on Windows)
    try:
        subprocess.run(["cmd", "/c", f"start msedge --app={url}"], check=True)
    except:
        # Fallback to Chrome
        try:
            subprocess.run(["cmd", "/c", f"start chrome --app={url}"], check=True)
        except:
            # Last fallback to default browser
            import webbrowser
            webbrowser.open(url)

if __name__ == "__main__":
    # Start the window launcher in a separate thread
    threading.Thread(target=launch_app_window, daemon=True).start()
    
    # This is the entry point for the PyInstaller executable
    app_path = resolve_path("src/app.py")
    
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",  # Prevent opening default browser tab
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
