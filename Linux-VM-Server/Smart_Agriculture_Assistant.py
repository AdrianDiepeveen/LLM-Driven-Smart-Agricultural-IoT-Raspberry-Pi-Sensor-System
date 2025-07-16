#!/usr/bin/env python3
"""
Chat-style LLM assistant window.
Called from main.py   →   run_chat_gui(shared_data, lock)
"""

import os, re, subprocess, threading, time, tkinter as tk
ANSI = re.compile(r'\x1b\[[0-9;?]*[ -/]*[@-~]')
strip = lambda t: ANSI.sub('', t)

# Smart agriculture assistant chat graphical user interface
def run_chat_gui(shared_data, lock):
    root = tk.Toplevel()
    root.title("Smart Farming AI Assistant")

    # ⇢ NEW — full-screen + “back” arrow
    root.attributes('-fullscreen', True)

    back_row = tk.Frame(root, bg="#EEE")
    back_row.pack(fill=tk.X, padx=5, pady=5, anchor="w")
    tk.Button(back_row, text="← Back", font=("Arial", 12, "bold"),
              command=root.destroy).pack(side=tk.LEFT)

    # Loading Indicator for responses
    loading = tk.Label(root, text="", font=("Arial", 12), fg="#555")
    loading.pack(pady=(5,0))

    # Widgets
    row = tk.Frame(root, bg="#EEE")
    row.pack(fill=tk.X, padx=10, pady=5)

    ctx_var = tk.StringVar(value="General")
    ctx_menu = tk.OptionMenu(
        row, ctx_var,
        "General", "Water Level", "Pest Detection", "Temperature and Humidity"
    )
    ctx_menu.config(font=("Arial", 11))
    ctx_menu.pack(side=tk.LEFT, padx=5, pady=5)

    prompt_entry = tk.Entry(row, font=("Arial", 11), width=50)
    prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    send_btn = tk.Button(row, text="Send", font=("Arial", 11))
    send_btn.pack(side=tk.RIGHT, padx=5)

    chat = tk.Text(root, wrap=tk.WORD, state=tk.DISABLED,
                   bg="#FFFFFF", font=("Arial", 11))
    chat.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # ───────── helpers ─────────
    # ───────── helpers ─────────
    def append(txt, tag=None):
        chat.config(state=tk.NORMAL)

        # remember where the new text will start
        start_index = chat.index("end-1c")

        # ----- wrap the two speaker-tags in coloured bubbles -----
        if tag == "user":
            txt = f"Farmer: {txt}\n\n"
        elif tag == "assistant":
            txt = f"Smart-Ag Assistant: {txt}\n\n"

        chat.insert(tk.END, txt)

        if tag:
            # 1️⃣  define bubble-styles only **once**
            if not chat.tag_names().__contains__("bubble_user"):
                chat.tag_config(
                    "bubble_user",
                    background="#d1f2d1",        # light green
                    foreground="#006400",        # dark green text
                    lmargin1=10, lmargin2=10,    # left-indents
                    rmargin=50, spacing3=4,      # right indent & gap after paragraph
                    relief="ridge", borderwidth=2
                )
                chat.tag_config(
                    "bubble_ai",
                    background="#e0e0e0",        # light grey
                    foreground="black",
                    lmargin1=50, lmargin2=50,
                    rmargin=10, spacing3=4,
                    relief="ridge", borderwidth=2
                )

            # 2️⃣  apply the right bubble tag to the just-inserted block
            end_index = chat.index("end-1c")
            bubble_tag = "bubble_user" if tag == "user" else "bubble_ai"
            chat.tag_add(bubble_tag, start_index, end_index)

        chat.config(state=tk.DISABLED)
        chat.see(tk.END)


    # -------- build specialised prompt ----------
    def build_prompt(ctx, user):
        if ctx == "Water Level":
            with lock:
                hist   = "\n".join(f"- {t}: {l}" for t, l in shared_data["water_history"])
                latest = shared_data["current_water"]
            return (
                "You are an AI agronomist.\nWater-level readings:\n"
                f"{hist}\n\nLatest: {latest}\n"
                "Explain implications for crop growth and irrigation.\n"
            ) + user

        if ctx == "Pest Detection":
            with lock:
                hist  = "\n".join(f"- {t}: {l}" for t, l in shared_data["pest_history"])
                total = shared_data["pest_count"]
            return (
                "You are an AI agronomist.\nPest-detection events:\n"
                f"{hist}\n\nTotal pests so far: {total}\n"
                "Assess pest pressure and actions.\n"
            ) + user

        if ctx == "Temperature and Humidity":
            with lock:
                hist = "\n".join(
                    f"- {t}: {temp:.1f}°C, {hum:.1f}%"
                    for t, temp, hum in shared_data["th_history"][-100:]
                )
                latest = f"{shared_data['current_temp']}, {shared_data['current_hum']}"
            return (
                "You are an AI agronomist.\n"
                "Temperature and humidity readings:\n"
                f"{hist}\n\nLatest: {latest}\n"
                "Explain implications for crop growth and irrigation.\n"
            ) + user

        return user

    # Run Ollama
    def run_llama(prompt: str):
        # show loading icon
        loading.config(text="\u231B Generating Response… \u231B")
        append("", tag=None)  # ensure new paragraph

        append("", tag="assistant")  # space before assistant text
        process = subprocess.Popen(
            ["ollama", "run", "llama3.2"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
            env=dict(os.environ, OLLAMA_NO_SPINNER="1")
        )
        process.stdin.write(prompt + "\n")
        process.stdin.close()
        
        # Stream ollama output with typing effect
        for line in process.stdout:
            cleaned = strip(line)
            for ch in cleaned:
                chat.config(state=tk.NORMAL)
                chat.insert(tk.END, ch)
                chat.config(state=tk.DISABLED)
                chat.tag_config("assistant", foreground="black")
                chat.see(tk.END)
                time.sleep(0.015)

        process.wait()
        loading.config(text="")  # clear loading

    # Event handler
    def on_send(_=None):
        user = prompt_entry.get().strip()
        if not user:
            return
        append(user, tag="user")     # dark green user prompt
        prompt_entry.delete(0, tk.END)
        threading.Thread(
            target=run_llama,
            args=(build_prompt(ctx_var.get(), user),),
            daemon=True
        ).start()

    root.bind("<Return>", on_send)
    send_btn.config(command=on_send)
    root.mainloop()