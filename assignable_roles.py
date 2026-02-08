import json
import os
from config import ASSIGNABLE_ROLES_FILE

def load_assignable_roles():
    try:
        if os.path.exists(ASSIGNABLE_ROLES_FILE):
            with open(ASSIGNABLE_ROLES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {str(gid): list(roles) for gid, roles in data.items()}
    except Exception as e:
        print(f"[ERROR] Failed to load assignable roles: {e}")
    return {}

def save_assignable_roles(data):
    try:
        with open(ASSIGNABLE_ROLES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save assignable roles: {e}")

assignable_roles = load_assignable_roles()

def get_assignable_roles(guild_id):
    return list(assignable_roles.get(str(guild_id), []))

def add_assignable_role(guild_id, role_name):
    gid = str(guild_id)
    if gid not in assignable_roles:
        assignable_roles[gid] = []
    role_name = role_name.strip()
    if role_name and role_name not in assignable_roles[gid]:
        assignable_roles[gid].append(role_name)
        save_assignable_roles(assignable_roles)
        return True
    return False

def remove_assignable_role(guild_id, role_name):
    gid = str(guild_id)
    if gid not in assignable_roles:
        return False
    role_name = role_name.strip()
    if role_name in assignable_roles[gid]:
        assignable_roles[gid].remove(role_name)
        save_assignable_roles(assignable_roles)
        return True
    return False
