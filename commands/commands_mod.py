import discord
from discord.ext import commands
from config import bot

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    # delete messages and log to mod-logs
    if amount <= 0:
        await ctx.send("⚠️ Please specify a number greater than 0.")
        return

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        confirmation = await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages.", delete_after=5)

        log_channel = discord.utils.get(ctx.guild.text_channels, name="mod-logs")
        if log_channel:
            await log_channel.send(
                f"🧾 **Message Clear**\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Channel:** {ctx.channel.mention}\n"
                f"**Messages Deleted:** {len(deleted) - 1}"
            )
        else:
            print("[WARN] Could not find #mod-logs channel to log message deletions.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages or access the mod-logs channel.")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")
