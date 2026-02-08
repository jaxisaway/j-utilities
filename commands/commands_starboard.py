import discord
import re
from discord.ext import commands
from config import bot
from starboards_config import starboards, save_starboards
from db import get_db

@bot.command()
@commands.has_permissions(administrator=True)
async def starboard(ctx, board_name: str, subcommand: str, *args):
    # create or delete or configure starboards
    guild_id = str(ctx.guild.id)
    if guild_id not in starboards:
        starboards[guild_id] = {}

    if subcommand == "create":
        if board_name not in starboards[guild_id]:
            starboards[guild_id][board_name] = {}
            save_starboards()
            await ctx.send(f"✅ Starboard '{board_name}' created.")
        else:
            await ctx.send("⚠️ That starboard already exists.")

    elif subcommand == "delete":
        if board_name in starboards[guild_id]:
            del starboards[guild_id][board_name]
            save_starboards()
            await ctx.send(f"🗑️ Deleted starboard '{board_name}'.")
        else:
            await ctx.send("❌ Starboard does not exist.")

    elif subcommand == "add":
        if board_name not in starboards[guild_id]:
            await ctx.send("❌ Starboard not found.")
            return
        if args[0] == "reaction" and len(args) == 3:
            emoji, threshold = args[1], int(args[2])
            starboards[guild_id][board_name][emoji] = starboards[guild_id][board_name].get(emoji, {})
            starboards[guild_id][board_name][emoji]["threshold"] = threshold
            save_starboards()
            await ctx.send(f"⭐ Reaction '{emoji}' set with threshold {threshold} for starboard '{board_name}'.")
        elif args[0] == "channel" and len(args) == 2:
            channel = discord.utils.get(ctx.guild.text_channels, name=args[1]) or ctx.guild.get_channel(int(args[1]))
            if not channel:
                await ctx.send("❌ Channel not found.")
                return
            for emoji in starboards[guild_id][board_name]:
                starboards[guild_id][board_name][emoji]["channel_id"] = channel.id
            save_starboards()
            await ctx.send(f"📌 Channel set to {channel.mention} for starboard '{board_name}'.")

    elif subcommand == "remove":
        if board_name not in starboards[guild_id]:
            await ctx.send("❌ Starboard not found.")
            return
        if args[0] == "reaction" and len(args) == 2:
            emoji = args[1]
            if emoji in starboards[guild_id][board_name]:
                del starboards[guild_id][board_name][emoji]
                save_starboards()
                await ctx.send(f"🧹 Removed emoji '{emoji}' from starboard '{board_name}'.")
            else:
                await ctx.send("⚠️ Emoji not found in that starboard.")
        elif args[0] == "channel":
            for emoji in starboards[guild_id][board_name]:
                if "channel_id" in starboards[guild_id][board_name][emoji]:
                    del starboards[guild_id][board_name][emoji]["channel_id"]
            save_starboards()
            await ctx.send(f"🧼 Removed output channel from starboard '{board_name}'.")

    else:
        await ctx.send("❌ Unknown subcommand.")


@bot.command()
@commands.has_permissions(administrator=True)
async def viewstarboards(ctx):
    # list all starboards and their settings
    guild_id = str(ctx.guild.id)
    if guild_id not in starboards or not starboards[guild_id]:
        await ctx.send("❌ No starboards configured for this server.")
        return

    embed = discord.Embed(
        title=f"⭐ Starboards in {ctx.guild.name}",
        color=discord.Color.gold()
    )

    for board_name, settings in starboards[guild_id].items():
        board_info = []
        for emoji, emoji_settings in settings.items():
            channel = ctx.guild.get_channel(emoji_settings.get("channel_id", 0))
            channel_info = f"→ {channel.mention}" if channel else "→ *No channel set*"
            board_info.append(
                f"**{emoji}** (Threshold: {emoji_settings.get('threshold', 2)}) {channel_info}"
            )
        embed.add_field(
            name=f"📌 {board_name}",
            value="\n".join(board_info) if board_info else "No reactions configured",
            inline=False
        )

    await ctx.send(embed=embed)


@bot.event
async def on_raw_reaction_add(payload):
    # when someone reacts, check if it should go on the starboard
    if payload.guild_id is None:
        return

    guild_id = str(payload.guild_id)

    # check if its souls leaderboard pagination
    from souls_config import souls_data, save_souls
    from commands.commands_souls import build_souls_pages
    if guild_id in souls_data:
        data = souls_data[guild_id]
        if data.get('leaderboard_msg_id') == payload.message_id:
            emoji_str = str(payload.emoji)
            if emoji_str in ["⬅️", "➡️"]:
                guild = bot.get_guild(payload.guild_id)
                channel = bot.get_channel(payload.channel_id)
                if guild and channel:
                    try:
                        message = await channel.fetch_message(payload.message_id)
                        pages = build_souls_pages(guild, data)
                        current = data.get('current_page', 0)
                        if emoji_str == "➡️":
                            current = (current + 1) % len(pages)
                        else:
                            current = (current - 1) % len(pages)
                        data['current_page'] = current
                        save_souls()
                        await message.edit(embed=pages[current])
                        user = await bot.fetch_user(payload.user_id)
                        await message.remove_reaction(payload.emoji, user)
                    except Exception:
                        pass
            return

    # check if its tracker pagination
    from word_tracker_config import tracker_data, save_tracker
    from commands.commands_tracker import build_tracker_pages
    if guild_id in tracker_data:
        data = tracker_data[guild_id]
        if data.get('embed_msg_id') == payload.message_id:
            emoji_str = str(payload.emoji)
            if emoji_str in ["⬅️", "➡️"]:
                guild = bot.get_guild(payload.guild_id)
                channel = bot.get_channel(payload.channel_id)
                if guild and channel:
                    try:
                        message = await channel.fetch_message(payload.message_id)
                        pages = build_tracker_pages(data)
                        current = data.get('current_page', 0)
                        if emoji_str == "➡️":
                            current = (current + 1) % len(pages)
                        else:
                            current = (current - 1) % len(pages)
                        data['current_page'] = current
                        save_tracker()
                        await message.edit(embed=pages[current])
                        user = await bot.fetch_user(payload.user_id)
                        await message.remove_reaction(payload.emoji, user)
                    except Exception:
                        pass
            return

    if guild_id not in starboards:
        return

    for board_name, emoji_map in starboards[guild_id].items():
        emoji_str = str(payload.emoji)
        if emoji_str in emoji_map:
            threshold = emoji_map[emoji_str].get("threshold", 2)
            channel_id = emoji_map[emoji_str].get("channel_id")
            if not channel_id:
                return

            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            reaction_count = 0
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji_str:
                    users = [user async for user in reaction.users() if not user.bot]
                    reaction_count = len(users)
                    break

            if reaction_count < threshold:
                return

            target_channel = bot.get_channel(channel_id)
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'SELECT starboard_msg_id FROM starboard_messages WHERE original_msg_id = ? AND guild_id = ?',
                (message.id, payload.guild_id)
            )
            existing = cursor.fetchone()

            top_line = f"{emoji_str} **{reaction_count}** | https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            embed = discord.Embed(
                description=message.content or "No text",
                color=discord.Color.gold(),
                timestamp=message.created_at
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.set_footer(text="Original message sent")

            if message.attachments:
                embed.set_image(url=message.attachments[0].url)

            if existing:
                try:
                    starboard_msg = await target_channel.fetch_message(existing['starboard_msg_id'])
                    await starboard_msg.edit(content=top_line, embed=embed)
                except discord.NotFound:
                    starboard_msg = await target_channel.send(content=top_line, embed=embed)
                    cursor.execute(
                        'UPDATE starboard_messages SET starboard_msg_id = ? WHERE original_msg_id = ? AND guild_id = ?',
                        (starboard_msg.id, message.id, payload.guild_id)
                    )
                    db.commit()
            else:
                starboard_msg = await target_channel.send(content=top_line, embed=embed)
                cursor.execute(
                    'INSERT INTO starboard_messages VALUES (?, ?, ?)',
                    (message.id, starboard_msg.id, payload.guild_id)
                )
                db.commit()

                # send url previews for new messages that have links
                if message.content and ("http://" in message.content or "https://" in message.content):
                    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', message.content)
                    if urls:
                        await target_channel.send("\n".join(urls))

            db.close()
            return
