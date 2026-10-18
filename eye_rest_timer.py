#!/usr/bin/env python3
"""
Eye Rest Timer — macOS menu bar app
- Set a custom session timer (e.g. 6 hours)
- Every 20 min of active screen time, reminds you to look away for 20s
- Pauses when screen is locked/asleep, resumes on unlock/wake
"""

import rumps
import objc
from Foundation import (
    NSDistributedNotificationCenter, NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode,
)
from AppKit import NSWorkspace, NSWorkspaceScreensDidSleepNotification, NSWorkspaceScreensDidWakeNotification
import subprocess
import math
import time


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
            self.on_lock("locked")

    def screenUnlocked_(self, notification):
        if self.on_unlock:
            self.on_unlock("locked")

    def screenSlept_(self, notification):
        if self.on_lock:
            self.on_lock("asleep")

    def screenWoke_(self, notification):
        if self.on_unlock:
            self.on_unlock("asleep")


class EyeRestTimerApp(rumps.App):
    def __init__(self):
        super().__init__("Work Timer", title="⏳ Start Timer")

        self.eye_rest_interval = 20 * 60  # 20 minutes
        self.eye_rest_remaining = self.eye_rest_interval
        self.eye_resting = False
        self.eye_rest_pause_remaining = 20

        self.session_total = 0
        self.session_remaining = 0
        self.session_active = False

        self.paused = False  # Manual pause, independent of screen state.
        self._inactive_reasons = set()
        self._last_active_time = None
        self._timer = None

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

    def _on_screen_inactive(self, reason="screen"):
        self._advance()
        self._inactive_reasons.add(reason)
        self._refresh()

    def _on_screen_active(self, reason="screen"):
        self._advance()
        self._inactive_reasons.discard(reason)
        self._refresh()

    def _running(self):
        return self.session_active and not self.paused and not self._inactive_reasons

    def _cancel_timer(self):
        if self._timer is not None:
            self._timer.invalidate()
            self._timer = None

    def _set_title(self, title):
        if self.title != title:
            self.title = title

    def _refresh(self):
        self._cancel_timer()
        self.menu["Pause"].title = "Resume" if self.paused else "Pause"
        if not self.session_active:
            self._last_active_time = None
            self.menu["Status: Idle"].title = "Status: Idle"
            return
        if not self._running():
            self._last_active_time = None
            status = "PAUSED" if self.paused else "PAUSED (screen off)"
            self.menu["Status: Idle"].title = f"Status: {status}"
            self._set_title("⏸ Paused")
            return
        self.menu["Status: Idle"].title = "Status: Running"
        if self._last_active_time is None:
            self._last_active_time = time.monotonic()
        self._update_title()
        self._schedule()

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
        if minutes is None or not math.isfinite(minutes) or minutes <= 0:
            rumps.alert("Invalid input", "Enter a number like: 360, 6h, 1.5h, or 90m")
            return

        self._cancel_timer()
        self._last_active_time = None
        self.session_total = max(1, int(minutes * 60))
        self.session_remaining = self.session_total
        self.session_active = True
        self.paused = False
        self.eye_rest_remaining = self.eye_rest_interval
        self.eye_resting = False
        self.eye_rest_pause_remaining = 20
        self._refresh()

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
        self._advance()
        if self.session_active:
            self.paused = not self.paused
        self._refresh()

    def stop_session(self, _):
        self._cancel_timer()
        self._last_active_time = None
        self.session_active = False
        self.session_remaining = 0
        self.eye_resting = False
        self.paused = False
        self._set_title("⏳ Start Timer")
        self._refresh()

    def _advance(self):
        if not self._running() or self._last_active_time is None:
            return
        now = time.monotonic()
        elapsed = max(0, now - self._last_active_time)
        self._last_active_time = now
        self.session_remaining = max(0, self.session_remaining - elapsed)
        # Session completion wins, including when a callback was delayed.
        if self.session_remaining <= 0:
            self.session_active = False
            self.eye_resting = False
            self.paused = False
            self._cancel_timer()
            self._last_active_time = None
            self._set_title("⏳ Done!")
            send_notification("Session Complete!", f"Your {self.session_total // 3600}h session is done. Take a break!")
            return

        while elapsed > 0:
            remaining = self.eye_rest_pause_remaining if self.eye_resting else self.eye_rest_remaining
            consumed = min(elapsed, remaining)
            elapsed -= consumed
            remaining -= consumed
            if self.eye_resting:
                self.eye_rest_pause_remaining = remaining
            else:
                self.eye_rest_remaining = remaining
            if remaining > 0:
                break
            if self.eye_resting:
                self.eye_resting = False
                self.eye_rest_remaining = self.eye_rest_interval
                send_notification("Rest Over", "You can look back at the screen now.")
            else:
                self.eye_resting = True
                self.eye_rest_pause_remaining = 20
                send_notification("Eye Rest", "Look at something 20 feet away for 20 seconds.")

    def tick(self, timer):
        # Ignore callbacks already queued before a pause, stop, or restart.
        if timer is not self._timer:
            return
        self._cancel_timer()
        self._advance()
        self._refresh()

    @staticmethod
    def _until_display_change(remaining, unit):
        return remaining - (math.ceil(remaining / unit) - 1) * unit

    def _schedule(self):
        delays = [self.session_remaining,
                  self._until_display_change(self.session_remaining, 60)]
        if self.eye_resting:
            delays.append(self._until_display_change(self.eye_rest_pause_remaining, 1))
        else:
            remaining = self.eye_rest_remaining
            if remaining > 30:
                delays.extend([remaining - 30, self._until_display_change(remaining, 60)])
            else:
                delays.append(self._until_display_change(remaining, 1))
        self._timer = NSTimer.timerWithTimeInterval_repeats_block_(
            max(0.001, min(delays)), False, lambda timer: self.tick(timer)
        )
        NSRunLoop.currentRunLoop().addTimer_forMode_(self._timer, NSDefaultRunLoopMode)

    def _update_title(self):
        minutes = math.ceil(self.session_remaining / 60)
        h, m = divmod(minutes, 60)
        session_part = f"{h}h {m:02d}m" if h else f"{m}m"
        if self.eye_resting:
            rest_part = f"REST {math.ceil(self.eye_rest_pause_remaining)}s"
        elif self.eye_rest_remaining <= 30:
            rest_part = f"{math.ceil(self.eye_rest_remaining)}s"
        else:
            rest_part = f"{math.ceil(self.eye_rest_remaining / 60)}m"
        self._set_title(f"⏳ {session_part} | {rest_part}")


if __name__ == "__main__":
    app = EyeRestTimerApp()
    app._setup_screen_observer()
    app.run()
