import json
import os
from datetime import datetime
from pytz import timezone
from config import BIRTHDAY_FILE, BIRTHDAY_CHANNELS_FILE, bot

# per-guild birthday announcement channels: { guild_id: channel_id }
def load_birthday_channels():
    try:
        if os.path.exists(BIRTHDAY_CHANNELS_FILE):
            with open(BIRTHDAY_CHANNELS_FILE, "r", encoding="utf-8") as f:
                return {str(gid): int(cid) for gid, cid in json.load(f).items()}
    except Exception as e:
        print(f"[ERROR] Failed to load birthday channels: {e}")
    return {}

def save_birthday_channels(data):
    try:
        with open(BIRTHDAY_CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save birthday channels: {e}")

birthday_channels = load_birthday_channels()

def set_birthday_channel(guild_id, channel_id):
    """Set the birthday announcement channel for a guild."""
    birthday_channels[str(guild_id)] = int(channel_id)
    save_birthday_channels(birthday_channels)

def clear_birthday_channel(guild_id):
    """Clear the birthday announcement channel for a guild."""
    gid = str(guild_id)
    if gid in birthday_channels:
        del birthday_channels[gid]
        save_birthday_channels(birthday_channels)

# load birthdays from the json file
# returns dict with "users" { user_id: "MM-DD" } and optionally "legacy" { "MM-DD": [names] }
def load_birthdays():
    try:
        with open(BIRTHDAY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load birthdays: {e}")
        return {"users": {}, "legacy": {}}

    if "users" in data:
        return {"users": data.get("users", {}), "legacy": data.get("legacy", {})}
    # legacy format: { "MM-DD": ["name1", ...] }
    return {"users": {}, "legacy": data if isinstance(data, dict) else {}}

def save_birthdays(data):
    try:
        with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save birthdays: {e}")

# check if its anyones birthday and send a message (to each guild that has a channel set)
async def birthday_check():
    now = datetime.now(timezone("US/Pacific"))
    today = now.strftime("%m-%d")
    raw = load_birthdays()
    users = raw.get("users", {})
    legacy = raw.get("legacy", {})

    today_names = []
    for uid, date in users.items():
        if date == today:
            today_names.append((uid, date, "user"))
    if today in legacy:
        for name in legacy[today]:
            today_names.append((name, today, "legacy"))

    if not today_names:
        return

    for guild_id, channel_id in list(birthday_channels.items()):
        channel = bot.get_channel(channel_id)
        if not channel:
            continue
        guild = channel.guild
        for item in today_names:
            if item[2] == "user":
                uid, date, _ = item
                member = guild.get_member(int(uid))
                name = member.display_name if member else f"User {uid}"
            else:
                name = item[0]
            await channel.send(f"🎈 merry birthday to **{name}**!")
