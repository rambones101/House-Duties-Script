"""Discord bot commands for House Duties Scheduler."""
import discord
from discord.ext import commands
from datetime import datetime, date as dt_date
from typing import Optional
import json
import os

from .scheduler import load_schedule, run_scheduler_with_retry
from .embeds import (
    create_header_embed,
    create_day_embed,
    create_footer_embed,
    create_error_embed,
    create_member_chores_embed,
    create_today_chores_embed,
    create_status_embed
)
from .config import COLOR_SUCCESS, COLOR_WARNING


def load_discord_mapping():
    """Load Discord username to brother name mapping."""
    mapping_path = "config/discord_mapping.json"
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('mappings', {})
        except:
            pass
    return {}


def get_brother_name(member: discord.Member) -> str:
    """Get brother name from Discord member, checking mapping file first."""
    mapping = load_discord_mapping()
    
    # Try display name first (server nickname)
    if member.display_name in mapping:
        return mapping[member.display_name]
    
    # Try username (global username)
    if member.name in mapping:
        return mapping[member.name]
    
    # Try case-insensitive matching
    display_lower = member.display_name.lower()
    name_lower = member.name.lower()
    for discord_name, brother_name in mapping.items():
        if discord_name.lower() == display_lower or discord_name.lower() == name_lower:
            return brother_name
    
    # Fall back to display name then username
    return member.display_name or member.name


async def send_schedule_embeds(channel, schedule_data):
    """Send schedule using Discord embeds for better formatting."""
    # Header
    await channel.send(embed=create_header_embed())
    
    # Group schedule by date
    by_date = {}
    for item in schedule_data:
        date = item['due'].split(' ')[0]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(item)
    
    # Send embeds for each date
    for date_str in sorted(by_date.keys()):
        # Group by deck
        by_deck = {}
        for item in by_date[date_str]:
            deck = item['deck']
            if deck not in by_deck:
                by_deck[deck] = []
            by_deck[deck].append(item)
        
        await channel.send(embed=create_day_embed(date_str, by_deck))
    
    # Footer
    await channel.send(embed=create_footer_embed())


def setup_commands(bot: commands.Bot, config):
    """Register all bot commands."""
    
    @bot.command(name='run-schedule', aliases=['run', 'generate'])
    @commands.has_permissions(administrator=True)
    async def run_schedule(ctx):
        """Manually trigger the scheduler (admin only)."""
        status_msg = await ctx.send(embed=create_status_embed(
            "🔄 Running Scheduler",
            "Generating schedule manually...",
            "info"
        ))
        
        success, error, schedule_data = await run_scheduler_with_retry(
            config.PYTHON_CMD,
            config.SCRIPT_PATH,
            config.MAX_RETRIES,
            config.RETRY_DELAY
        )
        
        if success and schedule_data:
            await status_msg.delete()
            await send_schedule_embeds(ctx.channel, schedule_data)
            
            # Send confirmation DM to user
            try:
                dm_embed = create_status_embed(
                    "✅ Schedule Generated",
                    f"Schedule successfully generated in {ctx.channel.mention}",
                    "success"
                )
                await ctx.author.send(embed=dm_embed)
            except:
                pass  # User has DMs disabled
        else:
            await status_msg.edit(embed=create_error_embed(error, config.MAX_RETRIES))
    
    
    @bot.command(name='my-chores', aliases=['my-duties', 'mychores'])
    async def my_chores(ctx, member: Optional[discord.Member] = None):
        """
        View your assigned chores for the week.
        Usage: !my-chores [@member]
        """
        target = member or ctx.author
        brother_name = get_brother_name(target)
        schedule_data = await load_schedule()
        
        if not schedule_data:
            embed = create_status_embed(
                "📋 No Schedule Available",
                "No schedule has been generated yet.\nAsk an admin to run `!run-schedule`.",
                "warning"
            )
            await ctx.send(embed=embed)
            return
        
        # Find chores for this member
        member_chores = {}
        for item in schedule_data:
            # Check if brother_name is in the assigned list
            if brother_name in item['assigned']:
                date = item['due'].split(' ')[0]
                if date not in member_chores:
                    member_chores[date] = []
                member_chores[date].append(item)
        
        await ctx.send(embed=create_member_chores_embed(target, member_chores))
    
    
    @bot.command(name='chores-today', aliases=['today', 'chores'])
    async def chores_today(ctx):
        """View all chores due today."""
        schedule_data = await load_schedule()
        
        if not schedule_data:
            embed = create_status_embed(
                "📋 No Schedule Available",
                "No schedule has been generated yet.\nAsk an admin to run `!run-schedule`.",
                "warning"
            )
            await ctx.send(embed=embed)
            return
        
        # Get today's date
        today = dt_date.today().isoformat()
        
        # Find today's chores
        today_chores = {}
        for item in schedule_data:
            date = item['due'].split(' ')[0]
            if date == today:
                deck = item['deck']
                if deck not in today_chores:
                    today_chores[deck] = []
                today_chores[deck].append(item)
        
        await ctx.send(embed=create_today_chores_embed(today_chores))
    
    
    @bot.command(name='ping')
    async def ping(ctx):
        """Check if bot is responsive."""
        latency_ms = round(bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=COLOR_SUCCESS if latency_ms < 200 else COLOR_WARNING
        )
        embed.add_field(name="Latency", value=f"{latency_ms}ms", inline=True)
        embed.add_field(name="Status", value="✅ Online", inline=True)
        
        # Add schedule file status
        schedule_exists = await load_schedule() is not None
        embed.add_field(
            name="Schedule",
            value="✅ Available" if schedule_exists else "❌ Not generated",
            inline=True
        )
        
        embed.set_footer(text=f"Scheduled run: Sundays at {config.RUN_TIME_HOUR:02d}:{config.RUN_TIME_MINUTE:02d}")
        await ctx.send(embed=embed)
