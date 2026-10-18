"""
Build a standalone .app bundle with py2app.
Run: python setup.py py2app
"""
from setuptools import setup

APP = ['eye_rest_timer.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': 'Work Timer',
        'CFBundleDisplayName': 'Work Timer',
        'CFBundleIdentifier': 'com.hgpt185.worktimer',
        'CFBundleShortVersionString': '1.0.1',
        'LSUIElement': True,  # Hide from Dock (menu bar only)
        'NSAppleEventsUsageDescription': 'Required for notifications.',
    },
    'packages': ['rumps', 'objc', 'Foundation', 'AppKit'],
}

setup(
    name='Work Timer',
    version='1.0.1',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
