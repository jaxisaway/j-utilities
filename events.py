import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import bot
from gif_roles import gif_block_roles
from birthdays import birthday_check
from souls_config import souls_data, save_souls
from commands.commands_souls import update_souls_leaderboard, process_soul_message
from commands.commands_tracker import process_tracker_message

@bot.event
async def on_ready():
    # start the bot and the birthday scheduler
    print("Bot Online")
    scheduler = AsyncIOScheduler(timezone="US/Pacific")
    scheduler.add_job(birthday_check, "cron", hour=0, minute=0)
    scheduler.start()


@bot.event
async def on_message(message):
    # check if message has gif from blocked role and delete it
    if message.author.bot or not message.guild:
        return

    guild_id = str(message.guild.id)
    target_role_ids = gif_block_roles.get(guild_id, [])

    has_blocked_role = any(role.id in target_role_ids for role in message.author.roles)

    if has_blocked_role:
        # check attachments for gifs
        for attachment in message.attachments:
            if attachment.content_type == "image/gif" or attachment.filename.endswith(".gif"):
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n{message.content}")
                return

        # check embeds for gifs
        for embed in message.embeds:
            if embed.image and embed.image.url and ".gif" in embed.image.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed image)")
                return
            if embed.video and embed.video.url and ".gif" in embed.video.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed video)")
                return
            if embed.url and ".gif" in embed.url:
                await message.delete()
                log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
                if log_channel:
                    await log_channel.send(f"🧹 Deleted GIF from {message.author.mention} in {message.channel.mention}:\n(embed URL)")
                return

        # check for tenor links
        if "https://tenor.com" in message.content.lower():
            await message.delete()
            log_channel = discord.utils.get(message.guild.text_channels, name="mod-logs")
            if log_channel:
                await log_channel.send(f"🧹 Deleted Tenor link from {message.author.mention} in {message.channel.mention}:\n{message.content}")
            return

    # check for souls bets
    guild_id = str(message.guild.id)
    if guild_id in souls_data:
        data = souls_data[guild_id]
        count = await process_soul_message(message, data)
        if count > 0:
            save_souls()
            await update_souls_leaderboard(bot, guild_id)

    # check for word tracker
    await process_tracker_message(message)

    await bot.process_commands(message)
