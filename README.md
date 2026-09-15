# ☕ TempShield — Disposable Email Client

A lightweight Java desktop email client that generates disposable email addresses, monitors incoming messages in real time, detects OTPs, and provides one-click clipboard copying.

The tool uses Java Swing for its graphical interface, the Guerrilla Mail API for temporary inbox functionality, `HttpURLConnection` for HTTP communication, `org.json` for response parsing, and `ExecutorService` for background inbox polling.

> Use only for lawful, authorized, and privacy-conscious purposes. Do not use disposable email services for spam, fraud, harassment, unauthorized access, or bypassing service restrictions.

## Features

- Generates disposable email addresses instantly.
- Supports multiple Guerrilla Mail domains.
- Polls the inbox automatically every 15 seconds.
- Displays incoming messages in real time.
- Shows sender, subject, message content, and received time.
- Detects OTPs and verification codes automatically.
- Copies email addresses and OTPs with one click.
- Includes a built-in one-hour mailbox countdown.
- Provides a modern dark-themed Java Swing interface.
- Uses background tasks to keep the interface responsive.
- Requires no build framework or dependency manager.
- Communicates with the Guerrilla Mail API over HTTP.

## How It Works

TempShield communicates with the Guerrilla Mail API to create and monitor a temporary mailbox.

When the application starts, it:

1. Requests a disposable email address.
2. Displays the address in the Swing interface.
3. Starts a background polling task.
4. Checks for new messages at the configured interval.
5. Parses the returned JSON data.
6. Displays available email details.
7. Searches message content for OTPs and verification codes.
8. Provides one-click clipboard actions.
9. Tracks the mailbox lifetime with a countdown timer.

Background work is handled with `ExecutorService` so that network requests do not freeze the graphical interface.

The application monitors messages through the API. It does not provide permanent email storage and should not be used for sensitive or confidential communication.

## Requirements

- Java 11 or later.
- Windows, Linux, or macOS.
- An active internet connection.
- Access to the Guerrilla Mail API.
- The `org.json` library.
- Permission to use the disposable email service.

## Installation

Clone the repository:

```bash
git clone [https://github.com/Adarshmishra87/TempShield.git](https://github.com/Adarshmishra87/TempShield.git)
cd TempShield
```

Download the JSON library:

```bash
curl -L "[https://repo1.maven.org/maven2/org/json/json/20231013/json-20231013.jar](https://repo1.maven.org/maven2/org/json/json/20231013/json-20231013.jar)" \
  -o json-20231013.jar
```

No additional package installation is required.

## Usage

### Windows

Double-click the following script:

```text
build_and_run.bat
```

Or compile and run manually:

```bash
javac -cp json-20231013.jar src/TempMailApp.java -d out/
java -cp "out;json-20231013.jar" TempMailApp
```

### Linux/macOS

Make the script executable:

```bash
chmod +x build_and_run.sh
```

Run the application:

```bash
./build_and_run.sh
```

Or compile and run manually:

```bash
javac -cp json-20231013.jar src/TempMailApp.java -d out/
java -cp "out:json-20231013.jar" TempMailApp
```

## Inbox Monitoring

The inbox is refreshed automatically every 15 seconds by default.

The polling interval is configured in `TempMailApp.java`. Look for the scheduled background task:

```java
scheduleAtFixedRate(task, 0, 15, TimeUnit.SECONDS);
```

To refresh every 30 seconds:

```java
scheduleAtFixedRate(task, 0, 30, TimeUnit.SECONDS);
```

A shorter interval may show new messages sooner but can result in more API requests. A longer interval reduces requests but may delay inbox updates.

## OTP Detection

TempShield searches incoming message content for common OTP and verification-code patterns.

Example formats may include:

```text
123456
OTP: 123456
Code: 123456
Your verification code is 123456
```

OTP detection is pattern-based and may not recognize every message format. Review the detected code before using it.

## Clipboard Actions

The interface provides one-click copying for:

- The generated disposable email address.
- Detected OTPs or verification codes.

Clipboard contents may be accessible to other applications on the system. Avoid copying sensitive information on shared or untrusted computers.

## Project Structure

```text
TempShield/
├── src/
│   └── TempMailApp.java
├── out/
├── json-20231013.jar
├── build_and_run.bat
├── build_and_run.sh
├── README.md
├── LICENSE
└── .gitignore
```

Do not commit local build files, secrets, or private email content. A suitable `.gitignore` may include:

```gitignore
out/
*.class
.venv/
__pycache__/
*.log
```

## Architecture

```text
                 Java Swing UI
                       │
                       ▼
               Email Controller
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
 Guerrilla Mail API          Background Polling
        │                    (ExecutorService)
        │                             │
        └──────────────┬──────────────┘
                       ▼
               Email Message Parser
                       │
                       ▼
          OTP Detection & Clipboard
```

## Screenshots

### Home Screen

_Add screenshot here._

### Inbox

_Add screenshot here._

### Email Viewer

_Add screenshot here._

## Limitations

- Depends on the availability and behavior of the Guerrilla Mail API.
- Requires an active internet connection.
- Disposable email domains may be blocked by third-party services.
- Mailbox lifetime may be limited.
- Inbox polling may delay message updates.
- OTP detection depends on the format of the email.
- Message delivery is not guaranteed.
- The application does not provide permanent email storage.
- Temporary inboxes may not be private or suitable for confidential information.
- API behavior, supported domains, and service policies may change.
- The application is not a replacement for a secure permanent email provider.

## Privacy and Security Notes

For safer use:

- Do not use disposable inboxes for banking, recovery, healthcare, or other sensitive accounts.
- Do not store passwords, private documents, or financial information in temporary mailboxes.
- Do not share mailbox addresses containing private messages.
- Review email content before copying OTPs or verification codes.
- Follow the Guerrilla Mail terms of service.
- Do not use TempShield for spam, fraud, harassment, or unauthorized access.
- Avoid logging or publishing email content without permission.
- Review third-party dependencies before building the application.

## Safe Testing Uses

TempShield may be useful for:

- Testing email verification flows in applications you own.
- Local development and QA workflows.
- Demonstrating email polling and JSON parsing.
- Testing OTP extraction logic.
- Educational Java Swing projects.
- Privacy-conscious uses where temporary email is explicitly permitted.

Do not use it to:

- Circumvent identity, age, or access verification.
- Create accounts in violation of a service's rules.
- Evade bans or rate limits.
- Send unsolicited bulk email.
- Impersonate another person or organization.
- Obtain unauthorized access to services.

## Testing Checklist

Before using the application regularly, test the following:

- Generate a disposable email address.
- Send a test message to the generated address.
- Confirm that the inbox refreshes correctly.
- Open and read a received message.
- Test OTP detection with different code formats.
- Copy the email address and OTP to the clipboard.
- Confirm that the mailbox countdown updates correctly.
- Test behavior when the API is unavailable.
- Test behavior when the network connection is interrupted.
- Confirm that background tasks stop when the application closes.

## Future Improvements

- Add desktop notifications.
- Add email attachment support.
- Support multiple inboxes.
- Add configurable polling intervals.
- Export emails to text, JSON, or HTML.
- Add a cross-platform installer.
- Create a JavaFX version.
- Add push notification support.
- Add email search.
- Add email history.
- Improve OTP and verification-code detection.
- Add configurable mailbox expiration.
- Add API retry and error handling.
- Add unit tests for API and parser components.
- Add a read-only privacy mode.
- Add localization support.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Author

**Adarsh Mishra**

- GitHub: [Adarshmishra87](https://github.com/Adarshmishra87)
- LinkedIn: [adarsh-mishra-4b5792319](https://linkedin.com/in/adarsh-mishra-4b5792319)

## Repository

[TempShield](https://github.com/Adarshmishra87/TempShield)

---

Developed with ❤️ using Java.
