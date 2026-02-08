import json
import os
from config import TRACKER_FILE

# load tracker data from file
def load_tracker():
    try:
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
    except Exception as e:
        print(f"[ERROR] Failed to load tracker: {e}")
    return {}

# save tracker data to file
def save_tracker():
    try:
        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(tracker_data, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save tracker: {e}")

# guild_id -> {channel_id, embed_msg_id, words: {main: [alts]}, counts: {main: n}, current_page}
tracker_data = load_tracker()
