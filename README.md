# Camera Access Watchdog

Detects when your webcam is **actually being used** — even if the LED never
turns on — and alerts you with the responsible process, so you can kill it
on the spot.

## Why this works (and what "LED not turning on" actually means)

No piece of software can query the physical LED directly — that circuit is
wired to the camera hardware, and if something is spoofing it, the light is
lying to you by definition. So instead of trusting the light, this tool
watches what Windows itself tracks internally: the `CapabilityAccessManager`
registry ("ConsentStore"), which the OS updates the instant *any* process
opens or closes the camera device. That update happens at the driver level,
completely independent of the LED. This is exactly the signal you want if
you suspect the LED has been tampered with.

## What it does

- Polls the registry every ~2 seconds for camera open/close events
- Resolves the responsible process to a live PID (via `psutil`) where possible
- Pops up an alert naming the app, path, and PID
- Lets you **Allow** (dismiss) or **Block & Kill** (terminate the process)
  right from the popup
- Logs every open/close event and every decision you make to
  `camera_access_log.csv` for an audit trail
- Supports a `trusted_apps.txt` allowlist so apps you expect (Zoom, Teams,
  Discord, your browser) don't spam you with alerts — they're still logged,
  just not popped up

## Setup

```bash
pip install -r requirements.txt
```

Windows only — it depends on `winreg` and the CapabilityAccessManager keys,
neither of which exist on macOS/Linux. See "Limitations" below for what to
do on those platforms instead.

## Usage

Run it in the background while you work:

```bash
python camera_watchdog.py
```

One-shot check — "is anything using my camera right now?":

```bash
python camera_watchdog.py --status
```

Whitelist an app you trust so it stops popping alerts (still logged):

```
# trusted_apps.txt
Teams.exe
Zoom.exe
Discord.exe
```

### Run it automatically at login

Windows Task Scheduler → Create Task → Trigger: "At log on" → Action: run
`pythonw.exe camera_watchdog.py` (use `pythonw` instead of `python` so no
console window stays open).

## Limitations — read this before you trust it fully

- **Windows only.** The registry path this relies on doesn't exist on other
  OSes.
- **Store/packaged apps** (from the Microsoft Store) are only identified by
  a `PackageFamilyName`, not a running PID, so those get logged and alerted
  on but can't be auto-killed from here — you'd close them from Settings ▸
  Privacy ▸ Camera or Task Manager.
- **What this reliably catches:** the overwhelming majority of real-world
  webcam-hijacking malware, RATs, and spyware, because all of them still
  have to go through the same OS camera broker to get frames — there's no
  legitimate way around it on modern Windows.
- **What this does *not* catch:** an attacker who has compromised the
  camera's own firmware deeply enough to bypass the Windows capability
  broker entirely and read frames at a level the OS can't see. That class
  of attack requires hardware/driver-level compromise and is extremely
  rare — well outside what any user-space script (from any vendor) can
  detect. If you're worried about that specific scenario, a physical
  camera cover is still the only 100% guarantee.

## Ideas to extend it (good next portfolio additions)

- Resolve packaged-app `PackageFamilyName` → friendly name via
  `Windows.Management.Deployment.PackageManager` for nicer alert text
- Add a system tray icon (`pystray`) instead of only console + popups
- Ship a "quarantine" mode: on Block, also suspend the process
  (`psutil.Process.suspend()`) before deciding whether to fully kill it
- Extend the same pattern to the **microphone** ConsentStore key
  (`...\ConsentStore\microphone`) — same technique, same registry shape
- On Linux, an analogous (much rougher) approach is polling
  `lsof /dev/video0` or watching `/sys/class/video4linux/*/name` combined
  with process file-descriptor scanning — no registry equivalent exists,
  so attribution is less clean
