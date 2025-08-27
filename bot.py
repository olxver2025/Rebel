from typing import List
import nextcord as nc 
import os
import sqlite3
from nextcord.ext import commands, application_checks
from cooldowns import cooldown, SlashBucket, CallableOnCooldown
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_NAME = os.getenv('BOT_NAME')
SEC = int(os.getenv('DEFAULT_TIMEOUT_SECONDS'))

intents = nc.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(intents=intents)
slash = bot.slash_command

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

def _available_cogs() -> List[str]:
    return [
        f[:-3]
        for f in os.listdir("./cogs")
        if f.endswith(".py") and not f.startswith("_")
    ]

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    with sqlite3.connect('data/rebel.db') as conn:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS bans 
                    (id INTEGER PRIMARY KEY, user INTEGER, guild INTEGER, reason TEXT, moderator INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS mutes
                    (id INTEGER PRIMARY KEY, user INTEGER, guild INTEGER, reason TEXT, moderator INTEGER, duration INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS warns
                    (id INTEGER PRIMARY KEY, user INTEGER, guild INTEGER, reason TEXT, moderator INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS kicks
                    (id INTEGER PRIMARY KEY, user INTEGER, guild INTEGER, reason TEXT, moderator INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS settings
                    (guild INTEGER PRIMARY KEY, modlog_channel INTEGER)''')
        # id = randomly generated unique id for each entry
        conn.commit()
        
    await bot.sync_all_application_commands()



@slash(name="ping", description="Check the bot's latency")
@cooldown(1, SEC, bucket=SlashBucket.author)
async def ping(interaction: nc.Interaction):
    embed = nc.Embed(title="Pong!", description=f"Latency: {round(bot.latency * 1000)}ms", color=nc.Colour.blurple())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@slash(name="reload", description="Reload a cog (developer only)")
@application_checks.is_owner()
async def reload_cog(
    interaction: nc.Interaction,
    cog: str = nc.SlashOption(
        name="cog",
        description="Which cog to reload",
        required=True,
        choices=_available_cogs()  
    ),
):
    try:
        bot.reload_extension(f"cogs.{cog}")
        await bot.sync_all_application_commands()
        await interaction.response.send_message(f"Reloaded cog: `{cog}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(
            f"Error reloading `{cog}`:\n```py\n{e}\n```",
            ephemeral=True
        )


@slash(name="help", description="Need help?")
@cooldown(1, SEC, bucket=SlashBucket.author)
async def help_command(interaction: nc.Interaction):
    embed = nc.Embed(title="Hey there! 👋", description=f"Hi {interaction.user.mention}!\nI am **{BOT_NAME}**, an advanced moderation bot designed to keep Discord servers safe and protected.", color=nc.Colour.blurple())
    await interaction.response.send_message(embed=embed, ephemeral=True)


# error handling

def humanize_seconds(seconds: float) -> str:
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


@bot.event
async def on_application_command_error(interaction: nc.Interaction, error: Exception):
    if isinstance(error, CallableOnCooldown):
        retry = humanize_seconds(error.retry_after)
        return await interaction.response.send_message(
            f"You're a bit quick! Try again in {retry}.",
            ephemeral=True
        )
    if isinstance(error, application_checks.ApplicationMissingPermissions):
        missing = [perm.replace("_", " ").title() for perm in error.missing_permissions]
        return await interaction.response.send_message(
            f"You don't have permission to do that here.\n"
            f"Missing: {', '.join(missing)}",
            ephemeral=True
        )

    if isinstance(error, application_checks.ApplicationBotMissingPermissions):
        missing = [perm.replace("_", " ").title() for perm in error.missing_permissions]
        return await interaction.response.send_message(
            "I’m missing required permissions to run that command.\n"
            f"Missing: {', '.join(missing)}",
            ephemeral=True
        )
    if isinstance(error, application_checks.ApplicationNotOwner):
        return await interaction.response.send_message(
            "Sorry! That command is developer only.",
            ephemeral=True
        )
    try:
        print(f"Unhandled error in command {interaction.application_command.name}: {error}")
        await interaction.response.send_message(
            "Something went wrong while running that command.",
            ephemeral=True
        )
    except nc.InteractionResponded:
        print(f"Interaction already responded to for error in command {interaction.application_command.name}: {error}")
        await interaction.followup.send(
            "Something went wrong while running that command.",
            ephemeral=True
        )



bot.run(TOKEN)