# Camera Access Watchdog

A Windows security-monitoring tool that detects camera-access activity, identifies the responsible application or process when possible, and alerts the user in real time.

The tool monitors Windows camera-access records through the `CapabilityAccessManager` ConsentStore, attempts to resolve process information using `psutil`, and records events and user decisions in a CSV audit log.

> Windows only. This project depends on Windows-specific registry keys and APIs.

## Features

- Polls camera-access records at a configurable interval.
- Detects camera open and close activity where Windows exposes corresponding records.
- Identifies the responsible application, executable path, and process ID when available.
- Displays real-time alerts for unexpected camera activity.
- Supports `Allow` and `Block & Kill` actions.
- Logs camera events and user decisions to a CSV audit file.
- Supports a trusted-application allowlist.
- Provides a one-shot camera-status check.
- Supports background monitoring through Windows Task Scheduler.
- Handles packaged-application limitations without silently treating missing process information as a failure.

## How It Works

Windows manages application permissions for sensitive resources such as the camera through its privacy and capability-management systems.

This project reads camera-related entries from the Windows `CapabilityAccessManager` ConsentStore and compares changes over time.

When a relevant change is detected, the tool:

1. Reads the camera-access entry.
2. Identifies the application or package.
3. Attempts to resolve a live process using `psutil`.
4. Displays an alert when the application is not trusted.
5. Records the event and user decision in the CSV audit log.

The tool does not query or control the physical webcam LED. It monitors operating-system records instead.

## Requirements

- Windows 10 or Windows 11.
- Python 3.9 or later.
- `psutil`.
- Tkinter, if the graphical alert interface is enabled.
- Permission to read the required Windows registry entries.

## Installation

Clone the repository:

```bash
git clone [https://github.com/Adarshmishra87/Camera-Access-Watchdog.git](https://github.com/Adarshmishra87/Camera-Access-Watchdog.git)
cd Camera-Access-Watchdog
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Start continuous monitoring

```bash
python camera_watchdog.py
```

The tool continuously monitors camera-access records and displays an alert when it detects activity from an application that is not trusted.

### Check current camera status

```bash
python camera_watchdog.py --status
```

This performs a one-time status check and exits.

### Run without a console window

Use `pythonw.exe` when launching the tool through a shortcut or Windows Task Scheduler:

```bash
pythonw.exe camera_watchdog.py
```

## Trusted Applications

Create a file named `trusted_apps.txt` in the project directory:

```text
Teams.exe
Zoom.exe
Discord.exe
chrome.exe
msedge.exe
```

Trusted applications will not trigger a popup, but their events should still be recorded in the audit log.

Use one executable name per line. Add an application only if you recognize and trust it.

## Alert Actions

When an alert is displayed, the tool can provide the following actions:

- **Allow:** Dismiss the alert and continue monitoring.
- **Block & Kill:** Attempt to terminate the identified process.
- **Ignore or close:** Keep the process running while recording the event, depending on the implementation.

Process termination may fail when:

- The process belongs to another user.
- The process requires administrator privileges.
- The event belongs to a packaged Microsoft Store application.
- The process has already exited.
- Windows prevents termination.

Always verify the process name and executable path before terminating it.

## Audit Logging

The tool records monitoring activity in:

```text
camera_access_log.csv
```

Typical fields may include:

```text
timestamp
event_type
application
executable_path
process_id
access_state
user_action
```

The log can be opened in a spreadsheet application or processed with Python for later analysis.

Do not upload the log publicly because it may contain usernames, local file paths, application names, and other system information.

## Automatic Startup

To run the watchdog when you sign in:

1. Open **Task Scheduler**.
2. Select **Create Task**.
3. Set the trigger to **At log on**.
4. Set the action to start `pythonw.exe`.
5. Pass the path to `camera_watchdog.py` as the argument.
6. Set the project directory as the working directory.
7. Test the task manually before relying on it.

Example configuration:

```text
Program:
C:\Path\To\Python\pythonw.exe

Arguments:
C:\Path\To\Camera-Access-Watchdog\camera_watchdog.py

Start in:
C:\Path\To\Camera-Access-Watchdog
```

## Project Structure

```text
Camera-Access-Watchdog/
├── camera_watchdog.py
├── requirements.txt
├── trusted_apps.txt
├── camera_access_log.csv
├── README.md
├── LICENSE
└── .gitignore
```

Do not commit local logs or virtual-environment files. Add them to `.gitignore`:

```gitignore
.venv/
__pycache__/
*.pyc
camera_access_log.csv
trusted_apps.txt
```

## Limitations

- The project is Windows-only.
- Registry-based records may not represent every possible camera event.
- Packaged Microsoft Store applications may expose a package family name instead of a directly killable process ID.
- Process identification may fail when an application has already exited or Windows does not expose a matching process.
- Terminating a process can cause unsaved work or application instability.
- Administrator privileges may be required to terminate some processes.
- The tool does not inspect camera firmware, driver internals, or hardware signals.
- It does not guarantee detection of every form of camera compromise.
- A physical camera cover remains the most reliable way to prevent unwanted optical capture.

## Security Notes

This project is a monitoring and investigation utility, not a replacement for endpoint-security software.

For safer use:

- Review the executable path before terminating a process.
- Do not automatically kill every unknown process.
- Keep Windows and security software updated.
- Do not run untrusted scripts with administrator privileges.
- Avoid committing personal logs or trusted-application lists to a public repository.
- Test the tool in a controlled environment before enabling automatic startup.

## Testing Checklist

Before using the tool continuously, test the following:

- Open the Windows Camera application.
- Start a video call in Teams, Zoom, or Discord.
- Add and remove an application from `trusted_apps.txt`.
- Run the `--status` command.
- Confirm that events are written to the CSV log.
- Verify that process termination is handled safely.
- Test behavior when an application closes before the event is processed.
- Test behavior with a packaged Microsoft Store application.

## Future Improvements

- Add automated tests for registry parsing and event comparison.
- Add configurable polling intervals through command-line arguments.
- Add structured JSON logging alongside CSV logging.
- Add Windows Event Log integration.
- Add a system-tray interface.
- Add signed release packages.
- Improve packaged-app detection and user guidance.
- Add notification throttling to prevent repeated alerts.
- Add an optional read-only mode that disables process termination.

## License

This project is licensed under the MIT License.


## Author

**Adarsh Mishra**

- GitHub: [Adarshmishra87](https://github.com/Adarshmishra87)
- LinkedIn: [adarsh-mishra-4b5792319](https://linkedin.com/in/adarsh-mishra-4b5792319)
