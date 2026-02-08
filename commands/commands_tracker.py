import discord
import re
import asyncio
from discord.ext import commands
from config import bot
from word_tracker_config import tracker_data, save_tracker

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

# parse a string into tokens, respecting single- and double-quoted phrases
def parse_quoted_args(s):
    s = s.strip()
    out = []
    i = 0
    while i < len(s):
        while i < len(s) and s[i] in " \t":
            i += 1
        if i >= len(s):
            break
        if s[i] in "\"'":
            quote = s[i]
            i += 1
            start = i
            while i < len(s) and s[i] != quote:
                i += 1
            out.append(s[start:i])
            if i < len(s):
                i += 1
        else:
            start = i
            while i < len(s) and s[i] not in " \t\"'":
                i += 1
            out.append(s[start:i])
    return out

# build regex pattern for a phrase (word boundaries, case insensitive)
def phrase_to_regex(phrase):
    parts = phrase.split()
    pattern = r"\b" + r"\s+".join(re.escape(p) for p in parts) + r"\b"
    return re.compile(pattern, re.IGNORECASE)

# count how many times tracked phrases appear in text
def count_phrases_in_text(text, words_map):
    if not text:
        return {}
    counts = {}
    for main_word, phrases in words_map.items():
        total = 0
        for phrase in phrases:
            pattern = phrase_to_regex(phrase)
            matches = pattern.findall(text)
            total += len(matches)
        if total > 0:
            counts[main_word] = counts.get(main_word, 0) + total
    return counts

# build all tracker embed pages
def build_tracker_pages(data):
    words_map = data.get('words', {})
    counts = data.get('counts', {})
    sorted_words = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    if not sorted_words:
        sorted_words = [(w, 0) for w in words_map.keys()]

    pages = []
    entries_per_page = 12

    for i in range(0, len(sorted_words), entries_per_page):
        chunk = sorted_words[i:i + entries_per_page]
        lines = []
        for rank, (word, count) in enumerate(chunk, start=i + 1):
            lines.append(f"{word} — {num_to_emoji(count)}")
        desc = "\n".join(lines) if lines else "*no words tracked yet*"
        embed = discord.Embed(
            title="📊 word tracker",
            description=desc,
            color=discord.Color.teal()
        )
        total_pages = (len(sorted_words) + entries_per_page - 1) // entries_per_page or 1
        page_num = (i // entries_per_page) + 1
        embed.set_footer(text=f"page {page_num} of {total_pages}")
        pages.append(embed)

    if not pages:
        embed = discord.Embed(
            title="📊 word tracker",
            description="*no words tracked yet*\n\nuse `!tracker add <word> <alt1> <alt2>` to add words",
            color=discord.Color.teal()
        )
        embed.set_footer(text="page 1 of 1")
        pages = [embed]

    return pages

# update the tracker embed in the channel
async def update_tracker_embed(bot, guild_id):
    guild_id_str = str(guild_id)
    if guild_id_str not in tracker_data:
        return
    data = tracker_data[guild_id_str]
    channel_id = data.get('channel_id')
    msg_id = data.get('embed_msg_id')
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
        pages = build_tracker_pages(data)
        current_page = data.get('current_page', 0)
        if current_page >= len(pages):
            current_page = 0
        await message.edit(embed=pages[current_page])
    except discord.NotFound:
        data['embed_msg_id'] = None
        save_tracker()
    except Exception as e:
        print(f"[ERROR] Failed to update tracker: {e}")

# process a message and update counts
async def process_tracker_message(message):
    if message.author.bot or not message.guild:
        return

    guild_id = str(message.guild.id)
    if guild_id not in tracker_data:
        return

    data = tracker_data[guild_id]
    words_map = data.get('words', {})
    if not words_map:
        return

    counts = count_phrases_in_text(message.content, words_map)
    if counts:
        if 'counts' not in data:
            data['counts'] = {}
        for word, add in counts.items():
            data['counts'][word] = data['counts'].get(word, 0) + add
        save_tracker()
        await update_tracker_embed(bot, guild_id)

# retroactive scan of channel history
async def retroactive_scan(guild_id, limit_per_channel=1000, progress_msg=None):
    guild_id_str = str(guild_id)
    if guild_id_str not in tracker_data:
        return 0

    data = tracker_data[guild_id_str]
    words_map = data.get('words', {})
    if not words_map:
        return 0

    guild = bot.get_guild(int(guild_id))
    if not guild:
        return 0

    total_counted = 0
    if 'counts' not in data:
        data['counts'] = {}

    text_channels = [c for c in guild.text_channels if c.permissions_for(guild.me).read_message_history]
    total_channels = len(text_channels)
    print(f"[tracker scan] starting scan of {total_channels} channels...", flush=True)

    for i, channel in enumerate(text_channels):
        try:
            msg_count = 0
            async for msg in channel.history(limit=limit_per_channel):
                if msg.author.bot:
                    continue
                counts = count_phrases_in_text(msg.content, words_map)
                for word, add in counts.items():
                    data['counts'][word] = data['counts'].get(word, 0) + add
                    total_counted += add
                msg_count += 1
                if msg_count % 500 == 0:
                    await asyncio.sleep(1)
        except discord.Forbidden:
            continue
        except discord.HTTPException as e:
            if e.status == 429:
                print(f"[tracker scan] rate limited, waiting 5s...", flush=True)
                await asyncio.sleep(5)
            else:
                print(f"[ERROR] Tracker scan failed for {channel.name}: {e}")
        except Exception as e:
            print(f"[ERROR] Tracker scan failed for {channel.name}: {e}")
        if progress_msg and (i + 1) % 3 == 0:
            try:
                await progress_msg.edit(content=f"🔄 scanning... ({i + 1}/{total_channels} channels, {total_counted} matches so far)")
            except Exception:
                pass
        await asyncio.sleep(2)

    save_tracker()
    print(f"[tracker scan] done, found {total_counted} matches", flush=True)
    return total_counted

@bot.command()
@commands.has_permissions(administrator=True)
async def tracker(ctx, subcommand: str = None, *args):
    # set up word tracker
    guild_id = str(ctx.guild.id)

    if subcommand == "channel" and args:
        channel = None
        arg = args[0]
        if arg.startswith('<#') and arg.endswith('>'):
            try:
                cid = int(arg[2:-1])
                channel = ctx.guild.get_channel(cid)
            except ValueError:
                pass
        if not channel:
            channel = discord.utils.get(ctx.guild.text_channels, name=arg)
        if not channel:
            try:
                channel = ctx.guild.get_channel(int(arg))
            except ValueError:
                pass
        if not channel:
            await ctx.send("❌ channel not found")
            return

        if guild_id not in tracker_data:
            tracker_data[guild_id] = {
                'channel_id': channel.id,
                'embed_msg_id': None,
                'words': {},
                'counts': {},
                'current_page': 0
            }
        else:
            tracker_data[guild_id]['channel_id'] = channel.id

        data = tracker_data[guild_id]
        pages = build_tracker_pages(data)
        msg = await channel.send(embed=pages[0])
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        data['embed_msg_id'] = msg.id
        data['current_page'] = 0
        save_tracker()

        await ctx.send(f"✅ tracker set to {channel.mention}")

    elif subcommand == "add" and args:
        if guild_id not in tracker_data:
            await ctx.send("⚠️ set up tracker with `!tracker channel #channel` first")
            return
        args_str = " ".join(args)
        parsed = parse_quoted_args(args_str)
        if not parsed:
            await ctx.send("⚠️ Use: `!tracker add <phrase> <alt1> ...` — use quotes for multi-word phrases, e.g. `!tracker add 'lock in' lockin`")
            return
        main_word = parsed[0].lower().strip()
        alts = [p.lower().strip() for p in parsed[1:]] if len(parsed) > 1 else [main_word]
        data = tracker_data[guild_id]
        if "words" not in data:
            data["words"] = {}
        data["words"][main_word] = list(set([main_word] + alts))
        if main_word not in data.get("counts", {}):
            data["counts"][main_word] = 0
        save_tracker()
        await update_tracker_embed(bot, guild_id)
        await ctx.send(f"✅ added *{main_word}* with alts: {', '.join(alts)}")

    elif subcommand == "remove" and args:
        if guild_id not in tracker_data:
            await ctx.send("⚠️ no tracker set up here")
            return
        args_str = " ".join(args)
        parsed = parse_quoted_args(args_str)
        if not parsed:
            await ctx.send("⚠️ Use: `!tracker remove <phrase>` — use quotes for multi-word, e.g. `!tracker remove 'lock in'`")
            return
        word = parsed[0].lower().strip()
        data = tracker_data[guild_id]
        if word in data.get("words", {}):
            del data["words"][word]
            if word in data.get("counts", {}):
                del data["counts"][word]
            save_tracker()
            await update_tracker_embed(bot, guild_id)
            await ctx.send(f"✅ removed *{word}*")
        else:
            await ctx.send("⚠️ phrase not in tracker")

    elif subcommand == "scan":
        if guild_id not in tracker_data:
            await ctx.send("⚠️ set up tracker with `!tracker channel #channel` first")
            return
        print("[tracker scan] command received, starting...", flush=True)
        msg = await ctx.send("🔄 scanning message history... (this can take a few min)")
        try:
            total = await retroactive_scan(guild_id, progress_msg=msg)
        except Exception as e:
            print(f"[tracker scan] ERROR: {e}")
            await ctx.send(f"⚠️ scan failed: {e}")
            return
        try:
            await msg.edit(content=f"✅ scan done, found {total} matches")
        except discord.NotFound:
            await ctx.send(f"✅ scan done, found {total} matches")

    elif subcommand == "list":
        if guild_id not in tracker_data:
            await ctx.send("⚠️ no tracker set up here. Use `!tracker channel #channel` first.")
            return
        data = tracker_data[guild_id]
        words_map = data.get('words', {})
        counts = data.get('counts', {})
        if not words_map:
            await ctx.send("📋 **Tracked words:** *none yet* — use `!tracker add <word> <alt1> <alt2>` to add.")
            return
        lines = []
        for main_word in sorted(words_map.keys()):
            alts = words_map[main_word]
            count = counts.get(main_word, 0)
            other_alts = [a for a in alts if a != main_word]
            alt_str = f" (alts: {', '.join(other_alts)})" if other_alts else ""
            lines.append(f"• **{main_word}** — {count} matches{alt_str}")
        await ctx.send("📋 **Tracked words:**\n" + "\n".join(lines))

    elif subcommand == "remove" and not args:
        await ctx.send("usage: `!tracker remove <word>`")

    else:
        await ctx.send(
            "usage:\n"
            "`!tracker channel #channel` — set tracker channel\n"
            "`!tracker add <phrase> <alt1> ...` — add phrase (use 'quotes' for multi-word)\n"
            "`!tracker remove <phrase>` — remove phrase\n"
            "`!tracker list` — list tracked words\n"
            "`!tracker scan` — scan past messages"
        )
