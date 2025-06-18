import sys
import os

# Tambahkan path project ke sys.path
path = '/home/yourusername/Perpustakaan'  # Ganti 'yourusername' dengan username PythonAnywhere Anda
if path not in sys.path:
    sys.path.append(path)

from app import app as application

if __name__ == "__main__":
    application.run()