# Face Lock — AI Biometric Folder Guardian

A sleek Windows desktop application that locks and unlocks folders using **webcam face recognition** (LBPH neural model) combined with an **eye-blink liveness check** (to prevent photo/spoof bypasses).

![App Icon](app_icon.png)

---

## Features

- 👤 **Biometric Enrollment**: Captures face samples via webcam and trains a local model (`facelock_data/face_model.yml`).
- 🔒 **Folder Locking**: Renames folders into system-hidden attributes so they disappear from normal File Explorer browsing.
- 👁️ **Eye-Blink Liveness**: Verification requires both face match and active eye-blink detection within a live webcam window.
- 🎨 **Futuristic Cyber HUD**: Dark space UI with target corners, live liveness feedback, and activity logs.

---

## Quick Start (Run from Source)

```bash
pip install -r requirements.txt
python face_lock.py
```

---

## Build Standalone Windows Executable (.exe)

Run the included build script in Command Prompt or PowerShell:

```cmd
build_exe.bat
```

The output executable will be created at `dist\FaceLock.exe`.

---

## Uploading to GitHub

### 1. Push Source Code to GitHub (< 1 MB)
The included `.gitignore` keeps large build folders (`dist/`, `build/`) out of Git, keeping your repository lightweight.

```bash
git init
git add .
git commit -m "Initial commit of Face Lock"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/FaceLock.git
git push -u origin main
```

### 2. Distribute the Executable via GitHub Releases
To share the standalone executable with users without committing heavy binaries into your repo:
1. Go to your GitHub repository page.
2. Click **Releases** -> **Draft a new release**.
3. Create a version tag (e.g. `v1.0.0`).
4. Drag and drop `dist/FaceLock.exe` or `FaceLock_v1.0_Windows.zip` under **Attach binaries by dropping them here**.
5. Click **Publish release**.

---

## Tech Stack & Dependencies

- Python 3.9+
- OpenCV (`opencv-contrib-python`) - Face & Eye Haar Cascades + LBPH Recognizer
- NumPy - Matrix operations
- Pillow - Asset handling
- PyInstaller - Standalone binary compilation
