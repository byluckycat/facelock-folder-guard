"""
Face Lock - Folder Guardian
----------------------------
Locks/unlocks a folder using webcam face recognition + eye-blink liveness
detection (to prevent unlocking with a photo of your face).

Sleek Cyber-Dark UI themed with custom app icon and tech HUD liveness visuals.
"""

import cv2
import numpy as np
import os
import sys
import json
import time
import random
import string
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

# ---------------------------------------------------------------------------
# Paths (work both as a plain script and as a frozen PyInstaller .exe)
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(APP_DIR, "facelock_data")
os.makedirs(DATA_DIR, exist_ok=True)

MODEL_PATH = os.path.join(DATA_DIR, "face_model.yml")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
SAMPLES_DIR = os.path.join(DATA_DIR, "samples")


def resource_path(filename):
    """Find a bundled resource whether running as .py or frozen .exe."""
    if hasattr(sys, "_MEIPASS"):
        bundled = os.path.join(sys._MEIPASS, filename)
        if os.path.exists(bundled):
            return bundled
    local = os.path.join(APP_DIR, filename)
    if os.path.exists(local):
        return local
    # fall back to the cascade files shipped inside opencv itself
    return os.path.join(cv2.data.haarcascades, filename)


FACE_CASCADE = cv2.CascadeClassifier(resource_path("haarcascade_frontalface_default.xml"))
EYE_CASCADE = cv2.CascadeClassifier(resource_path("haarcascade_eye.xml"))


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {"enrolled": False, "locked_folders": {}}


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def draw_tech_corners(img, x, y, w, h, color=(255, 210, 0), thickness=2, length=25):
    """Draw futuristic HUD corner brackets around detected face."""
    # Top-Left
    cv2.line(img, (x, y), (x + length, y), color, thickness)
    cv2.line(img, (x, y), (x, y + length), color, thickness)
    # Top-Right
    cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
    cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
    # Bottom-Left
    cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
    cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
    # Bottom-Right
    cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)


# ---------------------------------------------------------------------------
# GUI application
# ---------------------------------------------------------------------------
class FaceLockApp:
    def __init__(self, root):
        self.root = root
        root.title("Face Lock - Biometric Folder Guardian")
        root.geometry("540x620")
        root.configure(bg="#0B0E14")
        root.resizable(False, False)

        # Set Window Icon
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
            except Exception:
                pass

        self.cfg = load_config()

        # Custom Styling Colors
        self.BG_MAIN = "#0B0E14"
        self.BG_CARD = "#141C2B"
        self.BORDER_COLOR = "#22304A"
        self.TEXT_PRIMARY = "#F8FAFC"
        self.TEXT_SECONDARY = "#94A3B8"
        self.ACCENT_CYAN = "#00D2FF"

        # -------------------------------------------------------------------
        # Header Section with App Banner / Icon
        # -------------------------------------------------------------------
        header_frame = tk.Frame(root, bg=self.BG_CARD, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        header_frame.pack(fill="x", padx=16, pady=(16, 10))

        # Try loading PNG icon for header badge
        img_png_path = resource_path("app_icon.png")
        if not os.path.exists(img_png_path) and os.path.exists(resource_path("app_bg.jpg")):
            img_png_path = resource_path("app_bg.jpg")

        if os.path.exists(img_png_path):
            try:
                pil_img = Image.open(img_png_path).resize((70, 70), Image.Resampling.LANCZOS)
                self.header_img = ImageTk.PhotoImage(pil_img)
                icon_lbl = tk.Label(header_frame, image=self.header_img, bg=self.BG_CARD)
                icon_lbl.pack(side="left", padx=15, pady=12)
            except Exception:
                pass

        title_box = tk.Frame(header_frame, bg=self.BG_CARD)
        title_box.pack(side="left", fill="both", expand=True, pady=12)

        tk.Label(
            title_box,
            text="FACE LOCK",
            font=("Segoe UI", 18, "bold"),
            fg=self.ACCENT_CYAN,
            bg=self.BG_CARD,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            title_box,
            text="AI Biometric Folder Guardian & Liveness Vault",
            font=("Segoe UI", 9),
            fg=self.TEXT_SECONDARY,
            bg=self.BG_CARD,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # -------------------------------------------------------------------
        # Status Card
        # -------------------------------------------------------------------
        status_card = tk.Frame(root, bg=self.BG_CARD, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        status_card.pack(fill="x", padx=16, pady=6)

        self.status = tk.Label(
            status_card,
            text="",
            font=("Segoe UI", 10, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.BG_CARD,
            pady=10,
        )
        self.status.pack()

        # -------------------------------------------------------------------
        # Action Buttons Section
        # -------------------------------------------------------------------
        btn_frame = tk.Frame(root, bg=self.BG_MAIN)
        btn_frame.pack(fill="x", padx=16, pady=10)

        # Style button helper
        def create_cyber_button(parent, text, command, bg_color, hover_color):
            btn = tk.Button(
                parent,
                text=text,
                font=("Segoe UI", 10, "bold"),
                fg="#FFFFFF",
                bg=bg_color,
                activebackground=hover_color,
                activeforeground="#FFFFFF",
                bd=0,
                cursor="hand2",
                pady=10,
                command=command,
            )
            btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
            btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))
            return btn

        b1 = create_cyber_button(btn_frame, "1.  Enroll My Face", self.enroll, "#0284C7", "#0369A1")
        b1.pack(fill="x", pady=5)

        b2 = create_cyber_button(btn_frame, "2.  Lock a Folder", self.lock_folder, "#334155", "#475569")
        b2.pack(fill="x", pady=5)

        b3 = create_cyber_button(btn_frame, "3.  Unlock a Folder", self.unlock_folder, "#0D9488", "#0F766E")
        b3.pack(fill="x", pady=5)

        # -------------------------------------------------------------------
        # Terminal Console / Activity Log Box
        # -------------------------------------------------------------------
        log_frame = tk.Frame(root, bg=self.BG_CARD, highlightbackground=self.BORDER_COLOR, highlightthickness=1)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        tk.Label(
            log_frame,
            text="ACTIVITY LOG",
            font=("Segoe UI", 8, "bold"),
            fg=self.TEXT_SECONDARY,
            bg=self.BG_CARD,
            anchor="w",
            padx=10,
            pady=6,
        ).pack(fill="x")

        self.log = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=("Consolas", 9),
            bg="#070A10",
            fg="#00E5FF",
            insertbackground="#00E5FF",
            selectbackground="#1E293B",
            selectforeground="#FFFFFF",
            bd=0,
            relief="flat",
            state="disabled",
        )
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.refresh_status()

    # -- helpers -----------------------------------------------------------
    def refresh_status(self):
        self.cfg = load_config()
        enrolled = "Yes" if self.cfg.get("enrolled") else "No"
        locked_count = len(self.cfg.get("locked_folders", {}))
        self.status.config(
            text=f"Biometric Enrolled:  [{enrolled}]       |       Vault Locked Folders:  [{locked_count}]"
        )

    def logmsg(self, msg):
        self.log.config(state="normal")
        tstr = time.strftime("[%H:%M:%S] ")
        self.log.insert(tk.END, tstr + msg + "\n")
        self.log.see(tk.END)
        self.log.config(state="disabled")

    # -- enrollment ----------------------------------------------------------
    def enroll(self):
        threading.Thread(target=self._enroll_thread, daemon=True).start()

    def _enroll_thread(self):
        self.logmsg("Starting enrollment scanner. Look into the camera...")
        os.makedirs(SAMPLES_DIR, exist_ok=True)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.logmsg("ERROR: could not open webcam device.")
            return

        count = 0
        target = 30
        while count < target:
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                face_img = cv2.resize(gray[y : y + h, x : x + w], (200, 200))
                cv2.imwrite(os.path.join(SAMPLES_DIR, f"{count}.png"), face_img)
                count += 1
                draw_tech_corners(frame, x, y, w, h, color=(255, 210, 0), thickness=2, length=25)
                break

            # HUD Overlay text
            cv2.putText(
                frame,
                f"FACELOCK SCANNING: {count}/{target}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 210, 0),
                2,
            )
            cv2.imshow("Face Lock Enrollment - Press Q to Cancel", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            time.sleep(0.04)

        cap.release()
        cv2.destroyAllWindows()

        if count < 10:
            self.logmsg("Enrollment cancelled or insufficient face samples.")
            return

        self.logmsg("Training biometric LBPH neural model...")
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        images, labels = [], []
        for fname in os.listdir(SAMPLES_DIR):
            img = cv2.imread(os.path.join(SAMPLES_DIR, fname), cv2.IMREAD_GRAYSCALE)
            images.append(img)
            labels.append(1)
        recognizer.train(images, np.array(labels))
        recognizer.save(MODEL_PATH)

        self.cfg["enrolled"] = True
        save_config(self.cfg)
        self.logmsg("Biometric enrollment successfully completed and saved.")
        self.refresh_status()

    # -- locking -------------------------------------------------------------
    def lock_folder(self):
        if not self.cfg.get("enrolled"):
            messagebox.showwarning("Not Enrolled", "Please enroll your face biometric profile first.")
            return
        folder = filedialog.askdirectory(title="Select Folder to Secure & Lock")
        if not folder:
            return
        folder = os.path.abspath(folder)
        parent = os.path.dirname(folder)
        token = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        hidden_name = f".flk_{token}"
        hidden_path = os.path.join(parent, hidden_name)

        try:
            os.rename(folder, hidden_path)
            if os.name == "nt":
                os.system(f'attrib +h +s "{hidden_path}"')
        except Exception as e:
            messagebox.showerror("Lock Failed", f"Could not lock folder: {e}")
            return

        self.cfg.setdefault("locked_folders", {})[token] = {
            "original_path": folder,
            "hidden_path": hidden_path,
        }
        save_config(self.cfg)
        self.logmsg(f"SECURED & HIDDEN: {folder}")
        self.refresh_status()
        messagebox.showinfo(
            "Folder Locked",
            f"Folder has been secured and hidden:\n{folder}\n\nUse 'Unlock a Folder' with face + blink verification to restore.",
        )

    # -- unlocking -----------------------------------------------------------
    def unlock_folder(self):
        if not self.cfg.get("enrolled"):
            messagebox.showwarning("Not Enrolled", "Please enroll your face biometric profile first.")
            return
        locked = self.cfg.get("locked_folders", {})
        if not locked:
            messagebox.showinfo("Vault Empty", "There are currently no locked folders in the vault.")
            return

        options = {v["original_path"]: k for k, v in locked.items()}
        pick_win = tk.Toplevel(self.root)
        pick_win.title("Select Vault Folder to Unlock")
        pick_win.geometry("460x280")
        pick_win.configure(bg="#0B0E14")
        pick_win.resizable(False, False)

        tk.Label(
            pick_win,
            text="Select Locked Folder to Restore:",
            font=("Segoe UI", 10, "bold"),
            fg="#F8FAFC",
            bg="#0B0E14",
        ).pack(pady=(16, 8))

        listbox = tk.Listbox(
            pick_win,
            width=54,
            height=6,
            font=("Consolas", 9),
            bg="#141C2B",
            fg="#00E5FF",
            selectbackground="#0284C7",
            selectforeground="#FFFFFF",
            bd=1,
            relief="solid",
        )
        for path in options:
            listbox.insert(tk.END, path)
        listbox.pack(pady=5)

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            path = listbox.get(sel[0])
            token = options[path]
            pick_win.destroy()
            threading.Thread(target=self._unlock_thread, args=(token,), daemon=True).start()

        btn = tk.Button(
            pick_win,
            text="Verify Face Biometrics & Unlock",
            font=("Segoe UI", 10, "bold"),
            fg="#FFFFFF",
            bg="#0D9488",
            activebackground="#0F766E",
            bd=0,
            cursor="hand2",
            pady=8,
            command=confirm,
        )
        btn.pack(pady=12, fill="x", padx=30)

    def _unlock_thread(self, token):
        self.logmsg("Starting biometric scanner. Look at camera & blink naturally...")
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(MODEL_PATH)

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.logmsg("ERROR: could not access webcam device.")
            return

        CONFIDENCE_THRESHOLD = 70  # lower = stricter for LBPH
        eye_open_prev = True
        blink_detected = False
        face_recognized = False
        start_time = time.time()
        TIMEOUT = 15

        while time.time() - start_time < TIMEOUT:
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5)

            face_recognized = False
            for (x, y, w, h) in faces:
                face_roi = cv2.resize(gray[y : y + h, x : x + w], (200, 200))
                label, confidence = recognizer.predict(face_roi)
                if confidence < CONFIDENCE_THRESHOLD:
                    face_recognized = True
                    draw_tech_corners(frame, x, y, w, h, color=(0, 255, 0), thickness=2, length=25)

                    eyes = EYE_CASCADE.detectMultiScale(gray[y : y + h, x : x + w])
                    eyes_open_now = len(eyes) >= 2

                    if (not eye_open_prev) and eyes_open_now:
                        blink_detected = True
                    eye_open_prev = eyes_open_now
                else:
                    draw_tech_corners(frame, x, y, w, h, color=(0, 0, 255), thickness=2, length=25)
                break

            status_color = (0, 255, 0) if face_recognized else (0, 0, 255)
            blink_color = (0, 255, 0) if blink_detected else (0, 210, 255)

            cv2.putText(
                frame,
                f"BIOMETRIC: {'MATCH VERIFIED' if face_recognized else 'SCANNING...'}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                status_color,
                2,
            )
            cv2.putText(
                frame,
                f"LIVENESS: {'BLINK CONFIRMED' if blink_detected else 'BLINK TO UNLOCK'}",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                blink_color,
                2,
            )
            cv2.imshow("Face Lock Verification - Press Q to Cancel", frame)

            if face_recognized and blink_detected:
                cv2.waitKey(400)
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                cap.release()
                cv2.destroyAllWindows()
                self.logmsg("Verification aborted by user.")
                return

        cap.release()
        cv2.destroyAllWindows()

        if not (face_recognized and blink_detected):
            self.logmsg("ACCESS DENIED: Biometric match failed or liveness timeout.")
            messagebox.showerror("Access Denied", "Face verification or eye-blink liveness check failed.")
            return

        entry = self.cfg["locked_folders"].get(token)
        if not entry:
            self.logmsg("Lock record not found.")
            return

        try:
            if os.name == "nt":
                os.system(f'attrib -h -s "{entry["hidden_path"]}"')
            os.rename(entry["hidden_path"], entry["original_path"])
        except Exception as e:
            self.logmsg(f"Error restoring folder: {e}")
            messagebox.showerror("Restore Error", f"Could not restore folder: {e}")
            return

        del self.cfg["locked_folders"][token]
        save_config(self.cfg)
        self.logmsg(f"UNLOCKED & RESTORED: {entry['original_path']}")
        self.refresh_status()
        messagebox.showinfo("Folder Unlocked", f"Biometric & Liveness Verified!\nFolder restored to:\n{entry['original_path']}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceLockApp(root)
    root.mainloop()
