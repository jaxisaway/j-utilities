import json
import os
from config import STARBOARD_FILE

# load starboard config from file
def load_starboards():
    try:
        if os.path.exists(STARBOARD_FILE):
            with open(STARBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
    except Exception as e:
        print(f"[ERROR] Failed to load starboards: {e}")
    return {}

# save starboard config to file
def save_starboards():
    try:
        with open(STARBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(starboards, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save starboards: {e}")

# the actual dict that holds starboard settings
starboards = load_starboards()
