# Mithun AI — Windows Desktop Assistant

A lightweight JARVIS-style assistant with a futuristic desktop UI, voice input,
spoken responses, wake-word mode, weather, news, safe local commands, web search,
and Gemini-powered chat.

## Requirements

- Windows 10 or 11
- Python 3.10–3.12
- Internet connection for speech recognition and Gemini chat
- A microphone for voice commands

## Quick start

1. Extract the ZIP.
2. Double-click `run.bat` and wait for package installation.
3. Test local commands such as `Open Notepad`, `Open YouTube`, or `What time is it?`.

## Enable Gemini AI chat

1. Get a Gemini API key from https://aistudio.google.com/app/apikey
2. Copy `.env.example` and rename the copy to `.env`.
3. Replace `your_gemini_api_key_here` with your key.
4. Restart `run.bat`.

Never upload or commit your `.env` file.

## Supported commands

- `Open Notepad`
- `Open Calculator`
- `Open Paint`
- `Open File Explorer`
- `Open YouTube`, `Open Google`, `Open GitHub`, `Open Gmail`
- `Search Python DSA roadmap`
- `YouTube machine learning tutorial`
- `What time is it?`
- `Weather in Kakinada`
- `Latest news`
- `Take screenshot`
- `Volume up`, `Volume down`, or `Mute`
- `Find file resume`
- Any general question (with Gemini key configured)

## Wake mode

Click **WAKE MODE: OFF** once to turn it on. Then say `Hey Mithun`. You can say the
command in the same phrase (`Hey Mithun, open YouTube`) or wait for the assistant
to say `Yes Mithun, boliye` and speak the command. Click the button again to stop
background listening.

## Computer controls

- Screenshots are saved under `Pictures/MithunAI Screenshots`.
- File search checks Desktop, Documents, Downloads, and OneDrive when present.
- File search returns at most eight matches and never deletes or modifies files.
- Volume commands use safe Windows media keys.

## Start manually

```powershell
python main.py
```

The microphone uses `sounddevice`, so PyAudio and Microsoft C++ Build Tools are
not required. Press **LISTEN**, speak within eight seconds, and wait for the reply.

## Safety

The assistant runs only a small allowlist of local apps. Destructive system actions
such as deleting files, shutdown, registry changes, and arbitrary shell execution
are intentionally disabled in this version.
