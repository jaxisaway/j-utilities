import json
import os
from config import SOULS_FILE

# load souls data from file
def load_souls():
    try:
        if os.path.exists(SOULS_FILE):
            with open(SOULS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
    except Exception as e:
        print(f"[ERROR] Failed to load souls: {e}")
    return {}

# save souls data to file
def save_souls():
    try:
        with open(SOULS_FILE, "w", encoding="utf-8") as f:
            json.dump(souls_data, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save souls: {e}")

# guild_id -> {channel_id, leaderboard_msg_id, soul_bets: {user_id: count}, gamblers: {user_id: count}}
souls_data = load_souls()
