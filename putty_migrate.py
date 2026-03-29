#!/usr/bin/env python3
"""
PuTTY Migration Tools - Entry Point

Entry point for PyInstaller builds and direct execution.
For module execution use: python -m tui

This file exists to provide a clean entry point outside the tui package,
which helps PyInstaller maintain the correct package context and prevents
relative import errors.
"""
import sys
from tui.__main__ import main

if __name__ == '__main__':
    sys.exit(main())
