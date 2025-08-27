import time
import datetime
import subprocess
import threading
from loguru import logger
import pystray
from PIL import Image, ImageDraw

# --- Logging setup ---
logger.remove()
logger.add("keep_awake.log", rotation="1 day", retention="1 day", level="INFO")

# --- Sleep control ---
running = True
working = True  # whether we keep the PC awake

def disable_sleep():
    subprocess.run(["powercfg", "-change", "-standby-timeout-ac", "0"], shell=True)
    logger.info("Sleep disabled")

def enable_sleep():
    subprocess.run(["powercfg", "-change", "-standby-timeout-ac", "30"], shell=True)
    logger.info("Sleep enabled")


def keep_awake(start_hour=8, end_hour=18):
    logger.info("KeepAwake service started")
    while running:
        logger.info("checking...")
        now = datetime.datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        if working and weekday < 5 and start_hour <= now.hour < end_hour:
            disable_sleep()
        else:
            enable_sleep()
        logger.info("sleep 5min")
        time.sleep(300)  # check every 5 minutes

# --- Icon creation ---
def make_icon(color):
    """Create a circular icon with given color."""
    img = Image.new("RGB", (64, 64), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return img

ICON_ACTIVE = make_icon((0, 200, 0))   # green
ICON_INACTIVE = make_icon((200, 0, 0)) # red

# --- Tray menu actions ---
def on_start(icon, item):
    global working
    working = True
    icon.icon = ICON_ACTIVE
    logger.info("KeepAwake activated")

def on_stop(icon, item):
    global working
    working = False
    icon.icon = ICON_INACTIVE
    logger.info("KeepAwake deactivated")

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
    icon.run()



if __name__ == "__main__":
    # Run background task
    t = threading.Thread(target=keep_awake, daemon=True)
    t.start()

    # Run tray icon
    run_tray()
