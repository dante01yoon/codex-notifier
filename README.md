# codex-notifier

codex-notifier is a small helper for turning Codex CLI agent events into macOS notifications via `terminal-notifier`. It parses the JSON payload emitted by the CLI when an agent turn completes and presents a richer notification with emoji, icons, and optional sound.

## Requirements
- macOS with Python 3.10 or newer
- [`terminal-notifier`](https://github.com/julienXX/terminal-notifier) available on the `PATH` (installable with `brew install terminal-notifier`)
- Optional: custom icon files (PNG/ICNS) and audio files if you want to override the defaults

## Available scripts
- `codex_emoji_notify.py` – primary notifier that selects an emoji, formats the message, and supports custom icons and sounds.
- `codex_notify.py` – minimal legacy notifier kept for reference or fallback scenarios.

## Usage
1. Produce or capture the JSON payload from the Codex CLI. A sample payload is provided in `sample_notification.json`.
2. Invoke the notifier with the JSON blob as the only argument:
   ```bash
   python codex_emoji_notify.py "$(cat sample_notification.json)"
   ```
   The script validates the payload, builds a notification, and forwards it to `terminal-notifier`.
3. Hook the script into your Codex CLI configuration (for example by pointing the CLI's notification command to this script).

If the payload type is not `agent-turn-complete`, the script exits without sending a notification.

## Customisation
- Icon: set `CODEX_NOTIFIER_ICON` to an absolute path to a PNG/ICNS file. If unset, the script looks up a themed icon from the bundled `icons/` directory that matches the chosen emoji.
- Sound: set `CODEX_NOTIFIER_SOUND` to either a system sound name, a file path, or one of `none` / `silent` / `off` to disable audio. Missing sounds fall back to the macOS **Boop** sound with a warning.
- Emoji: the emoji is deterministically selected from a small palette based on the assistant's last message so the same message produces the same emoji.

## Development notes
- The script expects the JSON argument as a single string. If you stream JSON from another process make sure to quote or escape it so the shell passes it unchanged.
- `SOUND_SEARCH_PATHS` scans standard macOS sound folders (System, Library, and `~/Library/Sounds`). Drop custom alerts there to reference them by name.
- All external commands are run through `terminal-notifier`; make sure it is installed and accessible before wiring this into an automation.

## Troubleshooting
- **No notification appears**: confirm the payload contains `"type": "agent-turn-complete"` and that `terminal-notifier` is installed.
- **Sound falls back to Boop**: the provided sound name/path could not be resolved. Check the spelling or full path.
- **Icons missing**: verify the files in `icons/` exist or provide a custom icon path via `CODEX_NOTIFIER_ICON`.
