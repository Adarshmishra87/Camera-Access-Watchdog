import csv
import ctypes
import datetime
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

if sys.platform != "win32":
    sys.exit(
        "Camera Watchdog relies on Windows-only APIs (winreg / CapabilityAccessManager).\n"
        "This won't run on macOS/Linux. See README.md for notes on alternative "
        "approaches for those platforms."
    )

import winreg  # noqa: E402  (Windows-only import, deliberately after the platform check)
import psutil  # noqa: E402

try:
    import winsound
except ImportError:
    winsound = None


CONSENT_BASE = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camera_access_log.csv")
TRUSTED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trusted_apps.txt")
POLL_INTERVAL_SECONDS = 2

# Windows FILETIME epoch (1601-01-01) offset to Unix epoch, in 100-ns units
FILETIME_EPOCH_DELTA = 116444736000000000


def filetime_to_datetime(qword_value):
    """Convert a Windows FILETIME (as an int) to a Python datetime, or None if 0/invalid."""
    if not qword_value:
        return None
    try:
        unix_100ns = qword_value - FILETIME_EPOCH_DELTA
        return datetime.datetime.fromtimestamp(unix_100ns / 10_000_000, tz=datetime.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def load_trusted_apps():
    """Read a simple list of process names (one per line) the user has whitelisted,
    e.g. 'Teams.exe', 'Zoom.exe'. These still get logged, just not popped up."""
    if not os.path.exists(TRUSTED_FILE):
        return set()
    with open(TRUSTED_FILE, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}


def read_consent_store():
    """
    Returns a dict keyed by app identifier -> {
        'active': bool,
        'exe_path': str or None,
        'start': datetime or None,
        'kind': 'desktop' or 'packaged',
    }
    """
    results = {}

    def scan(key_path, kind):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            return
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
            except OSError:
                break
            i += 1
            if kind == "desktop" and subkey_name.lower() == "nonpackaged":
                # handled separately below
                continue
            try:
                subkey = winreg.OpenKey(key, subkey_name)
                stop_val, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStop")
                start_val = None
                try:
                    start_val, _ = winreg.QueryValueEx(subkey, "LastUsedTimeStart")
                except FileNotFoundError:
                    pass
                winreg.CloseKey(subkey)
            except (FileNotFoundError, OSError):
                continue

            active = (stop_val == 0)
            exe_path = None
            if kind == "desktop":
                # NonPackaged subkey names look like: C#Program Files#App#app.exe
                exe_path = subkey_name.replace("#", "\\")

            results[subkey_name] = {
                "active": active,
                "exe_path": exe_path,
                "start": filetime_to_datetime(start_val) if start_val else None,
                "kind": kind,
            }
        winreg.CloseKey(key)

    scan(CONSENT_BASE, "packaged")
    scan(CONSENT_BASE + r"\NonPackaged", "desktop")
    return results


def find_process_for_exe(exe_path):
    """Best-effort match of a filesystem path to a live psutil Process."""
    if not exe_path:
        return None
    target = exe_path.lower()
    for proc in psutil.process_iter(attrs=["pid", "name", "exe"]):
        try:
            p_exe = proc.info.get("exe")
            if p_exe and p_exe.lower() == target:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def ensure_log_header():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "app_id", "kind", "exe_path", "pid", "event", "action"])


def log_event(app_id, kind, exe_path, pid, event, action=""):
    ensure_log_header()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                          app_id, kind, exe_path or "", pid or "", event, action])


class CameraWatchdog:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.stop_flag = threading.Event()
        self.trusted = load_trusted_apps()
        self.previously_active = set()

    def poll_loop(self):
        while not self.stop_flag.is_set():
            try:
                current = read_consent_store()
            except Exception as e:  # registry hiccups shouldn't kill the thread
                print(f"[watchdog] registry read error: {e}")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            currently_active = {app_id for app_id, info in current.items() if info["active"]}
            newly_active = currently_active - self.previously_active

            for app_id in newly_active:
                info = current[app_id]
                proc = find_process_for_exe(info["exe_path"]) if info["exe_path"] else None
                pid = proc.pid if proc else None
                proc_name = proc.name() if proc else (os.path.basename(info["exe_path"]) if info["exe_path"] else app_id)

                log_event(app_id, info["kind"], info["exe_path"], pid, "camera_opened")

                if proc_name.lower() in self.trusted:
                    continue  # whitelisted, silent (but logged above)

                self.event_queue.put({
                    "app_id": app_id,
                    "kind": info["kind"],
                    "exe_path": info["exe_path"],
                    "pid": pid,
                    "proc_name": proc_name,
                })

            # also log stop events for completeness
            newly_stopped = self.previously_active - currently_active
            for app_id in newly_stopped:
                log_event(app_id, current.get(app_id, {}).get("kind", "?"),
                          current.get(app_id, {}).get("exe_path"), "", "camera_closed")

            self.previously_active = currently_active
            time.sleep(POLL_INTERVAL_SECONDS)

    def start(self):
        thread = threading.Thread(target=self.poll_loop, daemon=True)
        thread.start()
        return thread


class AlertUI:
    def __init__(self, watchdog: CameraWatchdog):
        self.watchdog = watchdog
        self.root = tk.Tk()
        self.root.withdraw()  # no visible main window, just spawns alert popups
        self.root.after(500, self.check_queue)

    def check_queue(self):
        try:
            while True:
                event = self.watchdog.event_queue.get_nowait()
                self.show_alert(event)
        except queue.Empty:
            pass
        self.root.after(500, self.check_queue)

    def show_alert(self, event):
        if winsound:
            try:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

        win = tk.Toplevel(self.root)
        win.title("Camera Access Detected")
        win.attributes("-topmost", True)
        win.resizable(False, False)

        pid_txt = event["pid"] if event["pid"] else "unknown (packaged app)"
        msg = (
            f"Your camera was just opened by:\n\n"
            f"  Process:  {event['proc_name']}\n"
            f"  PID:      {pid_txt}\n"
            f"  Path:     {event['exe_path'] or '(Windows Store app, no exe path)'}\n\n"
            f"This fired regardless of whether the camera LED is on, so check "
            f"if you expected this."
        )

        tk.Label(win, text=msg, justify="left", padx=16, pady=12, font=("Segoe UI", 10)).pack()

        btn_frame = tk.Frame(win, pady=10)
        btn_frame.pack()

        def on_allow():
            log_event(event["app_id"], event["kind"], event["exe_path"], event["pid"],
                      "user_decision", "allowed")
            win.destroy()

        def on_block():
            action = "block_failed_no_pid"
            if event["pid"]:
                try:
                    proc = psutil.Process(event["pid"])
                    proc.terminate()
                    action = "blocked_terminated"
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    messagebox.showerror("Camera Watchdog", f"Could not terminate process: {e}")
                    action = f"block_failed_{type(e).__name__}"
            else:
                messagebox.showwarning(
                    "Camera Watchdog",
                    "This is a packaged Windows app with no resolvable PID -- "
                    "close it manually from Task Manager or Settings > Privacy > Camera."
                )
            log_event(event["app_id"], event["kind"], event["exe_path"], event["pid"],
                      "user_decision", action)
            win.destroy()

        tk.Button(btn_frame, text="Allow", width=12, command=on_allow).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Block & Kill", width=12, bg="#c0392b", fg="white",
                  command=on_block).pack(side="left", padx=8)

        win.protocol("WM_DELETE_WINDOW", on_allow)  # closing the window == allow, but still logged

    def run(self):
        self.root.mainloop()


def print_status_once():
    """One-shot CLI check: `python camera_watchdog.py --status`"""
    current = read_consent_store()
    active = [(app_id, info) for app_id, info in current.items() if info["active"]]
    if not active:
        print("No app currently holds the camera open.")
        return
    print("Camera currently OPEN by:")
    for app_id, info in active:
        proc = find_process_for_exe(info["exe_path"]) if info["exe_path"] else None
        pid = proc.pid if proc else "n/a"
        print(f"  - {info['exe_path'] or app_id}  (pid={pid}, kind={info['kind']})")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        print_status_once()
        return

    print("Camera Watchdog running. Polling every "
          f"{POLL_INTERVAL_SECONDS}s. Ctrl+C in this console to stop.")
    print(f"Log file: {LOG_FILE}")
    if not os.path.exists(TRUSTED_FILE):
        with open(TRUSTED_FILE, "w", encoding="utf-8") as f:
            f.write("# One process name per line, e.g. Teams.exe\n# These are still logged, just not popped up.\n")

    watchdog = CameraWatchdog()
    watchdog.start()
    ui = AlertUI(watchdog)
    ui.run()


if __name__ == "__main__":
    main()
