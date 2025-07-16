#!/usr/bin/env python3
"""
MAIN LAUNCHER – Smart-Agricultural IoT System
(login page ➜ dashboard / assistant)

• Reads SHA-256 hash from authentication.txt (root folder)
• Full-screen login (farm photo background + avatar)
• After authentication shows a home page with:
      – Dashboard   – Smart-Farming AI Assistant   – Exit
"""

import socket, threading, time, tkinter as tk
from tkinter import messagebox
import importlib.util, sys, hashlib
from pathlib import Path
from PIL import Image, ImageTk, ImageOps          # pip install pillow

# ───────── global data (unchanged) ─────────
shared_data = {
    "water_history": [], "current_water": "N/A",
    "pest_history": [],  "pest_total_history": [],
    "current_pest": "No Pests Detected", "pest_count": 0,
    "th_history": [],    "current_temp": "N/A", "current_hum": "N/A",
}
DATA_LOCK = threading.Lock()

# ───────── networking thread (unchanged) ─────────
SERVER_SOCKET = None
def sensor_server(host="0.0.0.0", port=6000):
    global SERVER_SOCKET
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        SERVER_SOCKET = srv
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port)); srv.listen(5)
        print(f"[Main] Sensor server listening on {port}")

        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                print("Server socket closed successfully."); break

            with conn:
                data = conn.recv(1024)
                if not data:
                    continue
                line = data.decode().strip()
                ts   = time.strftime("%Y-%m-%d %H:%M:%S")
                print("[Console]", line)

                with DATA_LOCK:
                    if line.startswith("Water level"):
                        shared_data["current_water"] = line
                        shared_data["water_history"].append((ts, line))
                    elif line.startswith("Pest"):
                        if line.startswith("Pest Detected"):
                            shared_data["pest_count"] += 1
                        shared_data["current_pest"] = line
                        shared_data["pest_history"].append((ts, line))
                    elif line.startswith("Total Pests Detected"):
                        try:
                            tot = int(line.split(":")[1].strip())
                            shared_data["pest_count"] = tot
                            shared_data["pest_total_history"].append((ts, tot))
                        except ValueError:
                            pass
                    elif line.startswith("Temperature:"):
                        try:
                            t = float(line.split("Temperature:")[1].split("°C")[0])
                            h = float(line.split("Humidity:")[1].split("%")[0])
                            shared_data["current_temp"] = f"{t:.1f} °C"
                            shared_data["current_hum"]  = f"{h:.1f} %"
                            shared_data["th_history"].append((ts, t, h))
                        except Exception:
                            pass
                conn.sendall(b"OK")

# ───────── dynamic import helpers (unchanged) ─────────
def _import_module(fname: str):
    path = Path(__file__).with_name(fname)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    return mod
def open_chat_window():      _import_module("Smart_Agriculture_Assistant.py").run_chat_gui(shared_data, DATA_LOCK)
def open_dashboard_window(): _import_module("Dashboard.py").run_dashboard(shared_data, DATA_LOCK)

# ───────── authentication helpers ─────────
USERNAME   = "adrian"
AUTH_FILE  = Path(__file__).with_name("authentication.txt")
ASSETS     = Path(__file__).with_name("assets")      # farm_bg.jpg, user_pic.jpeg

def load_stored_hash() -> str:
    if AUTH_FILE.exists():
        val = AUTH_FILE.read_text(encoding="utf-8").strip().lower()
        if len(val) == 64 and all(c in "0123456789abcdef" for c in val):
            return val
    messagebox.showerror("Login error", f"Cannot read valid hash from {AUTH_FILE}")
    sys.exit(1)

STORED_HASH = load_stored_hash()

def resize_to_screen(img, w, h):
    return ImageOps.fit(img, (w, h), Image.LANCZOS, centering=(0.5, 0.5))

# ───────── UI builders ─────────
def build_home_page(root: tk.Tk):
    for w in root.winfo_children(): w.destroy()
    root.attributes("-fullscreen", True)

    content = tk.Frame(root); content.place(relx=0.5, rely=0.3, anchor="c")

    tk.Label(content, text="\U0001F331  Welcome, Farmer!  \U0001F331",
             font=("Helvetica", 22, "bold"), fg="#2e7d32").pack(pady=20)

    tk.Label(content,
             text="\U0001F4CA  Monitor and Interpret Your Farm's IoT Sensor Data Below  \U0001F4CA",
             font=("Helvetica", 16, "bold"), fg="#2e7d32").pack(pady=10)

    tk.Button(content, text="Dashboard", font=("Arial", 14), width=32,
              bg="#66bb6a", command=open_dashboard_window).pack(pady=12)
    tk.Button(content, text="Smart Farming AI Assistant", font=("Arial", 14),
              width=32, bg="#81c784", command=open_chat_window).pack(pady=12)

    # Exit
    def on_exit():
        for aid in root.tk.call('after', 'info').split():
            try: root.after_cancel(aid)
            except Exception: pass
        if SERVER_SOCKET: SERVER_SOCKET.close()
        print("Server socket closed successfully.")
        root.destroy()

    tk.Button(content, text="Exit", font=("Arial", 14), width=32,
              bg="#e57373", command=on_exit).pack(pady=12)
    tk.Label(content, text="Receiving sensor data on TCP 6000 …",
             font=("Arial", 10, "italic")).pack(pady=(20, 0))


def build_login_screen(root: tk.Tk):
    root.attributes("-fullscreen", True)
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()

    # background
    bg_path = ASSETS / "farm_bg.jpg"
    if bg_path.exists():
        try:
            pil_bg = resize_to_screen(Image.open(bg_path), sw, sh)
            bg_img = ImageTk.PhotoImage(pil_bg)
            tk.Label(root, image=bg_img).place(relx=0.5, rely=0.5, anchor="c")
            root.bg_img = bg_img
        except Exception as e:
            print("Background image error:", e); root.configure(bg="#cfe8d5")
    else:
        root.configure(bg="#cfe8d5")

    # card
    card = tk.Frame(root, bg="#ffffff", bd=2, relief="groove")
    card.place(relx=0.5, rely=0.5, anchor="c")

    # avatar
    av_path = ASSETS / "user_pic.jpeg"
    if av_path.exists():
        try:
            img = Image.open(av_path).resize((140, 140), Image.LANCZOS)
            av  = ImageTk.PhotoImage(img)
            tk.Label(card, image=av, bg="#ffffff").pack(pady=(10, 0))
            card.avatar = av
        except Exception as e:
            print("Avatar error:", e)

    tk.Label(card, text="Log In", bg="#ffffff",
             font=("Helvetica", 18, "bold")).pack(pady=(10, 20))

    # username entry
    u_row = tk.Frame(card, bg="#ffffff"); u_row.pack(pady=5)
    tk.Label(u_row, text="Username:", bg="#ffffff",
             font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
    usr_var = tk.StringVar()
    tk.Entry(u_row, textvariable=usr_var, width=22,
             font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

    # password entry
    p_row = tk.Frame(card, bg="#ffffff"); p_row.pack(pady=5)
    tk.Label(p_row, text="Password:", bg="#ffffff",
             font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
    pwd_var = tk.StringVar()
    tk.Entry(p_row, textvariable=pwd_var, show="*", width=22,
             font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

    msg = tk.Label(card, text="", bg="#ffffff", font=("Arial", 10), fg="red")
    msg.pack(pady=(5, 0))

    # validate
    def attempt_login():
        if usr_var.get().strip().lower() != USERNAME:
            msg.config(text="Unknown user.")
            return
        hashed = hashlib.sha256(pwd_var.get().encode()).hexdigest()
        if hashed == STORED_HASH:
            # build home page after a tiny delay so Tkinter can
            # finish redrawing / destroying widgets (removes ‘lag’)
            root.after(1, lambda: build_home_page(root))
        else:
            msg.config(text="Incorrect password – please try again.")
            pwd_var.set(""); root.after(2000, lambda: msg.config(text=""))

    tk.Button(card, text="Login", font=("Arial", 12, "bold"),
              bg="#66bb6a", fg="white",
              command=attempt_login).pack(pady=15, ipadx=30)


# ═════════════════════ main entry-point ═════════════════════
def main():
    threading.Thread(target=sensor_server, daemon=True).start()
    root = tk.Tk(); root.title("AI-Driven Smart Agricultural IoT Monitoring System")
    build_login_screen(root)

    root.mainloop()

    sys.exit(0)

if __name__ == "__main__":
    main()