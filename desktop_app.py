"""
LightShare - Native Python Desktop GUI Launcher (V1.0)
Strictly prioritizes Google Chrome as the dedicated Desktop App Window.
Runs on Windows, macOS, and Linux with zero Node.js/npm dependencies required.
"""

import sys
import os
import time
import socket
import subprocess
import threading
import webbrowser
import shutil

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import DEFAULT_PORT, get_local_ip

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if the local server port is actively listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def wait_for_server(port: int, host: str = "127.0.0.1", timeout: float = 8.0) -> bool:
    """Poll socket until FastAPI server is ready to accept connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            return True
        time.sleep(0.15)
    return False

def run_fastapi_server():
    """Run uvicorn server in daemon thread."""
    try:
        import uvicorn
        from app.main import app
        uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="warning")
    except Exception as e:
        print(f"[*] Server thread info: {e}")

def get_chrome_executable() -> str:
    """Find Google Chrome executable path across Windows, macOS, and Linux."""
    # 1. Windows Registry Search for Google Chrome
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                val, _ = winreg.QueryValueEx(key, "")
                if val and os.path.exists(val):
                    return val
        except Exception:
            pass

        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
                val, _ = winreg.QueryValueEx(key, "")
                if val and os.path.exists(val):
                    return val
        except Exception:
            pass

        # Standard Windows Google Chrome Paths
        win_candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            # Chromium / Brave / Vivaldi
            os.path.expandvars(r"%LocalAppData%\Chromium\Application\chrome.exe"),
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ]
        for path in win_candidates:
            if path and os.path.exists(path):
                return path

    # 2. macOS Chrome Paths
    elif sys.platform == "darwin":
        mac_candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        ]
        for path in mac_candidates:
            if os.path.exists(path):
                return path

    # 3. Linux Chrome Paths
    else:
        linux_binaries = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "brave-browser"]
        for b in linux_binaries:
            found = shutil.which(b)
            if found:
                return found

    return ""

def launch_desktop_gui():
    """Launch Google Chrome in dedicated App Window Mode."""
    target_url = f"http://127.0.0.1:{DEFAULT_PORT}"
    
    # 1. Strictly locate and launch Google Chrome
    chrome_exe = get_chrome_executable()
    if chrome_exe:
        try:
            print(f"[*] Launching Google Chrome dedicated window: {chrome_exe}")
            subprocess.Popen([
                chrome_exe, 
                f"--app={target_url}", 
                "--window-size=1200,860", 
                "--app-id=LightShare",
                "--disable-http-cache",
                "--no-first-run",
                "--no-default-browser-check"
            ])
            return
        except Exception as e:
            print(f"[!] Chrome launch warning: {e}")

    # 2. Fallback: PyWebView if installed
    try:
        import importlib
        if importlib.util.find_spec("webview"):
            webview = importlib.import_module("webview")
            print(f"[*] Starting LightShare Native Desktop Window ({target_url})...")
            webview.create_window(
                title="LightShare V1.0",
                url=target_url,
                width=1200,
                height=860,
                min_size=(360, 560),
                background_color='#060813'
            )
            webview.start()
            return
    except Exception:
        pass

    # 3. Fallback: Default system browser
    print(f"[*] Opening LightShare in browser: {target_url}")
    webbrowser.open(target_url)

def main():
    local_ip = get_local_ip()
    print("=" * 60)
    print("      [APP] LIGHTSHARE V1.0 - DESKTOP APP LAUNCHER")
    print(f"      [LAN] Host IP: http://{local_ip}:{DEFAULT_PORT}")
    print("=" * 60)
    
    # Check if server is already running
    if not is_port_in_use(DEFAULT_PORT):
        # Start server in background daemon thread
        server_thread = threading.Thread(target=run_fastapi_server, daemon=True)
        server_thread.start()
        
        # Wait until port is actively ready
        print("[*] Waiting for server initialization...")
        server_ready = wait_for_server(DEFAULT_PORT, timeout=8.0)
        if not server_ready:
            print("[!] Server took longer than usual, proceeding with GUI launch...")
    else:
        print(f"[*] Server already listening on port {DEFAULT_PORT}. Connecting...")

    # Launch GUI in Google Chrome
    launch_desktop_gui()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Exiting LightShare...")

if __name__ == "__main__":
    main()

