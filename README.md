# KeepAwake 🖥️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

A lightweight **Windows tray app** that prevents your PC from going into standby during working hours.  
It runs silently in the system tray with a green/red status icon and simple menu controls.

---

## ✨ Features
- 🟢 **Green tray icon** when active, 🔴 **red icon** when stopped  
- ⏰ Keeps your PC awake **Monday–Friday, 08:00–18:00** 
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
