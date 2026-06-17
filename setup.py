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
        'CFBundleName': 'Respite',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Hide from Dock (menu bar only)
        'NSAppleEventsUsageDescription': 'Required for notifications.',
    },
    'packages': ['rumps', 'objc', 'Foundation', 'AppKit'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
