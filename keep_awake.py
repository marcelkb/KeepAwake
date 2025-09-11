import ctypes
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
working = True  # whether we keep the PC awake
last_state = None  # Track last applied state
stop_event = threading.Event()
worker_thread = None  # global

def disable_sleep():
    # Run the command
    result = subprocess.run(
        ["powercfg", "-change", "-standby-timeout-ac", "0"],
        capture_output=True,
        text=True,
        shell=True
    )

    if result.returncode != 0:
        logger.error("❌ Failed to run powercfg:", result.stderr.strip())
        return False

    logger.info("✅ Sleep successfully disabled on AC power.")
    return True


def enable_sleep():
    """Enable standby on AC power with given timeout (default 30 min) and verify."""
    result = subprocess.run(
        ["powercfg", "-change", "-standby-timeout-ac", str(SLEEP_AFTER_MIN)],
        capture_output=True,
        text=True,
        shell=True
    )
    if result.returncode != 0:
        logger.error("❌ Failed to run powercfg:", result.stderr.strip())
        return False
    logger.info(f"✅ Sleep successfully enabled with timeout {SLEEP_AFTER_MIN} min.")
    return True


# --- Background worker ---
def keep_awake(icon):
    global last_state
    logger.info("KeepAwake service started")
    while not stop_event.is_set():
        if working:
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
                    success = disable_sleep()
                else:
                    success = enable_sleep()
                if success:
                    last_state = desired_state
                    update_status(icon)

                    # optical if its in working time and enabled
                    if desired_state == "awake" and weekday < 5 and START_HOUR <= now.hour < END_HOUR and icon.icon != ICON_WORKTIME:
                        icon.icon = ICON_WORKTIME
                    elif desired_state == "normal" or not (weekday < 5 and START_HOUR <= now.hour < END_HOUR):
                        icon.icon = ICON_ACTIVE
                else:
                    logger.error("no state change, sleep change call was unsuccessful")
            else:
                logger.info(f"No state change, still '{last_state}' with working: {working} and stop event not set.")
        else:
            logger.info(f"working: {working} and stop event not set.")

        # If icon object exists but tray is gone → restart it
        if icon and not icon.visible:
            logger.info("Explorer restarted? → restoring tray icon")
            restart_icon()

        logger.info(f"Sleep {CHECK_INTERVAL}s")
        # Wait, but allow early exit
        stop_event.wait(CHECK_INTERVAL)

# --- Icon creation ---
def make_icon(color):
    """Create a circular icon with given color."""
    img = Image.new("RGB", (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return img

ICON_FORCE = make_icon((0, 0, 200))   # blue
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
    global last_state
    logger.info("on_start")
    working = True
    now = datetime.datetime.now()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    if weekday < 5 and START_HOUR <= now.hour < END_HOUR and icon.icon != ICON_WORKTIME:
        icon.icon = ICON_WORKTIME
        disable_sleep()
        last_state = "awake"
    else:
        icon.icon = ICON_ACTIVE
        enable_sleep()
        last_state = "normal"
    update_status(icon)
    logger.info("KeepAwake activated")

def on_force(icon, item):
    global working
    global last_state
    logger.info("on_force")
    if working is True:
        working = False
        disable_sleep()
        last_state = "awake"
        icon.icon = ICON_FORCE
        update_status(icon)
        logger.info("KeepAwake force activated")

def on_stop(icon, item):
    global working
    logger.info("on_stop")
    working = False
    icon.icon = ICON_INACTIVE
    enable_sleep()
    update_status(icon)
    logger.info("KeepAwake deactivated")

def on_exit(icon, item):
    logger.info("on_exit")
    icon.stop()
    stop_event.set()  # signal thread to stop immediately
    update_status(icon)
    logger.info("Exiting KeepAwake")


def restart_icon():
    global icon
    logger.info("restart tray icon")
    if icon:
        try:
            icon.stop()
        except Exception:
            pass
    run_tray(start_worker=False)


def update_status(icon):
    icon.title = f"KeepAwake - {'Running' if working else 'Stopped'}{'' if last_state is None else ' - ' + last_state.capitalize()}"

# --- Tray runner ---
def run_tray(start_worker=True):
    global icon, worker_thread
    logger.info("run_tray()")
    icon = pystray.Icon(
        "keep_awake",
        ICON_ACTIVE if working else ICON_INACTIVE,
        "KeepAwake",
        menu=pystray.Menu(
            pystray.MenuItem("Start", on_start),
            pystray.MenuItem("Stop", on_stop),
            pystray.MenuItem("Force", on_force),
            pystray.MenuItem("Exit", on_exit)
        )
    )
    update_status(icon)  # set initial status

    # Start worker only once
    if start_worker and worker_thread is None:
        logger.info("starting worker thread")
        worker_thread = threading.Thread(target=keep_awake, args=(icon,), daemon=True)
        worker_thread.start()
    icon.run()

# def explorer_monitor():
#     while True:
#         # Look for the "Shell_TrayWnd" window (taskbar)
#         hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
#         if hwnd == 0:  # Explorer not running
#             time.sleep(2)
#             continue
#
#         # If icon object exists but tray is gone → restart it
#         if icon and not icon.visible:
#             logger.info("Explorer restarted → restoring tray icon")
#             restart_icon()
#
#         time.sleep(5)

if __name__ == "__main__":
    #logger.info("starting explorer monitor")
    run_tray()
    #threading.Thread(target=explorer_monitor, daemon=True).start()
