#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from textwrap import shorten
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
ICON_DIR = BASE_DIR / "icons"
EMOJI_PALETTE: Sequence[str] = ("✨", "🚀", "🤖", "🎯", "🌈", "🪄", "⚡️")
EMOJI_ICON_FILES: dict[str, str] = {
    "✨": "sparkles.png",
    "🚀": "rocket.png",
    "🤖": "robot.png",
    "🎯": "target.png",
    "🌈": "rainbow.png",
    "🪄": "wand.png",
    "⚡️": "bolt.png",
}
ICON_ENV_VAR = "CODEX_NOTIFIER_ICON"
SOUND_ENV_VAR = "CODEX_NOTIFIER_SOUND"
SOUND_DISABLE_VALUES = {"none", "silent", "off"}
SOUND_SEARCH_PATHS = (
    Path.home() / "Library" / "Sounds",
    Path("/Library/Sounds"),
    Path("/System/Library/Sounds"),
)
SOUND_FILE_EXTENSIONS = {".aiff", ".caf", ".wav", ".mp3", ".m4a"}


def _build_sound_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for directory in SOUND_SEARCH_PATHS:
        if not directory.exists():
            continue
        try:
            entries = list(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in SOUND_FILE_EXTENSIONS:
                continue
            lookup[entry.stem.lower()] = entry.stem
    return lookup


SYSTEM_SOUND_LOOKUP = _build_sound_lookup()


def _sanitize(text: str | None) -> str | None:
    if not text:
        return None
    return " ".join(text.split())


def _pick_emoji(seed: str | None) -> str:
    if not seed:
        return EMOJI_PALETTE[0]
    digest = hashlib.sha1(seed.encode("utf-8", "ignore")).digest()
    return EMOJI_PALETTE[digest[0] % len(EMOJI_PALETTE)]


def _format_message(messages: Sequence[str]) -> str:
    if not messages:
        return "Ready when you are!"

    sanitized = [
        cleaned for cleaned in (_sanitize(message) or "" for message in messages) if cleaned
    ]

    if not sanitized:
        return "Ready when you are!"

    bullets = [
        f"• {shorten(message, width=72, placeholder='…')}"
        for message in sanitized[:3]
    ]

    remaining = len(sanitized) - len(bullets)
    if remaining > 0:
        extra_word = "messages" if remaining > 1 else "message"
        bullets.append(f"• …and {remaining} more {extra_word}")

    return "\n".join(bullets) if bullets else "Ready when you are!"


def _resolve_icon(emoji: str) -> str | None:
    env_path = os.getenv(ICON_ENV_VAR)
    if env_path:
        path = Path(env_path).expanduser()
        if path.exists():
            return str(path)

    icon_name = EMOJI_ICON_FILES.get(emoji)
    if not icon_name:
        return None

    candidate = ICON_DIR / icon_name
    if candidate.exists():
        return str(candidate)

    return None


def _resolve_sound(raw_sound: str | None) -> str | None:
    if raw_sound is None:
        return "Boop"

    normalized = raw_sound.strip()
    if not normalized:
        return "Boop"

    lowered = normalized.lower()
    if lowered in SOUND_DISABLE_VALUES:
        return None
    if lowered == "boop":
        return "Boop"

    candidate_path = Path(normalized).expanduser()
    if candidate_path.exists() and candidate_path.is_file():
        return str(candidate_path)

    resolved = SYSTEM_SOUND_LOOKUP.get(candidate_path.stem.lower())
    if resolved is not None:
        return resolved

    print(f"Sound '{normalized}' not found; using Boop sound.", file=sys.stderr)
    return "Boop"


def build_notification(notification: dict[str, Any]) -> tuple[str, str, str, str | None] | None:
    notification_type = notification.get("type")

    if notification_type != "agent-turn-complete":
        print(f"not sending a push notification for: {notification_type}")
        return None

    assistant_message = _sanitize(notification.get("last-assistant-message"))
    title_emoji = _pick_emoji(assistant_message or "agent-turn-complete")
    title = f"{title_emoji} Codex Update"
    subtitle = assistant_message or "Agent turn complete"
    raw_messages = notification.get("input_messages", [])
    if isinstance(raw_messages, Sequence) and not isinstance(raw_messages, (str, bytes)):
        input_messages = [str(item) for item in raw_messages]
    elif raw_messages:
        input_messages = [str(raw_messages)]
    else:
        input_messages = []
    message = _format_message(input_messages)
    icon_path = _resolve_icon(title_emoji)
    return title, subtitle, message, icon_path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: notify.py <NOTIFICATION_JSON>")
        return 1

    try:
        notification = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        return 1

    content = build_notification(notification)
    if content is None:
        return 0

    title, subtitle, message, icon_path = content

    sound = _resolve_sound(os.getenv(SOUND_ENV_VAR))

    cmd = [
        "terminal-notifier",
        "-title",
        title,
        "-subtitle",
        subtitle,
        "-message",
        message,
        "-group",
        "codex",
        "-ignoreDnD",
        "-activate",
        "com.googlecode.iterm2",
        "-closeLabel",
        "Dismiss",
    ]

    if icon_path:
        cmd.extend(["-appIcon", icon_path])

    if sound:
        cmd.extend(["-sound", sound])

    subprocess.check_output(
        cmd
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
