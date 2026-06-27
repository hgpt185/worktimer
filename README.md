# Respite

A minimal macOS menu bar app that keeps your eyes healthy during long work sessions.

Set a work timer. Every 20 minutes, Respite nudges you to look away for 20 seconds. When your screen locks or sleeps, timers pause automatically. When you're back, they resume — no lost time.

## Demo

<video src="assets/respite-demo.mp4" controls width="720"></video>

---

## Install

**One-liner (recommended):**

```bash
curl -fsSL https://raw.githubusercontent.com/hgpt185/worktimer/main/install.sh | bash
```

This downloads the DMG, copies `Respite.app` to `/Applications`, and launches it.

**Manual:**

1. Download `Respite.dmg` from [Releases](https://github.com/hgpt185/worktimer)
2. Open the DMG and drag `Respite.app` to `/Applications`
3. Launch from Spotlight or `open /Applications/Respite.app`

---

## Usage

| Action | How |
|--------|-----|
| Start a session | Click ⏳ in menu bar → **Start Timer...** → enter duration (`6h`, `90m`, `45`) |
| Pause/Resume | Click ⏳ → **Pause** / **Resume** |
| Stop | Click ⏳ → **Stop Timer** |

**Menu bar display:**

```
⏳ 5:42:01 | 18:30
│          │
│          └── Next eye-rest break in 18min 30s
└── Session time remaining
```

**Notifications:**
- "Look at something 20 feet away for 20 seconds" — every 20 min
- "You can look back at the screen now" — after 20s rest
- "Session complete!" — when your timer hits zero

---

## How It Works

- Follows the **20-20-20 rule**: every 20 minutes, look at something 20 feet away for 20 seconds
- Listens to `com.apple.screenIsLocked` / `screenIsUnlocked` and `NSWorkspaceScreensDidSleep/Wake`
- All countdowns freeze when your Mac is locked or asleep — only active screen time counts
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

The built app is at `dist/Respite.app`.

**Run without building:**

```bash
source .venv/bin/activate
python eye_rest_timer.py
```

---

## Auto-start at Login

System Settings → General → Login Items → add `/Applications/Respite.app`

---

## Tech

- Python + [rumps](https://github.com/jaredks/rumps) (menu bar framework)
- [pyobjc](https://github.com/ronaldoussoren/pyobjc) (screen lock/wake detection)
- [py2app](https://py2app.readthedocs.io/) (standalone .app packaging)

---

## License

MIT
