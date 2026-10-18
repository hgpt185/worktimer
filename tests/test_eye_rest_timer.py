"""Deterministic timer tests; macOS UI and notification bridges are stubbed."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import PropertyMock, patch


class MenuItem:
    def __init__(self, title, callback=None):
        self.title = title


class App:
    def __init__(self, name, title):
        self.title = title

    @property
    def menu(self):
        return self._menu

    @menu.setter
    def menu(self, items):
        self._menu = {item.title: item for item in items if item is not None}


class Timer:
    instances = []

    def __init__(self, callback, interval):
        self.callback, self.interval, self.active = callback, interval, False
        self.instances.append(self)

    @classmethod
    def timerWithTimeInterval_repeats_block_(cls, interval, repeats, callback):
        assert repeats is False
        return cls(callback, interval)

    @classmethod
    def currentRunLoop(cls):
        return cls

    @classmethod
    def addTimer_forMode_(cls, timer, mode):
        timer.start()

    def start(self):
        self.active = True

    def invalidate(self):
        self.active = False


sys.modules['rumps'] = types.SimpleNamespace(App=App, MenuItem=MenuItem, Timer=Timer)
sys.modules['objc'] = types.SimpleNamespace()
sys.modules['Foundation'] = types.SimpleNamespace(NSDistributedNotificationCenter=object, NSObject=object, NSTimer=Timer, NSRunLoop=Timer, NSDefaultRunLoopMode='default')
sys.modules['AppKit'] = types.SimpleNamespace(NSWorkspace=object, NSWorkspaceScreensDidSleepNotification='sleep', NSWorkspaceScreensDidWakeNotification='wake')
spec = importlib.util.spec_from_file_location('eye_rest_timer', Path(__file__).resolve().parents[1] / 'eye_rest_timer.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TimerTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        Timer.instances.clear()
        self.clock = patch.object(module.time, 'monotonic', side_effect=lambda: self.now)
        self.clock.start()
        self.notifications = patch.object(module, 'send_notification').start()
        self.app = module.EyeRestTimerApp()
        self.addCleanup(patch.stopall)

    def start(self, duration=7200, work=1200):
        a = self.app
        a._cancel_timer()
        a._last_active_time = None
        a.session_active = True
        a.session_total = a.session_remaining = duration
        a.eye_rest_interval = a.eye_rest_remaining = work
        a.eye_resting = a.paused = False
        a._refresh()

    def advance(self, seconds):
        self.now += seconds
        self.app.tick(self.app._timer)

    def assertSingle(self, count=1):
        self.assertEqual(sum(t.active for t in Timer.instances), count)

    def test_rounding_and_thresholds(self):
        for remaining, expected in [(61,'2m'), (60,'1m'), (31,'1m'), (30,'30s'), (1,'1s')]:
            with self.subTest(remaining=remaining):
                self.start(remaining, remaining)
                self.assertEqual(self.app.title, f'⏳ {2 if remaining == 61 else 1}m | {expected}')
        self.start(20521)
        self.assertTrue(self.app.title.startswith('⏳ 5h 43m'))

    def test_full_rest_and_repeat(self):
        self.start(work=31)
        self.advance(1)
        self.assertTrue(self.app.title.endswith('30s'))
        for _ in range(30):
            self.advance(1)
        self.assertTrue(self.app.title.endswith('REST 20s'))
        for remaining in range(19, 0, -1):
            self.advance(1)
            self.assertTrue(self.app.title.endswith(f'REST {remaining}s'))
        self.advance(1)
        self.assertFalse(self.app.eye_resting)
        self.assertEqual(self.app.eye_rest_remaining, 31)
        self.advance(31)
        self.assertTrue(self.app.eye_resting)
        self.assertEqual([c.args[0] for c in self.notifications.call_args_list], ['Eye Rest','Rest Over','Eye Rest'])
        self.assertSingle()

    def test_delayed_callback_and_fractional_pause(self):
        self.start()
        self.now = 12.75
        self.app.toggle_pause(self.app.menu['Pause'])
        self.assertEqual(self.app.session_remaining, 7187.25)
        self.assertSingle(0)
        self.now += 900
        self.app.toggle_pause(self.app.menu['Pause'])
        self.advance(75.5)
        self.assertEqual(self.app.session_remaining, 7111.75)
        self.assertSingle()

    def test_manual_pause_and_overlapping_screen_states(self):
        self.start()
        self.now = 5
        self.app._on_screen_inactive('locked')
        self.app._on_screen_inactive('asleep')
        self.app.toggle_pause(self.app.menu['Pause'])
        self.now = 100
        self.app._on_screen_active('asleep')
        self.app._on_screen_active('locked')
        self.assertTrue(self.app.paused)
        self.assertEqual(self.app.session_remaining, 7195)
        self.assertSingle(0)
        self.app.toggle_pause(self.app.menu['Pause'])
        self.advance(3)
        self.assertEqual(self.app.session_remaining, 7192)
        self.app._on_screen_inactive('locked')
        self.app._on_screen_inactive('asleep')
        self.app._on_screen_active('asleep')
        self.assertSingle(0)
        self.app._on_screen_active('locked')
        self.assertSingle()

    def test_completion_work_rest_and_coincident(self):
        for duration in [10, 31, 40, 51]:
            with self.subTest(duration=duration):
                self.notifications.reset_mock()
                self.start(duration,31)
                if duration > 31:
                    self.advance(31)
                self.advance(self.app.session_remaining)
                self.assertFalse(self.app.session_active)
                self.assertEqual(self.app.title, '⏳ Done!')
                self.assertEqual(self.notifications.call_args.args[0], 'Session Complete!')
                self.assertSingle(0)
                if duration == 31:
                    self.assertEqual(self.notifications.call_count, 1)

    def test_idle_restart_stop_and_stale_callbacks(self):
        self.assertSingle(0)
        self.start()
        old = self.app._timer
        self.start(3600)
        self.app.tick(old)
        self.assertEqual(self.app.session_remaining,3600)
        self.assertSingle()
        current = self.app._timer
        self.app.stop_session(None)
        self.app.tick(current)
        self.app._on_screen_active('locked')
        self.assertSingle(0)
        self.assertEqual(self.app.title,'⏳ Start Timer')

    def test_start_restart_and_screen_inactive(self):
        response = types.SimpleNamespace(clicked=True, text='6h')
        window = types.SimpleNamespace(run=lambda: response)
        with patch.object(module.rumps, 'Window', create=True, return_value=window):
            self.app.start_session(None)
            self.assertEqual(self.app.title, '⏳ 6h 00m | 20m')
            old = self.app._timer
            self.app.eye_resting = True
            self.app.eye_rest_pause_remaining = 3
            self.app.start_session(None)
            self.app.tick(old)
            self.assertFalse(self.app.eye_resting)
            self.assertEqual(self.app.eye_rest_pause_remaining, 20)
            self.assertSingle()
            self.app._on_screen_inactive('locked')
            self.app.start_session(None)
            self.assertSingle(0)
            self.app._on_screen_active('locked')
            self.assertSingle()

    def test_rest_pause_and_delayed_phase_transitions(self):
        self.start(work=31)
        self.advance(35.5)
        self.assertEqual(self.app.eye_rest_pause_remaining, 15.5)
        self.app.toggle_pause(self.app.menu['Pause'])
        self.now += 500
        self.app.toggle_pause(self.app.menu['Pause'])
        self.assertEqual(self.app.eye_rest_pause_remaining, 15.5)
        self.advance(16)
        self.assertFalse(self.app.eye_resting)
        self.assertEqual(self.app.eye_rest_remaining, 30.5)
        self.assertEqual(self.app.session_remaining, 7148.5)

    def test_duplicate_wake_refreshes_elapsed_time(self):
        self.start()
        self.now = 61
        self.app._on_screen_active('asleep')
        self.assertEqual(self.app.session_remaining, 7139)
        self.assertSingle()

    def test_callback_savings(self):
        self.start(21600)
        count = 0
        while not self.app.eye_resting:
            self.advance(self.app._timer.interval)
            count += 1
            self.assertSingle()
        self.assertEqual(count, 50)
        print(f'20-minute work interval: {count} callbacks vs 1200 previously')

    def test_title_only_assigned_when_changed(self):
        self.start()
        with patch.object(module.EyeRestTimerApp, 'title', create=True, new_callable=PropertyMock) as title:
            title.return_value = 'unchanged'
            self.app._set_title('unchanged')
            self.assertEqual(title.call_count,1)


if __name__ == '__main__':
    unittest.main()
