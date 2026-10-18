# Work Timer

A minimal macOS menu bar app that keeps your eyes healthy during long work sessions.

Set a work timer. Every 20 minutes, Work Timer nudges you to look away for 20 seconds. When your screen locks or sleeps, timers pause automatically. When you're back, they resume — no lost time.

## Demo

[![Work Timer demo](assets/work-timer-demo.gif)](assets/work-timer-demo.mp4)

Click the preview to watch the full-resolution video.

---

## Install

**One-liner (recommended):**

```bash
curl -fsSL https://raw.githubusercontent.com/hgpt185/worktimer/main/install.sh | bash
```

This downloads the DMG, copies `Work Timer.app` to `/Applications`, and launches it.

**Manual:**

1. Download `Work Timer.dmg` from [the repository](https://github.com/hgpt185/worktimer/blob/main/Work%20Timer.dmg)
2. Open the DMG and drag `Work Timer.app` to `/Applications`
3. Launch from Spotlight or `open "/Applications/Work Timer.app"`

---

## Usage

| Action | How |
|--------|-----|
| Start a session | Click ⏳ in menu bar → **Start Timer...** → enter duration (`6h`, `90m`, `45`) |
| Pause/Resume | Click ⏳ → **Pause** / **Resume** |
| Stop | Click ⏳ → **Stop Timer** |

**Menu bar display:**

```
⏳ 5h 42m | 18m
⏳ 42m | 30s
⏳ 42m | REST 20s
```

Session and break minutes round up. The break countdown shows seconds for the final 30 seconds, then `REST 20s` through `REST 1s`. Session time continues counting during rest.

**Notifications:**
- "Look at something 20 feet away for 20 seconds" — every 20 min
- "You can look back at the screen now" — after 20s rest
- "Session complete!" — when your timer hits zero

---

## How It Works

- Follows the **20-20-20 rule**: every 20 minutes, look at something 20 feet away for 20 seconds
- Listens to `com.apple.screenIsLocked` / `screenIsUnlocked` and `NSWorkspaceScreensDidSleep/Wake`
- All countdowns freeze when your Mac is locked or asleep — only active screen time counts
- Manual pause stays paused through lock/unlock and sleep/wake
- Uses monotonic elapsed time and schedules callbacks only for the next display change or timer event; no callbacks while idle or paused
- Updates the menu bar title only when its text changes
- Lives in the menu bar only (no Dock icon)
- Native macOS notifications with sound

---

## Build from Source

Requires Python 3.9+ and macOS.

```bash
git clone https://github.com/hgpt185/worktimer.git
cd worktimer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt py2app
python setup.py py2app
```

The built app is at `dist/Work Timer.app`.

**Run without building:**

```bash
source .venv/bin/activate
python eye_rest_timer.py
```

**Run timer logic tests (no macOS UI dependencies required):**

```bash
python3 -m unittest discover -s tests -v
```

The tests use a simulated monotonic clock. Native notifications, screen events, and Activity Monitor energy readings require manual verification on macOS.

---

## Auto-start at Login

System Settings → General → Login Items → add `/Applications/Work Timer.app`

---

## Tech

- Python + [rumps](https://github.com/jaredks/rumps) (menu bar framework)
- [pyobjc](https://github.com/ronaldoussoren/pyobjc) (screen lock/wake detection)
- [py2app](https://py2app.readthedocs.io/) (standalone .app packaging)

---

## License

MIT
