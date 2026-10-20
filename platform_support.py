"""Desktop integration without OS-specific calls in the HTTP handlers."""
import os
import subprocess
import sys


def open_folder(folder):
    path = str(folder.resolve())
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])
