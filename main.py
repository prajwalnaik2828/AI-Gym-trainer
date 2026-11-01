import os
import sys
import time
import threading
import subprocess
import webbrowser
from pathlib import Path

# Important for Windows: load OpenCV & MediaPipe C++ runtime first
import cv2
import mediapipe as mp

# Add 'src' directory to Python path
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def open_browser(url: str, delay: float = 1.0):
    """Open the application in the default browser so the address bar and camera permission prompts are fully accessible."""
    def _open():
        time.sleep(delay)
        webbrowser.open(url)

    t = threading.Thread(target=_open, daemon=True)
    t.start()


def launch_web_app(port: int = 8000):
    """Launch the AI Gym Trainer application."""
    from webapp.server import app

    url = f"http://localhost:{port}"

    print("=" * 60)
    print("           AI Gym Trainer Application Starting")
    print("=" * 60)
    print(f"  App URL  : {url}")
    print("  Opening browser...")
    print("  Tip      : When prompted by your browser, click 'Allow' for Camera.")
    print("  Press Ctrl+C in this terminal to stop.")
    print("=" * 60)

    # Automatically launch browser with accessible address bar
    open_browser(url, delay=1.0)

    # Run the web server
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)


def launch_qt_gui():
    """Optional Qt GUI launcher if explicitly requested via --qt."""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from gui.main_window import MainWindow

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("AI Gym Trainer")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


def main():
    # If exercise argument (-t / --exercise_type) is provided, run CLI mode
    if any(arg in sys.argv for arg in ["-t", "--exercise_type", "-h", "--help"]):
        import importlib
        cli_module = importlib.import_module("main")
    elif "--qt" in sys.argv or "--desktop-qt" in sys.argv:
        launch_qt_gui()
    else:
        # Default: Launch the original application design!
        port = int(os.environ.get("PORT", 8000))
        launch_web_app(port=port)


if __name__ == "__main__":
    main()
