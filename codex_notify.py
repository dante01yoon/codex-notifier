#!/usr/bin/env python3

import json
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: notify.py <NOTIFICATION_JSON>")
        return 1

    try:
        notification = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        return 1

    notification_type = notification.get("type")

    if notification_type == "agent-turn-complete":
        assistant_message = notification.get("last-assistant-message")
        if assistant_message:
            title = f"Codex: {assistant_message}"
        else:
            title = "Codex: Turn Complete!"
        input_messages = notification.get("input_messages", [])
        message = " ".join(input_messages)
        title += message
    else:
        print(f"not sending a push notification for: {notification_type}")
        return 0

    cmd = [
        "terminal-notifier",
        "-title",
        title,
        "-message",
        message,
        "-group",
        "codex",
        "-ignoreDnD",
        "-activate",
        "com.googlecode.iterm2",
        "-sound",
        "default",
    ]

    subprocess.check_output(
        cmd
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
