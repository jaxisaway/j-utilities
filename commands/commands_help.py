import discord
import asyncio
from config import bot

@bot.command(name="help")
async def help_command(ctx):
    # show help with page navigation
    gif_commands = discord.Embed(
        title="📘 GIF Management",
        color=discord.Color.red()
    )
    gif_commands.add_field(
        name="!showgifblockrole",
        value="Shows which roles are blocked from sending GIFs",
        inline=False
    )
    gif_commands.add_field(
        name="!setgifblockrole @Role",
        value="Blocks GIFs from members with the specified role",
        inline=False
    )
    gif_commands.add_field(
        name="!removegifblockrole @Role",
        value="Removes GIF block from the specified role",
        inline=False
    )
    gif_commands.set_footer(text="Admins only · Page 1 of 7")

    role_commands = discord.Embed(
        title="📘 Role Management",
        color=discord.Color.green()
    )
    role_commands.add_field(
        name="!addrole <name>",
        value="Adds an allowed role to yourself",
        inline=False
    )
    role_commands.add_field(
        name="!removerole <name>",
        value="Removes an allowed role from yourself",
        inline=False
    )
    role_commands.add_field(
        name="!viewroles",
        value="Shows list of self-assignable roles",
        inline=False
    )
    role_commands.add_field(
        name="!assignablerole add <name>",
        value="Add a role to the self-assignable list (admins only)",
        inline=False
    )
    role_commands.add_field(
        name="!assignablerole remove <name>",
        value="Remove a role from the self-assignable list (admins only)",
        inline=False
    )
    role_commands.set_footer(text="Page 2 of 7")

    starboard_commands = discord.Embed(
        title="📘 Starboard",
        color=discord.Color.gold()
    )
    starboard_commands.add_field(
        name="!starboard <name> create",
        value="Creates a new starboard",
        inline=False
    )
    starboard_commands.add_field(
        name="!starboard <name> delete",
        value="Deletes a starboard",
        inline=False
    )
    starboard_commands.add_field(
        name="!starboard <name> add reaction <emoji> <threshold>",
        value="Adds a reaction to track with a minimum threshold",
        inline=False
    )
    starboard_commands.add_field(
        name="!starboard <name> add channel <channel>",
        value="Sets the channel where starred messages appear",
        inline=False
    )
    starboard_commands.add_field(
        name="!starboard <name> remove reaction <emoji>",
        value="Removes a reaction from the starboard",
        inline=False
    )
    starboard_commands.add_field(
        name="!starboard <name> remove channel",
        value="Removes the output channel",
        inline=False
    )
    starboard_commands.add_field(
        name="!viewstarboards",
        value="Lists all starboards and their settings",
        inline=False
    )
    starboard_commands.set_footer(text="Admins only · Page 3 of 7")

    souls_commands = discord.Embed(
        title="📘 Souls Leaderboard",
        color=discord.Color.dark_purple()
    )
    souls_commands.add_field(
        name="!souls channel #channel",
        value="Sets the channel for the souls leaderboard",
        inline=False
    )
    souls_commands.add_field(
        name="!souls addnick @user nick1 nick2",
        value="Adds nicknames so multiple names count for the same person",
        inline=False
    )
    souls_commands.add_field(
        name="!souls remove",
        value="Removes souls tracking from this server",
        inline=False
    )
    souls_commands.add_field(
        name="!souls refresh",
        value="Refreshes the leaderboard display",
        inline=False
    )
    souls_commands.add_field(
        name="!souls scan",
        value="Scans past messages to count soul bets retroactively",
        inline=False
    )
    souls_commands.add_field(
        name="What is this?",
        value="Tracks messages that say *on [name]'s soul* or *word to my [name]*",
        inline=False
    )
    souls_commands.set_footer(text="Admins only · Page 4 of 7")

    tracker_commands = discord.Embed(
        title="📘 Word Tracker",
        color=discord.Color.teal()
    )
    tracker_commands.add_field(
        name="!tracker channel #channel",
        value="Sets the channel for the word tracker embed",
        inline=False
    )
    tracker_commands.add_field(
        name="!tracker add <phrase> <alt1> ...",
        value="Adds a word/phrase to track. Use 'quotes' for multi-word phrases (e.g. `!tracker add 'lock in' lockin`)",
        inline=False
    )
    tracker_commands.add_field(
        name="!tracker remove <phrase>",
        value="Removes a word/phrase. Use 'quotes' for multi-word (e.g. `!tracker remove 'lock in'`)",
        inline=False
    )
    tracker_commands.add_field(
        name="!tracker list",
        value="Lists all tracked words and their counts",
        inline=False
    )
    tracker_commands.add_field(
        name="!tracker scan",
        value="Scans past messages to count words retroactively",
        inline=False
    )
    tracker_commands.set_footer(text="Admins only · Page 5 of 7")

    birthday_commands = discord.Embed(
        title="📘 Birthdays",
        color=discord.Color.purple()
    )
    birthday_commands.add_field(
        name="!birthday add <name> <MM-DD>",
        value="Adds a birthday by name (date format: 06-12)",
        inline=False
    )
    birthday_commands.add_field(
        name="!birthday remove <name>",
        value="Removes a birthday by name",
        inline=False
    )
    birthday_commands.add_field(
        name="!birthdays",
        value="Shows the birthday list with page navigation",
        inline=False
    )
    birthday_commands.add_field(
        name="!birthday channel #channel",
        value="Set channel for birthday announcements",
        inline=False
    )
    birthday_commands.set_footer(text="Page 6 of 7")

    misc_commands = discord.Embed(
        title="📘 Miscellaneous",
        color=discord.Color.blue()
    )
    misc_commands.add_field(
        name="!clear <amount>",
        value="Deletes the specified number of messages from this channel",
        inline=False
    )
    misc_commands.add_field(
        name="!help",
        value="Shows this help message",
        inline=False
    )
    misc_commands.set_footer(text="Clear requires admin · Page 7 of 7")

    pages = [gif_commands, role_commands, starboard_commands, souls_commands, tracker_commands, birthday_commands, misc_commands]

    # add author and timestamp to all pages
    for embed in pages:
        embed.set_author(name=ctx.guild.me.display_name, icon_url=ctx.guild.me.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

    message = await ctx.send(embed=pages[0])

    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    current_page = 0

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

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
