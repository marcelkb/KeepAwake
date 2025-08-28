# KeepAwake 🖥️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

A lightweight **Windows tray app** that prevents your PC from going into standby during working hours if connected to ac.  
It runs silently in the system tray with a green/red status icon and simple menu controls.

---

## ✨ Features
- 🟢 **Green tray icon** when active, 🔴 **red icon** when stopped  
- ⏰ Keeps your PC awake **Monday–Friday, 08:00–18:00** (configurable)
- 📜 Logging with [loguru](https://github.com/Delgan/loguru) (`keep_awake.log`, rotated daily)  
- 🖱️ Tray menu options: **Start / Stop / Exit**  
- 🚀 Build into a standalone `.exe` with [PyInstaller](https://pyinstaller.org/)  

---

## 📦 Requirements
- Python **3.10+**
- Dependencies:
  - [loguru](https://github.com/Delgan/loguru)  
  - [pystray](https://github.com/moses-palmer/pystray)  
  - [Pillow](https://python-pillow.org/)  

## ⚙️ Configuration (`config.json`)

The behavior of **KeepAwake** can be customized using a simple `config.json` file located in the same folder as the script or executable.
- start_hour: hour of the working week where the script should begin to avoid standby
- end_hour: hour of the working week where the script should end the avoid of standby
- sleep_after_min: configuration for the powerplan sleep after x minutes
- check_interval_sec: seconds to wait to check again if the powerplan must be changed based on time
- disable_if_workstation_locked: disables the function if workstation is locked, default is false

### Example `config.json`

```json
{
  "start_hour": 8,
  "end_hour": 18,
  "sleep_after_min": 30,
  "check_interval_sec": 300
  "disable_if_workstation_locked": false
}
```

Install with [uv](https://github.com/astral-sh/uv).  

```bash
  uv add loguru pystray pillow
  
  ▶️ Run from source
  uv run python keep_awake_tray.py
  
  🛠️ Build as EXE
  
  Bundle into a Windows executable:
  
  uv add pyinstaller --dev
  uv run pyinstaller --onefile --noconsole keep_awake_tray.py
  ```
  
  The .exe will be generated in dist/keep_awake_tray.exe

## Preview
  <img width="150" height="96" alt="image" src="https://github.com/user-attachments/assets/54e8d67b-0f16-42ce-92c1-f5883492a729" />

