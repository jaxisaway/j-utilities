import json
import os
from config import GIF_ROLE_FILE

# save the gif block roles to the json file
def save_gif_roles():
    try:
        with open(GIF_ROLE_FILE, "w", encoding="utf-8") as f:
            json.dump(gif_block_roles, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Failed to save roles: {e}")

# load the gif block roles from the json file
def load_gif_roles():
    try:
        if os.path.exists(GIF_ROLE_FILE):
            with open(GIF_ROLE_FILE, "r", encoding="utf-8") as f:
                roles = json.load(f)
                return {str(guild_id): role_ids for guild_id, role_ids in roles.items()}
        else:
            return {}
    except Exception as e:
        print(f"[ERROR] Error reading the JSON file: {e}")
        return {}

# the actual dict that holds which roles block gifs
gif_block_roles = load_gif_roles()
