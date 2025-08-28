import ctypes
import time
import datetime
import subprocess
import threading
from loguru import logger
import pystray
from PIL import Image, ImageDraw
from pathlib import Path
import json
import win32api
import win32con

# --- Logging setup ---
logger.remove()
logger.add("keep_awake.log", rotation="1 day", retention="1 day", level="INFO")


# --- Load configuration ---
CONFIG_FILE = Path("config.json")
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {"start_hour": 8, "end_hour": 18,   "sleep_after_min": 30, "check_interval_sec": 300, "disable_if_workstation_locked": False}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# --- Config ---
START_HOUR = config.get("start_hour", 8)
END_HOUR = config.get("end_hour", 18)
SLEEP_AFTER_MIN = config.get("sleep_after_min", 30)
CHECK_INTERVAL = config.get("check_interval_sec", 300)
DISABLE_IF_WORKSTATION_LOCKED = config.get("disable_if_workstation_locked", False)

# --- Sleep control ---
running = True
working = True  # whether we keep the PC awake
last_state = None  # Track last applied state


def disable_sleep():
    subprocess.run(["powercfg", "-change", "-standby-timeout-ac", "0"], shell=True)
    logger.info("Sleep disabled")

def enable_sleep():
    subprocess.run(["powercfg", "-change", "-standby-timeout-ac", f"{SLEEP_AFTER_MIN}"], shell=True)
    logger.info("Sleep enabled")


# --- Background worker ---
def keep_awake(icon):
    global last_state
    logger.info("KeepAwake service started")
    while running:
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        if DISABLE_IF_WORKSTATION_LOCKED and is_workstation_locked():
            desired_state = "normal"  # monitor locked → do nothing
            logger.info("Workstation locked → allowing normal standby")
        else:
            if working and weekday < 5 and START_HOUR <= now.hour < END_HOUR:
                desired_state = "awake"
            else:
                desired_state = "normal"

        # Apply change only if state has changed
        if desired_state != last_state:
            if desired_state == "awake":
                disable_sleep()
            else:
                enable_sleep()
            last_state = desired_state
        else:
            logger.info(f"No state change, still '{last_state}'")

        # optical if its in working time and enabled
        if desired_state == "awake" and weekday < 5 and START_HOUR <= now.hour < END_HOUR and icon.icon != ICON_WORKTIME:
            icon.icon = ICON_WORKTIME
        elif desired_state == "normal" or not (weekday < 5 and START_HOUR <= now.hour < END_HOUR):
            icon.icon = ICON_ACTIVE

        logger.info(f"Sleep {CHECK_INTERVAL}s")
        time.sleep(CHECK_INTERVAL)  # check every 5 minutes

# --- Icon creation ---
def make_icon(color):
    """Create a circular icon with given color."""
    img = Image.new("RGB", (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return img

ICON_WORKTIME = make_icon((0, 200, 0))   # green
ICON_INACTIVE = make_icon((200, 0, 0)) # red
ICON_ACTIVE = make_icon((255, 165, 0)) # Orange

def is_workstation_locked():
    """
    Returns True if the workstation is locked, False otherwise.
    """
    user32 = ctypes.windll.User32
    hDesktop = user32.OpenInputDesktop(0, False, win32con.DESKTOP_SWITCHDESKTOP)
    if hDesktop == 0:
        # Desktop is locked or unavailable
        return True
    else:
        user32.CloseDesktop(hDesktop)
        return False

# def turn_off_screen():
#     """
#     Function to turn off the screen.
#     """
#     return win32api.PostMessage(win32con.HWND_BROADCAST,
#                             win32con.WM_SYSCOMMAND, win32con.SC_MONITORPOWER, 2)

# --- Tray menu actions ---
def on_start(icon, item):
    global working
    working = True
    now = datetime.datetime.now()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    if weekday < 5 and START_HOUR <= now.hour < END_HOUR and icon.icon != ICON_WORKTIME:
        icon.icon = ICON_WORKTIME
    else:
        icon.icon = ICON_ACTIVE

    logger.info("KeepAwake activated")
    disable_sleep()

def on_stop(icon, item):
    global working
    working = False
    icon.icon = ICON_INACTIVE
    logger.info("KeepAwake deactivated")
    enable_sleep()

def on_exit(icon, item):
    global running
    running = False
    icon.stop()
    logger.info("Exiting KeepAwake")


# --- Tray runner ---
def run_tray():
    icon = pystray.Icon(
        "keep_awake",
        ICON_ACTIVE if working else ICON_INACTIVE,
        "KeepAwake",
        menu=pystray.Menu(
            pystray.MenuItem("Start", on_start),
            pystray.MenuItem("Stop", on_stop),
            pystray.MenuItem("Exit", on_exit)
        )
    )

    # Worker mit Icon starten
    t = threading.Thread(target=keep_awake, args=(icon,), daemon=True)
    t.start()

    icon.run()



if __name__ == "__main__":
    # Run tray icon
    run_tray()
