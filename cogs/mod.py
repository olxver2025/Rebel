from datetime import timedelta
import nextcord as nc
import os
import sqlite3
from nextcord import slash_command as slash
from nextcord import Interaction, SlashOption
from nextcord.ext import commands, application_checks
from cooldowns import cooldown, SlashBucket
from dotenv import load_dotenv
load_dotenv()
BOT_NAME = os.getenv('BOT_NAME')
SEC = int(os.getenv('DEFAULT_TIMEOUT_SECONDS'))


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash(name=f"{BOT_NAME.lower()}", description="Main command for the bot.")
    async def rebel(self, interaction: Interaction): # rebel will not show in the slash command list, only what the BOT_NAME env variable is set to, change if you want
        pass

    @rebel.subcommand(name="panel", description="Open the moderation panel.")
    @application_checks.has_permissions(manage_guild=True)
    @application_checks.bot_has_permissions(manage_guild=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def panel(self, inter:Interaction):
        embed = nc.Embed(
            title=f"⚙️ {inter.guild.name} - Panel",
            description="Welcome to the moderation panel. Use the buttons below to manage this server.",
        )
        embed.set_thumbnail(url=inter.guild.icon.url if inter.guild.icon else "")
        await inter.response.send_message(embed=embed, ephemeral=True)

    @rebel.subcommand(name="member", description="member parent commands")
    @application_checks.has_permissions(moderate_members=True)
    @application_checks.bot_has_permissions(moderate_members=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def member(self, inter:Interaction):
        pass

    @member.subcommand(name="ban", description="Ban a member from the server.")
    @application_checks.has_permissions(ban_members=True)
    @application_checks.bot_has_permissions(ban_members=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def ban(
        self,
        inter: Interaction,
        member: nc.Member = SlashOption(
            name="member",
            description="The member to ban.",
            required=True,
        ),
        reason: str = SlashOption(
            name="reason",
            description="The reason for the ban.",
            required=False,
            default="No reason provided."
        )
    ):
        if member == inter.user:
            return await inter.response.send_message("You cannot ban yourself.", ephemeral=True)
        if member == self.bot.user:
            return await inter.response.send_message("I cannot ban myself.", ephemeral=True)
        if member.top_role >= inter.user.top_role and inter.guild.owner_id != inter.user.id:
            return await inter.response.send_message("You cannot ban this member.", ephemeral=True)
        if member.top_role >= inter.guild.me.top_role:
            return await inter.response.send_message("I cannot ban this member.", ephemeral=True)

        try:
            with sqlite3.connect('data/rebel.db') as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO bans (user, guild, reason, moderator) VALUES (?, ?, ?, ?)', (member.id, inter.guild.id, reason, inter.user.id))
                conn.commit()
            await member.ban(reason=reason)
            embed = nc.Embed(
                title="🚫 Member Banned",
                description=f"I successfully banned {member.mention}.",
                color=nc.Colour.red()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            with sqlite3.connect('data/rebel.db') as conn:
                cur = conn.cursor()
                cur.execute('SELECT modlog_channel FROM settings WHERE guild = ?', (inter.guild.id,))
                result = cur.fetchone()
                if result and result[0]:
                    modlog_channel = inter.guild.get_channel(result[0])
                    if modlog_channel:
                        log_embed = nc.Embed(
                            title="🚫 Member Banned",
                            description=f"{member.mention} was banned by {inter.user.mention}.\nReason: {reason}",
                            color=nc.Colour.blurple()
                        )
                        await modlog_channel.send(embed=log_embed)

        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't ban that member. Try again later.", ephemeral=True)
            print(e)
            return
        
    @member.subcommand(name="kick", description="Kick a member from the server.")
    @application_checks.has_permissions(kick_members=True)
    @application_checks.bot_has_permissions(kick_members=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def kick(self, 
                   inter:Interaction, 
                   member: nc.Member = SlashOption(
                       name="member",
                       description="The member to kick.",
                       required=True,
                   ),
                     reason: str = SlashOption(
                          name="reason",
                          description="The reason for the kick.",
                          required=False,
                          default="No reason provided."
                     )):
        if member == inter.user:
            return await inter.response.send_message("You cannot kick yourself.", ephemeral=True)
        if member == self.bot.user:
            return await inter.response.send_message("I cannot kick myself.", ephemeral=True)
        if member.top_role >= inter.user.top_role and inter.guild.owner_id != inter.user.id:
            return await inter.response.send_message("You cannot kick this member.", ephemeral=True)
        if member.top_role >= inter.guild.me.top_role:
            return await inter.response.send_message("I cannot kick this member.", ephemeral=True)
        try:
            with sqlite3.connect('data/rebel.db') as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO kicks (user, guild, reason, moderator) VALUES (?, ?, ?, ?)', (member.id, inter.guild.id, reason, inter.user.id))
                conn.commit()
            await member.kick(reason=reason)
            embed = nc.Embed(
                title="🥾 Member Kicked",
                description=f"I successfully kicked {member.mention}.",
                color=nc.Colour.orange()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            with sqlite3.connect('data/rebel.db') as conn:
                cur = conn.cursor()
                cur.execute('SELECT modlog_channel FROM settings WHERE guild = ?', (inter.guild.id,))
                result = cur.fetchone()
                if result and result[0]:
                    modlog_channel = inter.guild.get_channel(result[0])
                    if modlog_channel:
                        log_embed = nc.Embed(
                            title="🥾 Member Kicked",
                            description=f"{member.mention} was kicked by {inter.user.mention}.\nReason: {reason}",
                            color=nc.Colour.blurple()
                        )
                        await modlog_channel.send(embed=log_embed)
        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't kick that member. Try again later.", ephemeral=True)
            print(e)
            return
        
    
    @member.subcommand(name="mute", description="Mute (timeout) a member.")
    @application_checks.has_permissions(moderate_members=True)
    @application_checks.bot_has_permissions(moderate_members=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def timeout(
        self,
        inter: Interaction,
        member: nc.Member = SlashOption(
            name="member",
            description="The member to mute.",
            required=True,
        ),
        duration: int = SlashOption(
            name="duration",
            description="Duration of the mute in minutes (1-10080).",
            required=True,
            min_value=1,
            max_value=10080
        ),
        reas: str = SlashOption(
            name="reason",
            description="The reason for the mute.",
            required=False,
            default="No reason provided."
        )
    ):
        if member == inter.user:
            return await inter.response.send_message("You cannot mute yourself.", ephemeral=True)
        if member == self.bot.user:
            return await inter.response.send_message("I cannot mute myself.", ephemeral=True)
        if member.top_role >= inter.user.top_role and inter.guild.owner_id != inter.user.id:
            return await inter.response.send_message("You cannot mute this member.", ephemeral=True)
        if member.top_role >= inter.guild.me.top_role:
            return await inter.response.send_message("I cannot mute this member.", ephemeral=True)
        try:
            until = nc.utils.utcnow() + timedelta(minutes=duration)
            with sqlite3.connect('data/rebel.db') as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO mutes (user, guild, reason, moderator, duration) VALUES (?, ?, ?, ?, ?)', (member.id, inter.guild.id, f"Timed out for {duration} minutes", inter.user.id, duration))
                conn.commit()
            await member.timeout(timeout=until,reason=f"Timed out by {inter.user}; {reas}")
            embed = nc.Embed(
                title="🔇 Member Muted",
                description=f"I successfully muted {member.mention} for {duration} minutes.",
                color=nc.Colour.blue()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            with sqlite3.connect('data/rebel.db') as conn:
                cur = conn.cursor()
                cur.execute('SELECT modlog_channel FROM settings WHERE guild = ?', (inter.guild.id,))
                result = cur.fetchone()
                if result and result[0]:
                    modlog_channel = inter.guild.get_channel(result[0])
                    if modlog_channel:
                        log_embed = nc.Embed(
                            title="🔇 Member Muted",
                            description=f"{member.mention} was muted by {inter.user.mention} for {duration} minutes.\nReason: {reas}",
                            color=nc.Colour.blurple()
                        )
                        await modlog_channel.send(embed=log_embed)
        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't mute that member. Try again later.", ephemeral=True)
            print(e)
            return
        
    @rebel.subcommand(name="channel", description="channel parent commands")
    @application_checks.has_permissions(manage_channels=True)
    @application_checks.bot_has_permissions(manage_channels=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def channel(self, inter:Interaction):
        pass

    @channel.subcommand(name="cooldown", description="Set a channel's cooldown.")
    @application_checks.has_permissions(manage_channels=True)
    @application_checks.bot_has_permissions(manage_channels=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def chan_cooldown(self, 
        inter:Interaction,
        channel: nc.TextChannel = SlashOption(
            name="channel",
            description="The channel to set the cooldown for.",
            required=True,
        ),
        seconds: int = SlashOption(
            name="seconds",
            description="The cooldown duration in seconds (0-21600).",
            required=True,
            min_value=0,
            max_value=21600
        )
    ):
        try:
            await channel.edit(slowmode_delay=seconds, reason=f"Cooldown set by {inter.user}")
            embed = nc.Embed(
                title="❄️ Channel Cooldown Set",
                description=f"Set the cooldown for {channel.mention} to {seconds} seconds.",
                color=nc.Colour.green()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't set the cooldown for that channel. Try again later.", ephemeral=True)
            print(e)
            return
        
    @channel.subcommand(name="lock", description="Lock a channel.")
    @application_checks.has_permissions(manage_channels=True)
    @application_checks.bot_has_permissions(manage_channels=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def lock(self, 
        inter:Interaction,
        channel: nc.TextChannel = SlashOption(
            name="channel",
            description="The channel to lock.",
            required=True,
        )
    ):
        try:
            await channel.set_permissions(inter.guild.default_role, send_messages=False, reason=f"Channel locked by {inter.user}")
            embed = nc.Embed(
                title="🔒 Channel Locked",
                description=f"Locked {channel.mention}.",
                color=nc.Colour.red()
            )
            await inter.response.send_message(embed=embed)
        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't lock that channel. Try again later.", ephemeral=True)
            print(e)
            return
        
    @channel.subcommand(name="unlock", description="Unlock a channel.")
    @application_checks.has_permissions(manage_channels=True)
    @application_checks.bot_has_permissions(manage_channels=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def unlock(self, 
        inter:Interaction,
        channel: nc.TextChannel = SlashOption(
            name="channel",
            description="The channel to unlock.",
            required=True,
        )
    ):
        try:
            await channel.set_permissions(inter.guild.default_role, send_messages=None, reason=f"Channel unlocked by {inter.user}")
            embed = nc.Embed(
                title="🔓 Channel Unlocked",
                description=f"Unlocked {channel.mention}.",
                color=nc.Colour.green()
            )
            await inter.response.send_message(embed=embed)
        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't unlock that channel. Try again later.", ephemeral=True)
            print(e)
            return

    @channel.subcommand(name="purge", description="Purge messages in a channel.")
    @application_checks.has_permissions(manage_messages=True)
    @application_checks.bot_has_permissions(manage_messages=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def purge(self, 
        inter:Interaction,
        channel: nc.TextChannel = SlashOption(
            name="channel",
            description="The channel to purge messages in.",
            required=True,
        ),
        amount: int = SlashOption(
            name="amount",
            description="The number of messages to purge (1-100).",
            required=True,
            min_value=1,
            max_value=100
        )
    ):
        try:
            deleted = await channel.purge(limit=amount, reason=f"Messages purged by {inter.user}")
            embed = nc.Embed(
                title="Messages Purged",
                description=f"Purged {len(deleted)} messages in {channel.mention}.",
                color=nc.Colour.green()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't purge messages in that channel. Try again later.", ephemeral=True)
            print(e)
            return
        
    @rebel.subcommand(name="guild", description="guild parent commands")
    @application_checks.has_permissions(manage_guild=True)
    @application_checks.bot_has_permissions(manage_guild=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def guild(self, inter:Interaction):
        pass

    @guild.subcommand(name="logs", description="Set up moderation logs.")
    @application_checks.has_permissions(manage_guild=True)
    @application_checks.bot_has_permissions(manage_guild=True)
    @cooldown(1, SEC, bucket=SlashBucket.author)
    async def logs(self, 
        inter:Interaction,
        channel: nc.TextChannel = SlashOption(
            name="channel",
            description="The channel to set as the logs channel.",
            required=True,
        )
    ):
        try:
            with sqlite3.connect('data/rebel.db') as conn:
                cur = conn.cursor()
                cur.execute('REPLACE INTO settings (guild, modlog_channel) VALUES (?, ?)', (inter.guild.id, channel.id))
                conn.commit()
            embed = nc.Embed(
                title="📄 Logs Channel Set",
                description=f"Set {channel.mention} as the moderation logs channel.",
                color=nc.Colour.green()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await inter.response.send_message("Sorry! I couldn't set the logs channel. Try again later.", ephemeral=True)
            print(e)
            return


    

def setup(bot):
    bot.add_cog(Mod(bot))