import json
import os
import queue
import subprocess
import threading
import time
import ctypes
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext
import xml.etree.ElementTree as ET


APP_NAME = "MITHUN AI"
BG = "#030712"
PANEL = "#081426"
CYAN = "#19d3ff"
TEXT = "#d7f7ff"
MUTED = "#6f9aac"
GREEN = "#39ffad"

APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "command prompt": ["cmd.exe"],
    "cmd": ["cmd.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
}

SITES = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
}


def load_env(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class MithunAI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} — Desktop Assistant")
        self.root.geometry("1050x700")
        self.root.minsize(820, 580)
        self.root.configure(bg=BG)
        self.events = queue.Queue()
        self.listening = False
        self.wake_mode = False
        self.wake_thread = None
        self.voice_enabled = True
        self.orbit_angle = 0
        self._build_ui()
        self._tick()
        self._animate_core()
        self.add_message("AI", "Systems online. Type a command or press LISTEN.")

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG, padx=28, pady=20)
        header.pack(fill="x")

        tk.Label(header, text=APP_NAME, bg=BG, fg=CYAN,
                 font=("Segoe UI", 25, "bold")).pack(side="left")
        self.status = tk.Label(header, text="● ONLINE", bg=BG, fg=GREEN,
                               font=("Consolas", 11, "bold"))
        self.status.pack(side="right")

        body = tk.Frame(self.root, bg=BG, padx=28, pady=4)
        body.pack(fill="both", expand=True)

        side = tk.Frame(body, bg=PANEL, width=220, padx=18, pady=22,
                        highlightbackground="#123b51", highlightthickness=1)
        side.pack(side="left", fill="y", padx=(0, 18))
        side.pack_propagate(False)

        self.core = tk.Canvas(side, width=170, height=170, bg=PANEL,
                              highlightthickness=0)
        self.core.pack(pady=(5, 14))

        tk.Label(side, text="QUICK COMMANDS", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        examples = [
            "Open YouTube", "Open Notepad", "Search Python DSA",
            "What time is it?", "Ask any AI question"
        ]
        for item in examples:
            tk.Label(side, text="› " + item, bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 10), wraplength=180,
                     justify="left").pack(anchor="w", pady=5)

        self.wake_button = tk.Button(
            side, text="WAKE MODE: OFF", command=self.toggle_wake_mode,
            bg="#10283a", fg=MUTED, activebackground="#17445e",
            activeforeground=TEXT, relief="flat", pady=9,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        self.wake_button.pack(side="bottom", fill="x")

        chat_panel = tk.Frame(body, bg=PANEL, padx=16, pady=16,
                              highlightbackground="#123b51", highlightthickness=1)
        chat_panel.pack(side="left", fill="both", expand=True)

        self.chat = scrolledtext.ScrolledText(
            chat_panel, bg="#050d19", fg=TEXT, insertbackground=CYAN,
            font=("Segoe UI", 11), relief="flat", padx=15, pady=15,
            wrap="word", state="disabled"
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("ai", foreground=CYAN, font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("you", foreground=GREEN, font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("body", foreground=TEXT, spacing3=12)

        controls = tk.Frame(chat_panel, bg=PANEL, pady=14)
        controls.pack(fill="x")
        self.entry = tk.Entry(controls, bg="#07101e", fg=TEXT,
                              insertbackground=CYAN, relief="flat",
                              font=("Segoe UI", 12))
        self.entry.pack(side="left", fill="x", expand=True, ipady=12, padx=(0, 10))
        self.entry.bind("<Return>", lambda _event: self.submit())

        tk.Button(controls, text="SEND", command=self.submit, bg=CYAN, fg=BG,
                  activebackground="#8beaff", relief="flat", padx=18, pady=11,
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left")
        self.listen_button = tk.Button(
            controls, text="◉ LISTEN", command=self.listen, bg="#10283a", fg=CYAN,
            activebackground="#17445e", activeforeground=TEXT, relief="flat",
            padx=16, pady=11, font=("Segoe UI", 10, "bold"), cursor="hand2"
        )
        self.listen_button.pack(side="left", padx=(10, 0))

    def add_message(self, speaker, message):
        self.chat.configure(state="normal")
        tag = "you" if speaker == "YOU" else "ai"
        self.chat.insert("end", f"{speaker}\n", tag)
        self.chat.insert("end", f"{message}\n\n", "body")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def submit(self):
        command = self.entry.get().strip()
        if not command:
            return
        self.entry.delete(0, "end")
        self.add_message("YOU", command)
        self.set_busy(True)
        threading.Thread(target=self._process_worker, args=(command,), daemon=True).start()

    def _process_worker(self, command):
        try:
            reply = self.handle_command(command)
        except Exception as exc:
            reply = f"Something went wrong: {exc}"
        self.events.put(("reply", reply))

    def handle_command(self, command):
        text = command.lower().strip()

        if text in {"hi", "hello", "hey", "namaste"}:
            return "Hello Mithun! How can I help you?"
        if "time" in text and len(text.split()) <= 7:
            return "Current time is " + datetime.now().strftime("%I:%M %p") + "."
        if "date" in text and len(text.split()) <= 7:
            return "Today is " + datetime.now().strftime("%A, %d %B %Y") + "."

        if "weather" in text or "temperature" in text:
            city = self._extract_city(command)
            return self.get_weather(city)

        if text in {"news", "latest news", "tell me the news", "headlines"} or "latest news" in text:
            return self.get_news()

        if "screenshot" in text or "screen shot" in text:
            return self.take_screenshot()

        if text in {"volume up", "increase volume", "sound up"}:
            return self.change_volume("up")
        if text in {"volume down", "decrease volume", "sound down"}:
            return self.change_volume("down")
        if text in {"mute", "mute volume", "unmute", "unmute volume"}:
            return self.change_volume("mute")

        for prefix in ("find file ", "search file ", "locate file "):
            if text.startswith(prefix):
                filename = command[len(prefix):].strip()
                return self.find_files(filename)

        if text.startswith("open "):
            target = text[5:].strip()
            if target in SITES:
                webbrowser.open(SITES[target])
                return f"Opening {target.title()}."
            if target in APPS:
                subprocess.Popen(APPS[target])
                return f"Opening {target.title()}."
            return f"I don't have '{target}' in my safe app list yet."

        if text.startswith("search "):
            query = command[7:].strip()
            if not query:
                return "Tell me what you want to search."
            webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(query))
            return f"Searching Google for {query}."

        if text.startswith("youtube "):
            query = command[8:].strip()
            webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
            return f"Searching YouTube for {query}."

        return self.ask_gemini(command)

    def _extract_city(self, command):
        lowered = command.lower()
        for marker in ("weather in ", "temperature in "):
            if marker in lowered:
                start = lowered.index(marker) + len(marker)
                city = command[start:].strip(" ?.!")
                if city:
                    return city
        return os.getenv("DEFAULT_CITY", "Kakinada")

    def get_weather(self, city):
        url = "https://wttr.in/" + urllib.parse.quote(city) + "?format=j1"
        request = urllib.request.Request(url, headers={"User-Agent": "MithunAI/1.1"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            current = data["current_condition"][0]
            description = current["weatherDesc"][0]["value"]
            return (f"{city} mein {description} hai. Temperature {current['temp_C']}°C, "
                    f"feels like {current['FeelsLikeC']}°C, aur humidity {current['humidity']}% hai.")
        except Exception:
            return f"Sorry, {city} ka weather abhi retrieve nahi ho paaya."

    def get_news(self):
        url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        request = urllib.request.Request(url, headers={"User-Agent": "MithunAI/1.1"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                root = ET.fromstring(response.read())
            titles = [item.findtext("title", "").strip()
                      for item in root.findall("./channel/item")[:5]]
            titles = [title for title in titles if title]
            if not titles:
                raise ValueError("No headlines")
            return "India ke latest headlines:\n" + "\n".join(
                f"{index}. {title}" for index, title in enumerate(titles, 1)
            )
        except Exception:
            return "Sorry, latest news abhi retrieve nahi ho paayi."

    def take_screenshot(self):
        try:
            from PIL import ImageGrab

            pictures = Path.home() / "Pictures" / "MithunAI Screenshots"
            pictures.mkdir(parents=True, exist_ok=True)
            filename = "screenshot_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
            destination = pictures / filename
            ImageGrab.grab().save(destination)
            return f"Screenshot saved: {destination}"
        except Exception as exc:
            return f"Screenshot capture failed: {exc}"

    @staticmethod
    def change_volume(action):
        # Windows virtual media keys: mute, volume down, volume up.
        keys = {"mute": 0xAD, "down": 0xAE, "up": 0xAF}
        try:
            key = keys[action]
            presses = 3 if action in {"up", "down"} else 1
            for _ in range(presses):
                ctypes.windll.user32.keybd_event(key, 0, 0, 0)
                ctypes.windll.user32.keybd_event(key, 0, 2, 0)
            messages = {
                "up": "Volume increased.",
                "down": "Volume decreased.",
                "mute": "Mute state toggled."
            }
            return messages[action]
        except Exception:
            return "Volume control is available only on Windows."

    @staticmethod
    def find_files(filename):
        if not filename:
            return "Please provide a file name, for example: Find file resume."

        home = Path.home()
        roots = [home / "Desktop", home / "Documents", home / "Downloads"]
        one_drive = home / "OneDrive"
        if one_drive.exists():
            roots.append(one_drive)

        query = filename.lower()
        matches = []
        skipped = {".git", ".venv", "node_modules", "__pycache__"}
        for root in roots:
            if not root.exists():
                continue
            try:
                for current, directories, files in os.walk(root):
                    directories[:] = [name for name in directories if name not in skipped]
                    for name in files:
                        if query in name.lower():
                            matches.append(str(Path(current) / name))
                            if len(matches) == 8:
                                break
                    if len(matches) == 8:
                        break
            except (PermissionError, OSError):
                continue
            if len(matches) == 8:
                break

        if not matches:
            return f"'{filename}' naam ki file common folders mein nahi mili."
        return f"{len(matches)} matching file(s) mili:\n" + "\n".join(
            f"{index}. {path}" for index, path in enumerate(matches, 1)
        )

    def ask_gemini(self, prompt):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return ("AI chat needs a Gemini API key. Copy .env.example to .env, "
                    "add your key, and restart the app. Local commands already work.")

        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        url = ("https://generativelanguage.googleapis.com/v1beta/models/" +
               urllib.parse.quote(model, safe="") + ":generateContent?key=" +
               urllib.parse.quote(api_key))
        payload = {
            "system_instruction": {"parts": [{"text": (
                "You are Mithun AI, a concise and friendly Windows desktop assistant. "
                "Reply in Hinglish when the user uses Hindi or Hinglish."
            )}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.5, "maxOutputTokens": 500},
        }
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:250]
            return f"Gemini API error ({exc.code}): {detail}"
        except (KeyError, IndexError):
            return "Gemini returned an unexpected response. Please try again."

    def listen(self):
        if self.listening:
            return
        self.listening = True
        self.set_busy(True, "● LISTENING")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    @staticmethod
    def _record_and_recognize(duration=8):
        import numpy as np
        import sounddevice as sd
        import speech_recognition as sr

        sample_rate = 16000
        recognizer = sr.Recognizer()
        recording = sd.rec(
            int(duration * sample_rate), samplerate=sample_rate,
            channels=1, dtype="int16"
        )
        sd.wait()
        audio = sr.AudioData(np.asarray(recording, dtype=np.int16).tobytes(), sample_rate, 2)
        try:
            return recognizer.recognize_google(audio, language="en-IN")
        except sr.UnknownValueError:
            return recognizer.recognize_google(audio, language="hi-IN")

    def _listen_worker(self):
        try:
            command = self._record_and_recognize(8)
            self.events.put(("voice", command))
        except ImportError:
            self.events.put(("error", "Voice packages are not installed. Run: pip install -r requirements.txt"))
        except Exception as exc:
            self.events.put(("error", f"I could not hear clearly: {exc}"))

    def toggle_wake_mode(self):
        self.wake_mode = not self.wake_mode
        if self.wake_mode:
            self.wake_button.configure(text="WAKE MODE: ON", fg=GREEN)
            self.add_message("AI", "Wake mode enabled. Say: Hey Mithun.")
            self.wake_thread = threading.Thread(target=self._wake_worker, daemon=True)
            self.wake_thread.start()
        else:
            self.wake_button.configure(text="WAKE MODE: OFF", fg=MUTED)
            self.add_message("AI", "Wake mode disabled.")

    def _wake_worker(self):
        while self.wake_mode:
            if self.listening:
                time.sleep(0.5)
                continue
            try:
                heard = self._record_and_recognize(4)
                lowered = heard.lower()
                if "hey mithun" not in lowered and "hi mithun" not in lowered:
                    continue
                command = lowered.replace("hey mithun", "", 1).replace("hi mithun", "", 1).strip()
                self.events.put(("wake", command))
                while self.listening and self.wake_mode:
                    time.sleep(0.25)
            except Exception:
                time.sleep(0.5)

    def speak(self, text):
        if not self.voice_enabled:
            return
        def worker():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", 175)
                engine.say(text[:800])
                engine.runAndWait()
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def set_busy(self, busy, label=None):
        self.status.configure(text=label or ("● THINKING" if busy else "● ONLINE"),
                              fg="#ffd166" if busy else GREEN)

    def _animate_core(self):
        self.core.delete("all")
        angle = self.orbit_angle
        self.core.create_oval(12, 12, 158, 158, outline="#0b3448", width=2)
        self.core.create_arc(17, 17, 153, 153, start=angle, extent=80,
                             style="arc", outline=CYAN, width=3)
        self.core.create_arc(28, 28, 142, 142, start=-angle * 1.4, extent=125,
                             style="arc", outline="#15799a", width=2)
        pulse = 3 if (angle // 20) % 2 else 0
        self.core.create_oval(61-pulse, 61-pulse, 109+pulse, 109+pulse,
                              fill=CYAN, outline="#b9f6ff", width=2)
        self.core.create_text(85, 85, text="AI", fill=BG,
                              font=("Segoe UI", 13, "bold"))
        self.orbit_angle = (angle + 4) % 360
        self.root.after(45, self._animate_core)

    def _tick(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "voice":
                    self.listening = False
                    self.add_message("YOU", value)
                    threading.Thread(target=self._process_worker, args=(value,), daemon=True).start()
                elif kind == "wake":
                    self.listening = True
                    if value:
                        self.add_message("YOU", value)
                        self.set_busy(True)
                        threading.Thread(target=self._process_worker, args=(value,), daemon=True).start()
                    else:
                        self.add_message("AI", "Yes Mithun, boliye.")
                        self.speak("Yes Mithun, boliye.")
                        threading.Thread(target=self._listen_worker, daemon=True).start()
                elif kind == "reply":
                    self.listening = False
                    self.add_message("AI", value)
                    self.speak(value)
                    self.set_busy(False)
                elif kind == "error":
                    self.listening = False
                    self.add_message("AI", value)
                    self.set_busy(False)
        except queue.Empty:
            pass
        self.root.after(100, self._tick)


def main():
    load_env()
    root = tk.Tk()
    app = MithunAI(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
