import discord
from discord.ext import commands

# stuff the bot needs to run
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# file paths
GIF_ROLE_FILE = "gif_roles.json"
STARBOARD_FILE = "starboards.json"
BIRTHDAY_FILE = "birthdays.json"
BIRTHDAY_CHANNELS_FILE = "birthday_channels.json"
SOULS_FILE = "souls.json"
TRACKER_FILE = "word_tracker.json"
ASSIGNABLE_ROLES_FILE = "assignable_roles.json"
