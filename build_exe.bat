@echo off
REM Build Face Lock as a single Windows .exe with icon and optimizations
REM Run this on a WINDOWS machine, inside this folder, after installing requirements.

echo Installing dependencies...
pip install -r requirements.txt

echo Copying haar cascade files from installed OpenCV package...
python -c "import cv2, shutil, os; d=cv2.data.haarcascades; shutil.copy(os.path.join(d,'haarcascade_frontalface_default.xml'), '.'); shutil.copy(os.path.join(d,'haarcascade_eye.xml'), '.')"

echo Building optimized exe with PyInstaller...
python -m PyInstaller --onefile --windowed --name FaceLock ^
  --icon=app_icon.ico ^
  --add-data "app_icon.ico;." ^
  --add-data "app_icon.png;." ^
  --add-data "haarcascade_frontalface_default.xml;." ^
  --add-data "haarcascade_eye.xml;." ^
  --exclude-module=matplotlib ^
  --exclude-module=scipy ^
  --exclude-module=unittest ^
  --exclude-module=pydoc ^
  --exclude-module=test ^
  --exclude-module=sqlite3 ^
  face_lock.py

echo.
echo Done. Your exe is in the "dist" folder: dist\FaceLock.exe
pause
