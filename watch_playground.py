"""
File watcher - tự động chạy playground.py mỗi khi bạn save file đó.
Chạy một lần: python watch_playground.py
Sau đó cứ save playground.py là nó tự chạy lại.
"""

import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_FILE = Path(__file__).parent / "playground.py"
PYTHON = sys.executable


class PlaygroundHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if Path(event.src_path).resolve() == WATCH_FILE.resolve():
            print("\n" + "=" * 40)
            print(f"[watcher] Detected change, running {WATCH_FILE.name}...")
            print("=" * 40)
            subprocess.run([PYTHON, str(WATCH_FILE)])
            print("=" * 40 + "\n")


if __name__ == "__main__":
    if not WATCH_FILE.exists():
        print(f"[watcher] {WATCH_FILE.name} not found, creating it...")
        WATCH_FILE.write_text("# Viết code ở đây, save là tự chạy\n")

    print(f"[watcher] Watching {WATCH_FILE.name} for changes... (Ctrl+C to stop)")

    # Chạy ngay lần đầu
    subprocess.run([PYTHON, str(WATCH_FILE)])

    handler = PlaygroundHandler()
    observer = Observer()
    observer.schedule(handler, path=str(WATCH_FILE.parent), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[watcher] Stopped.")

    observer.join()
