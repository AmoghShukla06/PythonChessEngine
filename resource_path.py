"""
Resource path helper for PyInstaller compatibility.
When running as a bundled executable, resources are extracted to a
temporary directory (sys._MEIPASS). This module provides a helper
to resolve the correct path regardless of how the app is launched.
"""

import os
import sys


def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
