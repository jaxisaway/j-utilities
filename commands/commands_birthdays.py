import discord
import asyncio
import re
from datetime import datetime
from collections import defaultdict
from discord.ext import commands
from config import bot
from birthdays import load_birthdays, save_birthdays, set_birthday_channel, clear_birthday_channel

def _build_birthday_by_month(guild, raw):
    """Build { month: [(date, name), ...] } from load_birthdays() result."""
    birthday_by_month = defaultdict(list)
    users = raw.get("users", {})
    legacy = raw.get("legacy", {})
    for uid, date in users.items():
        month = int(date.split("-")[0])
        member = guild.get_member(int(uid))
        name = member.display_name if member else str(uid)
        birthday_by_month[month].append((date, name))
    for date, names in legacy.items():
        month = int(date.split("-")[0])
        for name in names:
            birthday_by_month[month].append((date, name))
    return birthday_by_month

def _validate_date(s):
    """Return True if s is MM-DD (01-12, 01-31)."""
    if not re.match(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$", s):
        return False
    return True

@bot.group(name="birthday", invoke_without_command=True)
async def birthday_group(ctx):
    await ctx.send("Use `!birthday add <name> MM-DD`, `!birthday remove <name>`, or `!birthday channel #channel`. List: `!birthdays`")

@birthday_group.command(name="add")
async def birthday_add(ctx, *, args: str):
    """Add a birthday by name. Usage: !birthday add <name> MM-DD"""
    parts = args.strip().rsplit(maxsplit=1)
    if len(parts) != 2:
        await ctx.send("⚠️ Use: `!birthday add <name> MM-DD` (e.g. `!birthday add Jackie 06-12`).")
        return
    name, date = parts
    name = name.strip()
    if not name:
        await ctx.send("⚠️ Use: `!birthday add <name> MM-DD`.")
        return
    if not _validate_date(date):
        await ctx.send("⚠️ Use date format **MM-DD** (e.g. `06-12`).")
        return
    raw = load_birthdays()
    raw.setdefault("legacy", {})
    raw["legacy"].setdefault(date, [])
    if name not in raw["legacy"][date]:
        raw["legacy"][date].append(name)
    save_birthdays(raw)
    await ctx.send(f"✅ Birthday for **{name}** set to **{date}**.")

@birthday_group.command(name="channel")
@commands.has_permissions(administrator=True)
async def birthday_channel_cmd(ctx, *, args: str = ""):
    """Set or clear the channel for birthday announcements (admin only). !birthday channel #channel to set, !birthday channel clear to clear."""
    args = args.strip().lower()
    if not args or args == "clear":
        clear_birthday_channel(ctx.guild.id)
        await ctx.send("✅ Birthday announcement channel cleared. Set one with `!birthday channel #channel`.")
        return
    channel = None
    if args.startswith("<#") and args.endswith(">"):
        try:
            cid = int(args[2:-1])
            channel = ctx.guild.get_channel(cid)
        except ValueError:
            pass
    if not channel:
        channel = discord.utils.get(ctx.guild.text_channels, name=args)
    if not channel:
        await ctx.send("❌ Channel not found. Use a #mention or channel name.")
        return
    set_birthday_channel(ctx.guild.id, channel.id)
    await ctx.send(f"✅ Birthday announcements will be sent to {channel.mention}.")

@birthday_group.command(name="remove")
async def birthday_remove(ctx, *, name: str):
    """Remove a birthday by name (plain string)."""
    name = name.strip()
    if not name:
        await ctx.send("⚠️ Use: `!birthday remove <name>`.")
        return
    raw = load_birthdays()
    legacy = raw.get("legacy", {})
    removed = False
    for date in list(legacy.keys()):
        if name in legacy[date]:
            legacy[date].remove(name)
            removed = True
        if not legacy[date]:
            del legacy[date]
    if not removed:
        await ctx.send(f"⚠️ **{name}** doesn't have a birthday set.")
        return
    save_birthdays(raw)
    await ctx.send(f"✅ Birthday removed for **{name}**.")

@bot.command()
async def birthdays(ctx):
    # show all birthdays in a paginated list
    raw = load_birthdays()
    birthday_by_month = _build_birthday_by_month(ctx.guild, raw)

    months = [
        ("January", "⛄"), ("February", "💌"), ("March", "🍀"), ("April", "☂️"),
        ("May", "🌷"), ("June", "🏖️"), ("July", "🎆"), ("August", "📚"),
        ("September", "🍁"), ("October", "🎃"), ("November", "🦃"), ("December", "🎄")
    ]

    pages = []
    for i, (month_name, emoji) in enumerate(months, start=1):
        entries = birthday_by_month.get(i, [])
        description = "\n".join([f"- {name} — {datetime.strptime(date, '%m-%d').strftime('%b %d')}" for date, name in sorted(entries)]) or "*No birthdays this month.*"
        embed = discord.Embed(
            title=f"🎂 Birthdays — {month_name} {emoji}",
            description=description,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Page {i} of {len(months)}")
        pages.append(embed)

    current_month = datetime.now().month
    current_page = current_month - 1
    message = await ctx.send(embed=pages[current_page])

    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "➡️":
                current_page = (current_page + 1) % len(pages)
            elif str(reaction.emoji) == "⬅️":
                current_page = (current_page - 1) % len(pages)
            await message.edit(embed=pages[current_page])
            await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break
