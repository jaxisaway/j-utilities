import discord
from discord.ext import commands
from config import bot
from assignable_roles import get_assignable_roles, add_assignable_role, remove_assignable_role

@bot.command()
async def addrole(ctx, *, role_name: str):
    # add a role to yourself
    allowed = get_assignable_roles(ctx.guild.id)
    if role_name not in allowed:
        await ctx.send(f"❌ You're not allowed to assign the `{role_name}` role.")
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Role `{role_name}` not found.")
        return

    if role in ctx.author.roles:
        await ctx.send(f"⚠️ You already have the `{role.name}` role.")
        return

    try:
        await ctx.author.add_roles(role)
        await ctx.send(f"✅ Added `{role.name}` to you.")

        log_channel = discord.utils.get(ctx.guild.text_channels, name="mod-logs")
        if log_channel:
            await log_channel.send(
                f"➕ **Role Added**\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**User:** {ctx.author.mention}\n"
                f"**Role:** `{role.name}`"
            )
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to assign that role.")


@bot.command()
async def removerole(ctx, *, role_name: str):
    # remove a role from yourself
    allowed = get_assignable_roles(ctx.guild.id)
    if role_name not in allowed:
        await ctx.send(f"❌ You're not allowed to remove the `{role_name}` role.")
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Role `{role_name}` not found.")
        return

    if role not in ctx.author.roles:
        await ctx.send(f"⚠️ You don't have the `{role.name}` role.")
        return

    try:
        await ctx.author.remove_roles(role)
        await ctx.send(f"✅ Removed `{role.name}` from you.")

        log_channel = discord.utils.get(ctx.guild.text_channels, name="mod-logs")
        if log_channel:
            await log_channel.send(
                f"➖ **Role Removed**\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**User:** {ctx.author.mention}\n"
                f"**Role:** `{role.name}`"
            )
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove that role.")


@bot.command()
async def viewroles(ctx):
    # show what roles you can add/remove
    allowed = get_assignable_roles(ctx.guild.id)
    if not allowed:
        await ctx.send("✅ No self-assignable roles are set for this server. Admins can add them with `!assignablerole add <name>`.")
        return
    roles_list = ", ".join(allowed)
    await ctx.send(f"✅ The roles you can assign or remove from yourself are: {roles_list}")

@bot.group(name="assignablerole", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def assignablerole_group(ctx):
    await ctx.send("Use `!assignablerole add <name>` or `!assignablerole remove <name>` to manage self-assignable roles.")

@assignablerole_group.command(name="add")
@commands.has_permissions(administrator=True)
async def assignablerole_add(ctx, *, role_name: str):
    """Add a role to the self-assignable list (admin only)."""
    role_name = role_name.strip()
    if not role_name:
        await ctx.send("⚠️ Use: `!assignablerole add <role name>`.")
        return
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Role `{role_name}` not found on this server.")
        return
    if add_assignable_role(ctx.guild.id, role_name):
        await ctx.send(f"✅ **{role_name}** is now self-assignable. Users can use `!addrole {role_name}` and `!removerole {role_name}`.")
    else:
        await ctx.send(f"⚠️ **{role_name}** is already in the self-assignable list.")

@assignablerole_group.command(name="remove")
@commands.has_permissions(administrator=True)
async def assignablerole_remove(ctx, *, role_name: str):
    """Remove a role from the self-assignable list (admin only)."""
    role_name = role_name.strip()
    if not role_name:
        await ctx.send("⚠️ Use: `!assignablerole remove <role name>`.")
        return
    if remove_assignable_role(ctx.guild.id, role_name):
        await ctx.send(f"✅ **{role_name}** is no longer self-assignable.")
    else:
        await ctx.send(f"⚠️ **{role_name}** was not in the self-assignable list.")
