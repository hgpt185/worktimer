#!/usr/bin/env python3
"""
Eye Rest Timer — macOS menu bar app
- Set a custom session timer (e.g. 6 hours)
- Every 20 min of active screen time, reminds you to look away for 20s
- Pauses when screen is locked/asleep, resumes on unlock/wake
"""

import rumps
import objc
from Foundation import NSDistributedNotificationCenter, NSObject
from AppKit import NSWorkspace, NSWorkspaceScreensDidSleepNotification, NSWorkspaceScreensDidWakeNotification
import subprocess


def send_notification(title, message):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}" sound name "Glass"'
    ], capture_output=True)


class ScreenStateObserver(NSObject):
    def init(self):
        self = objc.super(ScreenStateObserver, self).init()
        if self is None:
            return None
        self.on_lock = None
        self.on_unlock = None
        return self

    def screenLocked_(self, notification):
        if self.on_lock:
            self.on_lock()

    def screenUnlocked_(self, notification):
        if self.on_unlock:
            self.on_unlock()

    def screenSlept_(self, notification):
        if self.on_lock:
            self.on_lock()

    def screenWoke_(self, notification):
        if self.on_unlock:
            self.on_unlock()


class EyeRestTimerApp(rumps.App):
    def __init__(self):
        super().__init__("Respite", title="⏳ Start Timer")

        self.eye_rest_interval = 20 * 60  # 20 minutes
        self.eye_rest_remaining = self.eye_rest_interval
        self.eye_resting = False
        self.eye_rest_pause_remaining = 20

        self.session_total = 0
        self.session_remaining = 0
        self.session_active = False

        self.paused = False

        self.menu = [
            rumps.MenuItem("Start Timer...", callback=self.start_session),
            rumps.MenuItem("Pause", callback=self.toggle_pause),
            rumps.MenuItem("Stop Timer", callback=self.stop_session),
            None,
            rumps.MenuItem("Status: Idle", callback=None),
        ]

    def _setup_screen_observer(self):
        self.observer = ScreenStateObserver.alloc().init()
        self.observer.on_lock = self._on_screen_inactive
        self.observer.on_unlock = self._on_screen_active

        dnc = NSDistributedNotificationCenter.defaultCenter()
        dnc.addObserver_selector_name_object_(
            self.observer,
            objc.selector(self.observer.screenLocked_, signature=b"v@:@"),
            "com.apple.screenIsLocked",
            None
        )
        dnc.addObserver_selector_name_object_(
            self.observer,
            objc.selector(self.observer.screenUnlocked_, signature=b"v@:@"),
            "com.apple.screenIsUnlocked",
            None
        )

        ws = NSWorkspace.sharedWorkspace().notificationCenter()
        ws.addObserver_selector_name_object_(
            self.observer,
            objc.selector(self.observer.screenSlept_, signature=b"v@:@"),
            NSWorkspaceScreensDidSleepNotification,
            None
        )
        ws.addObserver_selector_name_object_(
            self.observer,
            objc.selector(self.observer.screenWoke_, signature=b"v@:@"),
            NSWorkspaceScreensDidWakeNotification,
            None
        )

    def _on_screen_inactive(self):
        self.paused = True
        self.menu["Status: Idle"].title = "Status: PAUSED (screen off)"

    def _on_screen_active(self):
        self.paused = False
        if self.session_active:
            self.menu["Status: Idle"].title = "Status: Running"
        else:
            self.menu["Status: Idle"].title = "Status: Idle"

    def start_session(self, _):
        window = rumps.Window(
            message="How long do you want to work?\nExamples: 360 (minutes), 6h, 1.5h, 90m",
            title="Set Session Timer",
            default_text="6h",
            ok="Start",
            cancel="Cancel",
            dimensions=(260, 24)
        )
        response = window.run()
        if not response.clicked:
            return

        text = response.text.strip().lower()
        minutes = self._parse_duration(text)
        if minutes is None or minutes <= 0:
            rumps.alert("Invalid input", "Enter a number like: 360, 6h, 1.5h, or 90m")
            return

        self.session_total = int(minutes * 60)
        self.session_remaining = self.session_total
        self.session_active = True
        self.paused = False
        self.eye_rest_remaining = self.eye_rest_interval
        self.eye_resting = False
        self.menu["Pause"].title = "Pause"
        self.menu["Status: Idle"].title = "Status: Running"

        hours = minutes / 60
        if hours >= 1:
            send_notification("Timer Started", f"{hours:.1g}h session started. Eye rest every 20 min.")
        else:
            send_notification("Timer Started", f"{int(minutes)}min session started. Eye rest every 20 min.")

    def _parse_duration(self, text):
        try:
            if text.endswith("h"):
                return float(text[:-1]) * 60
            elif text.endswith("m"):
                return float(text[:-1])
            else:
                return float(text)
        except ValueError:
            return None

    def toggle_pause(self, sender):
        if not self.session_active:
            return
        self.paused = not self.paused
        if self.paused:
            sender.title = "Resume"
            self.menu["Status: Idle"].title = "Status: PAUSED"
            self.title = "⏸ Paused"
        else:
            sender.title = "Pause"
            self.menu["Status: Idle"].title = "Status: Running"

    def stop_session(self, _):
        self.session_active = False
        self.session_remaining = 0
        self.eye_resting = False
        self.paused = False
        self.title = "⏳ Start Timer"
        self.menu["Pause"].title = "Pause"
        self.menu["Status: Idle"].title = "Status: Idle"

    @rumps.timer(1)
    def tick(self, _):
        if self.paused or not self.session_active:
            return

        # Session countdown
        self.session_remaining -= 1
        if self.session_remaining <= 0:
            self.session_active = False
            send_notification("Session Complete!", f"Your {self.session_total // 3600}h session is done. Take a break!")
            self.title = "⏳ Done!"
            self.menu["Status: Idle"].title = "Status: Idle"
            return

        # Eye rest logic
        if self.eye_resting:
            self.eye_rest_pause_remaining -= 1
            if self.eye_rest_pause_remaining <= 0:
                send_notification("Rest Over", "You can look back at the screen now.")
                self.eye_resting = False
                self.eye_rest_remaining = self.eye_rest_interval
        else:
            self.eye_rest_remaining -= 1
            if self.eye_rest_remaining <= 0:
                send_notification("Eye Rest", "Look at something 20 feet away for 20 seconds.")
                self.eye_resting = True
                self.eye_rest_pause_remaining = 20

        self._update_title()

    def _update_title(self):
        if self.paused:
            self.title = "⏸"
            return

        # Show session remaining time
        h, remainder = divmod(self.session_remaining, 3600)
        m, s = divmod(remainder, 60)

        if self.eye_resting:
            rest_part = f"REST {self.eye_rest_pause_remaining}s"
        else:
            rest_m, rest_s = divmod(self.eye_rest_remaining, 60)
            rest_part = f"{rest_m}:{rest_s:02d}"

        if h > 0:
            self.title = f"⏳ {h}:{m:02d}:{s:02d} | {rest_part}"
        else:
            self.title = f"⏳ {m}:{s:02d} | {rest_part}"


if __name__ == "__main__":
    app = EyeRestTimerApp()
    app._setup_screen_observer()
    app.run()
