#!/usr/bin/env python3
"""
Real-time dashboard window.
Plots water level, total pests, temperature, and humidity.
Called from main.py   →   run_dashboard(shared_data, lock)
"""
# ─── matplotlib import guard ───
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    import tkinter.messagebox as mb, sys
    mb.showerror("Missing library",
        "matplotlib is not installed.\n\n"
        "Activate your virtual-env and run:\n   pip install matplotlib")
    sys.exit(1)
# ───────────────────────────────

import tkinter as tk, time
from collections import deque
GREEN="#66bb6a"; ORANGE="#fb8c00"; BLUE="#42a5f5"

def run_dashboard(shared_data, lock):
    root = tk.Toplevel()
    root.title("Smart Agriculture IoT Sensor Data Dashboard")

    # ⇢ NEW — full-screen + “back” arrow
    root.attributes('-fullscreen', True)

    back_row = tk.Frame(root, bg="#EEE")
    back_row.pack(fill=tk.X, padx=5, pady=5, anchor="w")
    tk.Button(back_row, text="← Back", font=("Arial", 12, "bold"),
              command=root.destroy).pack(side=tk.LEFT)

    fig, ((ax_water, ax_pest), (ax_temp, ax_hum)) = \
        plt.subplots(2,2, figsize=(8,6))
    fig.patch.set_facecolor("#f0f0f0"); plt.tight_layout(pad=3)
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # rolling buffers
    water_y = deque(maxlen=300)
    pest_y  = deque(maxlen=300)
    temp_y  = deque(maxlen=300)
    hum_y   = deque(maxlen=300)

    # metric labels
    metrics = tk.Frame(root, bg="#e8f5e9"); metrics.pack(fill=tk.X)
    lbl_pests=tk.Label(metrics,bg="#e8f5e9",font=("Arial",12))
    lbl_temp =tk.Label(metrics,bg="#e8f5e9",font=("Arial",12))
    lbl_hum  =tk.Label(metrics,bg="#e8f5e9",font=("Arial",12))
    for w in (lbl_pests,lbl_temp,lbl_hum):
        w.pack(side=tk.LEFT, expand=True, padx=10, pady=6)

    def refresh():
        with lock:
            wh = list(shared_data["water_history"])
            pt = list(shared_data["pest_total_history"])
            th = list(shared_data["th_history"])
            pest_total = shared_data["pest_count"]
            cur_temp   = shared_data["current_temp"]
            cur_hum    = shared_data["current_hum"]

        if wh:
            try:
                cm=float(wh[-1][1].split(":")[1].split("cm")[0]); water_y.append(cm)
            except Exception: pass
        if pt:
            pest_y.append(pt[-1][1])          # append latest total
        if th:
            _,tc,h=th[-1]; temp_y.append(tc); hum_y.append(h)

        # plots
        ax_water.clear(); ax_water.set_title("Water Level (cm)")
        ax_water.plot(water_y,color=BLUE); ax_water.set_ylabel("cm")
        ax_water.set_xlabel("Current Time"); ax_water.set_xticks([])

        if water_y:                                             # only when we have data
            lo  = min(water_y)
            hi  = max(water_y)
            # round outward then create ticks at 0.3 cm steps
            import numpy as np
            start = np.floor(lo / 0.3) * 0.3
            stop  = np.ceil(hi / 0.3) * 0.3 + 0.001
            ax_water.set_yticks(np.arange(start, stop, 0.3))

        ax_pest.clear(); ax_pest.set_title("Total Pests Detected")
        ax_pest.plot(pest_y,color=GREEN,marker="o")
        ax_pest.set_ylabel("count"); ax_pest.set_xlabel("Current Time")
        ax_pest.set_xticks([])

        ax_temp.clear(); ax_temp.set_title("Temperature (°C)")
        ax_temp.plot(temp_y,color=ORANGE);  ax_temp.set_ylabel("°C")
        ax_temp.set_xlabel("Current Time"); ax_temp.set_xticks([])

        ax_hum.clear();  ax_hum.set_title("Humidity (%)")
        ax_hum.plot(hum_y,color="#9D00FF");     ax_hum.set_ylabel("%")
        ax_hum.set_xlabel("Current Time"); ax_hum.set_xticks([])

        canvas.draw()

        lbl_pests.config(text=f"Total pests: {pest_total}")
        lbl_temp.config(text=f"Temperature now: {cur_temp}")
        lbl_hum.config(text=f"Humidity now: {cur_hum}")

        root.after(1000, refresh)

    refresh(); root.mainloop()