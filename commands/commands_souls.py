import discord
import re
import asyncio
from typing import Union
from discord.ext import commands
from config import bot
from souls_config import souls_data, save_souls

# process a single message for soul bets, update data in place. returns count of soul bets found
async def process_soul_message(message, data):
    if message.author.bot or not message.guild:
        return 0
    matches = []
    matches.extend(re.findall(r"\bon\s+(\w+?)(?:'s|s)?\s+soul\b", message.content, re.IGNORECASE))
    matches.extend(re.findall(r"\bword\s+to\s+my\s+(\w+?)(?:'s|s)?\b", message.content, re.IGNORECASE))
    if not matches:
        return 0
    if 'soul_bets' not in data:
        data['soul_bets'] = {}
    if 'gamblers' not in data:
        data['gamblers'] = {}
    if 'nicknames' not in data:
        data['nicknames'] = {}
    if 'last_nick' not in data:
        data['last_nick'] = {}
    gambler_id = str(message.author.id)
    data['gamblers'][gambler_id] = data['gamblers'].get(gambler_id, 0) + 1
    count = 0
    for name in matches:
        name_lower = name.lower().strip()
        if not name_lower:
            continue
        uid = None
        nicknames = data.get('nicknames', {})
        if name_lower in nicknames:
            uid = nicknames[name_lower]
        if not uid:
            # try cache first
            member = discord.utils.find(
                lambda m: (m.display_name and m.display_name.lower() == name_lower)
                or (m.global_name and m.global_name.lower() == name_lower)
                or (m.name and m.name.lower() == name_lower),
                message.guild.members
            )
            if not member and len(name_lower) >= 2:
                # not in cache - search server (works for past messages / offline members)
                try:
                    queried = await message.guild.query_members(name_lower, limit=15)
                    member = discord.utils.find(
                        lambda m: (m.display_name and m.display_name.lower() == name_lower)
                        or (m.global_name and m.global_name.lower() == name_lower)
                        or (m.name and m.name.lower() == name_lower),
                        queried
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass
            if member:
                uid = str(member.id)
        if uid:
            data['soul_bets'][uid] = data['soul_bets'].get(uid, 0) + 1
            data['last_nick'][uid] = name_lower
            count += 1
    return count

# convert number to emoji digits
EMOJI_DIGITS = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

def num_to_emoji(n):
    if n == 0:
        return '0️⃣'
    s = ''
    while n > 0:
        s = EMOJI_DIGITS[n % 10] + s
        n //= 10
    return s

# build all leaderboard pages
def build_souls_pages(guild, data):
    soul_bets = data.get('soul_bets', {})
    gamblers = data.get('gamblers', {})

    # only real user ids (numeric) - skip bogus keys like "name:someone" from old scans
    soul_bets_valid = {k: v for k, v in soul_bets.items() if k.isdigit()}
    soul_sorted = sorted(soul_bets_valid.items(), key=lambda x: x[1], reverse=True)
    gambler_sorted = sorted(gamblers.items(), key=lambda x: x[1], reverse=True)

    pages = []
    entries_per_page = 15

    # lost souls section
    soul_title = "lost souls"
    last_nick = data.get('last_nick', {})
    for i in range(0, len(soul_sorted), entries_per_page):
        chunk = soul_sorted[i:i + entries_per_page]
        lines = []
        for rank, (uid, count) in enumerate(chunk, start=i + 1):
            name = last_nick.get(uid)
            if not name:
                member = guild.get_member(int(uid))
                name = member.display_name if member else str(uid)
            else:
                name = name.capitalize()
            lines.append(f"{name} — {num_to_emoji(count)}")
        desc = "\n".join(lines) if lines else "*no souls gambled yet*"
        embed = discord.Embed(
            title=f"🙇‍♀️ {soul_title}",
            description=desc,
            color=discord.Color.dark_purple()
        )
        total_soul_pages = (len(soul_sorted) + entries_per_page - 1) // entries_per_page or 1
        soul_page_num = (i // entries_per_page) + 1
        embed.set_footer(text=f"souls page {soul_page_num} of {total_soul_pages}")
        pages.append(embed)

    # most souls bet section
    gambler_title = "most souls bet"
    for i in range(0, len(gambler_sorted), entries_per_page):
        chunk = gambler_sorted[i:i + entries_per_page]
        lines = []
        for rank, (uid, count) in enumerate(chunk, start=i + 1):
            member = guild.get_member(int(uid))
            name = member.display_name if member else str(uid)
            lines.append(f"{name} — {num_to_emoji(count)} souls bet")
        desc = "\n".join(lines) if lines else "*no gamblers yet*"
        embed = discord.Embed(
            title=f"🎲 {gambler_title}",
            description=desc,
            color=discord.Color.dark_gold()
        )
        total_gambler_pages = (len(gambler_sorted) + entries_per_page - 1) // entries_per_page or 1
        gambler_page_num = (i // entries_per_page) + 1
        embed.set_footer(text=f"betters page {gambler_page_num} of {total_gambler_pages}")
        pages.append(embed)

    if not pages:
        embed = discord.Embed(
            title="👻 souls leaderboard",
            description="*no souls gambled yet*\n\nsay things like \"on jax's soul\" to get started",
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="page 1 of 1")
        pages = [embed]

    return pages

# update the leaderboard message in the channel
async def update_souls_leaderboard(bot, guild_id):
    guild_id_str = str(guild_id)
    if guild_id_str not in souls_data:
        return
    data = souls_data[guild_id_str]
    channel_id = data.get('channel_id')
    msg_id = data.get('leaderboard_msg_id')
    if not channel_id or not msg_id:
        return

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    try:
        message = await channel.fetch_message(int(msg_id))
        pages = build_souls_pages(guild, data)
        current_page = data.get('current_page', 0)
        if current_page >= len(pages):
            current_page = 0
        await message.edit(embed=pages[current_page])
    except Exception as e:
        print(f"[ERROR] Failed to update souls leaderboard: {e}")

# retroactive scan of channel history for soul bets
async def retroactive_souls_scan(guild_id, limit_per_channel=1000, progress_msg=None):
    guild_id_str = str(guild_id)
    if guild_id_str not in souls_data:
        return 0
    data = souls_data[guild_id_str]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return 0
    # skip guild.chunk() - it hangs on large servers. nicknames will still work
    total_counted = 0
    text_channels = [c for c in guild.text_channels if c.permissions_for(guild.me).read_message_history]
    print(f"[souls scan] starting scan of {len(text_channels)} channels...", flush=True)
    total_channels = len(text_channels)
    for i, channel in enumerate(text_channels):
        try:
            msg_count = 0
            async for msg in channel.history(limit=limit_per_channel):
                if msg.author.bot:
                    continue
                count = await process_soul_message(msg, data)
                total_counted += count
                msg_count += 1
                if msg_count % 500 == 0:
                    await asyncio.sleep(1)
        except discord.Forbidden:
            continue
        except discord.HTTPException as e:
            if e.status == 429:
                print(f"[souls scan] rate limited, waiting 5s...", flush=True)
                await asyncio.sleep(5)
            else:
                print(f"[ERROR] Souls scan failed for {channel.name}: {e}")
        except Exception as e:
            print(f"[ERROR] Souls scan failed for {channel.name}: {e}")
        if progress_msg and (i + 1) % 3 == 0:
            try:
                await progress_msg.edit(content=f"🔄 scanning... ({i + 1}/{total_channels} channels, {total_counted} soul bets so far)")
            except Exception:
                pass
        await asyncio.sleep(2)
    save_souls()
    print(f"[souls scan] done, found {total_counted} soul bets", flush=True)
    return total_counted

@bot.command()
@commands.has_permissions(administrator=True)
async def souls(ctx, subcommand: str = None, target: Union[discord.Member, discord.TextChannel] = None, *nicks: str):
    # set up or remove souls tracking
    guild_id = str(ctx.guild.id)

    if subcommand == "channel" and isinstance(target, discord.TextChannel):
        channel = target
        if guild_id not in souls_data:
            souls_data[guild_id] = {
                'channel_id': channel.id,
                'leaderboard_msg_id': None,
                'soul_bets': {},
                'gamblers': {},
                'nicknames': {},
                'last_nick': {},
                'current_page': 0
            }
        else:
            souls_data[guild_id]['channel_id'] = channel.id

        # send initial leaderboard
        data = souls_data[guild_id]
        pages = build_souls_pages(ctx.guild, data)
        msg = await channel.send(embed=pages[0])
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        data['leaderboard_msg_id'] = msg.id
        data['current_page'] = 0
        save_souls()

        await ctx.send(f"✅ souls leaderboard set to {channel.mention}")

    elif subcommand == "remove":
        if guild_id in souls_data:
            del souls_data[guild_id]
            save_souls()
            await ctx.send("🗑️ souls tracking removed from this server")
        else:
            await ctx.send("⚠️ no souls tracking set up here")

    elif subcommand == "refresh":
        if guild_id in souls_data:
            await update_souls_leaderboard(bot, guild_id)
            await ctx.send("🔄 leaderboard refreshed")
        else:
            await ctx.send("⚠️ no souls tracking set up here")

    elif subcommand == "scan":
        if guild_id not in souls_data:
            await ctx.send("⚠️ set up souls with `!souls channel #channel` first")
            return
        print("[souls scan] command received, starting...", flush=True)
        msg = await ctx.send("🔄 scanning message history for souls... (this can take a few min)")
        try:
            total = await retroactive_souls_scan(guild_id, progress_msg=msg)
        except Exception as e:
            print(f"[souls scan] ERROR: {e}")
            await ctx.send(f"⚠️ scan failed: {e}")
            return
        try:
            await msg.edit(content=f"✅ scan done, found {total} soul bets")
        except discord.NotFound:
            await ctx.send(f"✅ scan done, found {total} soul bets")
        await update_souls_leaderboard(bot, guild_id)

    elif subcommand == "addnick" and isinstance(target, discord.Member) and nicks:
        if guild_id not in souls_data:
            await ctx.send("⚠️ set up souls with `!souls channel #channel` first")
            return
        data = souls_data[guild_id]
        if 'nicknames' not in data:
            data['nicknames'] = {}
        uid = str(target.id)
        for nick in nicks:
            data['nicknames'][nick.lower()] = uid
        save_souls()
        await ctx.send(f"✅ added nicknames for {target.display_name}: {', '.join(nicks)}")

    elif subcommand == "addnick":
        await ctx.send("usage: `!souls addnick @user nick1 nick2 nick3`")

    else:
        await ctx.send("usage: `!souls channel #channel` to set up, `!souls remove` to remove, `!souls refresh` to refresh, `!souls scan` to scan past messages, `!souls addnick @user nick1 nick2` to add nicknames")
