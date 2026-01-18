"""
Discord Bot for House Duties Scheduler
Automatically runs the scheduler every Sunday and posts to a Discord channel.
Features: Embeds, retry logic, query commands, manual triggers.
"""

import discord
from discord.ext import commands, tasks
import asyncio
import subprocess
import json
from datetime import datetime, time as dt_time, date as dt_date, timedelta
import os
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# ===== CONFIGURATION =====
# Load from environment variables with defaults
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
RUN_TIME_HOUR = int(os.getenv("RUN_TIME_HOUR", "8"))
RUN_TIME_MINUTE = int(os.getenv("RUN_TIME_MINUTE", "0"))
SCRIPT_PATH = os.getenv("SCRIPT_PATH", "house_duties.py")
PYTHON_CMD = os.getenv("PYTHON_CMD", "python")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))

# Validation
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required. See .env.example")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID environment variable is required. See .env.example")

try:
    CHANNEL_ID = int(CHANNEL_ID)
except ValueError:
    raise ValueError(f"CHANNEL_ID must be a valid integer, got: {CHANNEL_ID}")

if not (0 <= RUN_TIME_HOUR <= 23):
    raise ValueError(f"RUN_TIME_HOUR must be 0-23, got: {RUN_TIME_HOUR}")
if not (0 <= RUN_TIME_MINUTE <= 59):
    raise ValueError(f"RUN_TIME_MINUTE must be 0-59, got: {RUN_TIME_MINUTE}")
# ========================

# Bot setup with minimal intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Colors for embeds
COLOR_SUCCESS = 0x00ff00  # Green
COLOR_ERROR = 0xff0000    # Red
COLOR_INFO = 0x3498db     # Blue
COLOR_WARNING = 0xffa500  # Orange

# Deck colors for visual distinction
DECK_COLORS = {
    "Zero Deck": 0x9b59b6,   # Purple
    "First Deck": 0x3498db,  # Blue
    "Second Deck": 0x2ecc71, # Green
    "Third Deck": 0xe74c3c,  # Red
    "Other": 0x95a5a6        # Gray
}


@bot.event
async def on_ready():
    print(f'🤖 {bot.user} is now online!')
    print(f'📅 Scheduled to run every Sunday at {RUN_TIME_HOUR:02d}:{RUN_TIME_MINUTE:02d}')
    print(f'💬 Command prefix: !')
    print(f'📝 Available commands: run-schedule, my-chores, chores-today, ping')
    weekly_scheduler.start()


@bot.event
async def on_command_error(ctx, error):
    """Global error handler for better error messages"""
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You don't have permission to use this command.",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="❓ Command Not Found",
            description=f"Use `!help` to see available commands.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="⚠️ Missing Argument",
            description=f"Missing required argument: `{error.param.name}`\nUse `!help {ctx.command}` for usage.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
    else:
        # Log unexpected errors
        print(f"❌ Unexpected error in {ctx.command}: {error}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"An unexpected error occurred: {str(error)}",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)


async def load_schedule() -> Optional[List[Dict]]:
    """Load schedule.json with error handling"""
    try:
        if not os.path.exists('schedule.json'):
            return None
        with open('schedule.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("❌ Error: schedule.json is invalid")
        return None
    except Exception as e:
        print(f"❌ Error loading schedule: {e}")
        return None


async def run_scheduler_with_retry() -> tuple[bool, Optional[str], Optional[List[Dict]]]:
    """
    Run the scheduler with retry logic.
    Returns: (success, error_message, schedule_data)
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"🏃 Running scheduler (attempt {attempt}/{MAX_RETRIES})...")
            
            result = subprocess.run(
                [PYTHON_CMD, SCRIPT_PATH],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                # Success!
                schedule_data = await load_schedule()
                if schedule_data:
                    print(f"✅ Scheduler completed successfully")
                    return True, None, schedule_data
                else:
                    error_msg = "Scheduler ran but schedule.json not found or invalid"
                    print(f"⚠️ {error_msg}")
                    return False, error_msg, None
            else:
                # Non-zero exit code
                error_msg = f"Exit code {result.returncode}\n{result.stderr[:500]}"
                print(f"❌ Scheduler failed: {error_msg}")
                
                if attempt < MAX_RETRIES:
                    print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    return False, error_msg, None
                    
        except subprocess.TimeoutExpired:
            error_msg = "Scheduler timed out after 60 seconds"
            print(f"⏱️ {error_msg}")
            
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False, error_msg, None
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                return False, error_msg, None
    
    return False, "All retry attempts failed", None


@tasks.loop(time=dt_time(hour=RUN_TIME_HOUR, minute=RUN_TIME_MINUTE))
async def weekly_scheduler():
    """Runs every day at the specified time, but only executes on Sundays"""
    now = datetime.now()
    
    # Only run on Sundays (weekday 6)
    if now.weekday() != 6:
        print(f"⏭️  Skipping - today is {now.strftime('%A')} (not Sunday)")
        return
    
    print(f"📅 Sunday detected - running house duties scheduler")
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Could not find channel with ID {CHANNEL_ID}")
        return
    
    # Send "generating" message
    embed = discord.Embed(
        title="🔄 Generating Schedule",
        description="Please wait while the schedule is being generated...",
        color=COLOR_INFO,
        timestamp=datetime.now()
    )
    status_msg = await channel.send(embed=embed)
    
    # Run scheduler with retry
    success, error, schedule_data = await run_scheduler_with_retry()
    
    if success and schedule_data:
        # Delete status message
        await status_msg.delete()
        
        # Send schedule with embeds
        await send_schedule_embeds(channel, schedule_data)
        print("✅ Schedule posted to Discord successfully!")
    else:
        # Update status message with error
        error_embed = discord.Embed(
            title="❌ Scheduler Failed",
            description=f"Failed to generate schedule after {MAX_RETRIES} attempts.",
            color=COLOR_ERROR,
            timestamp=datetime.now()
        )
        if error:
            error_embed.add_field(
                name="Error Details",
                value=f"```\n{error[:1000]}\n```",
                inline=False
            )
        error_embed.add_field(
            name="💡 What to do",
            value="• Check logs with `!ping` to verify bot is running\n"
                  "• Verify brothers.txt and other input files\n"
                  "• Contact administrator if issue persists",
            inline=False
        )
        await status_msg.edit(embed=error_embed)


async def send_schedule_embeds(channel, schedule_data: List[Dict]):
    """Send schedule using Discord embeds for better formatting"""
    now = datetime.now()
    
    # Header embed
    header_embed = discord.Embed(
        title="📋 Weekly House Duties Schedule",
        description=f"Schedule for the week of {now.strftime('%B %d, %Y')}",
        color=COLOR_SUCCESS,
        timestamp=now
    )
    header_embed.set_footer(text="Generated by House Duties Scheduler")
    await channel.send(embed=header_embed)
    
    # Group schedule by date
    by_date = {}
    for item in schedule_data:
        date = item['due'].split(' ')[0]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(item)
    
    # Send embeds for each date
    for date_str in sorted(by_date.keys()):
        dt = datetime.fromisoformat(date_str)
        dow = dt.strftime('%A')
        
        # Group by deck
        by_deck = {}
        for item in by_date[date_str]:
            deck = item['deck']
            if deck not in by_deck:
                by_deck[deck] = []
            by_deck[deck].append(item)
        
        # Create embed for this day
        day_embed = discord.Embed(
            title=f"📅 {dow}, {dt.strftime('%B %d')}",
            color=COLOR_INFO
        )
        
        # Add fields for each deck
        deck_order = ["Zero Deck", "First Deck", "Second Deck", "Third Deck", "Other"]
        for deck in deck_order:
            if deck in by_deck:
                tasks_text = ""
                for item in by_deck[deck]:
                    assigned = ", ".join(item['assigned'])
                    tasks_text += f"• **{item['task']}**\n  └ {assigned}\n"
                
                # Discord has a 1024 char limit per field
                if len(tasks_text) > 1000:
                    # Split into multiple fields
                    chunks = [tasks_text[i:i+1000] for i in range(0, len(tasks_text), 1000)]
                    for i, chunk in enumerate(chunks):
                        field_name = f"{deck} (part {i+1})" if i > 0 else deck
                        day_embed.add_field(name=field_name, value=chunk, inline=False)
                else:
                    day_embed.add_field(name=deck, value=tasks_text, inline=False)
        
        await channel.send(embed=day_embed)
    
    # Footer embed
    footer_embed = discord.Embed(
        title="✅ Schedule Complete",
        description="Good luck with your duties this week!\n\nUse `!my-chores` to see your assignments.",
        color=COLOR_SUCCESS
    )
    await channel.send(embed=footer_embed)


# ===== COMMANDS =====

@bot.command(name='run-schedule', aliases=['run', 'generate'])
@commands.has_permissions(administrator=True)
async def run_schedule(ctx):
    """Manually trigger the scheduler (admin only)"""
    embed = discord.Embed(
        title="🔄 Running Scheduler",
        description="Generating schedule manually...",
        color=COLOR_INFO,
        timestamp=datetime.now()
    )
    status_msg = await ctx.send(embed=embed)
    
    success, error, schedule_data = await run_scheduler_with_retry()
    
    if success and schedule_data:
        await status_msg.delete()
        await send_schedule_embeds(ctx.channel, schedule_data)
        
        # Send confirmation DM to user
        try:
            dm_embed = discord.Embed(
                title="✅ Schedule Generated",
                description=f"Schedule successfully generated in {ctx.channel.mention}",
                color=COLOR_SUCCESS
            )
            await ctx.author.send(embed=dm_embed)
        except:
            pass  # User has DMs disabled
    else:
        error_embed = discord.Embed(
            title="❌ Generation Failed",
            description=f"Failed after {MAX_RETRIES} attempts.",
            color=COLOR_ERROR,
            timestamp=datetime.now()
        )
        if error:
            error_embed.add_field(name="Error", value=f"```\n{error[:1000]}\n```", inline=False)
        await status_msg.edit(embed=error_embed)


@bot.command(name='my-chores', aliases=['my-duties', 'mychores'])
async def my_chores(ctx, member: Optional[discord.Member] = None):
    """
    View your assigned chores for the week.
    Usage: !my-chores [@member]
    """
    target = member or ctx.author
    schedule_data = await load_schedule()
    
    if not schedule_data:
        embed = discord.Embed(
            title="📋 No Schedule Available",
            description="No schedule has been generated yet.\nAsk an admin to run `!run-schedule`.",
            color=COLOR_WARNING
        )
        await ctx.send(embed=embed)
        return
    
    # Find chores for this member
    member_chores = {}
    for item in schedule_data:
        if target.display_name in item['assigned'] or target.name in item['assigned']:
            date = item['due'].split(' ')[0]
            if date not in member_chores:
                member_chores[date] = []
            member_chores[date].append(item)
    
    if not member_chores:
        embed = discord.Embed(
            title=f"📋 Chores for {target.display_name}",
            description="No chores assigned this week! 🎉",
            color=COLOR_SUCCESS
        )
        await ctx.send(embed=embed)
        return
    
    # Create embed with chores
    embed = discord.Embed(
        title=f"📋 Chores for {target.display_name}",
        description=f"Your assignments for this week:",
        color=COLOR_INFO,
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    total_chores = 0
    for date_str in sorted(member_chores.keys()):
        dt = datetime.fromisoformat(date_str)
        dow = dt.strftime('%A, %b %d')
        
        chores_text = ""
        for item in member_chores[date_str]:
            chores_text += f"• **{item['task']}** ({item['deck']})\n"
            total_chores += 1
        
        embed.add_field(name=dow, value=chores_text, inline=False)
    
    embed.set_footer(text=f"Total: {total_chores} chore{'s' if total_chores != 1 else ''}")
    await ctx.send(embed=embed)


@bot.command(name='chores-today', aliases=['today', 'chores'])
async def chores_today(ctx):
    """View all chores due today"""
    schedule_data = await load_schedule()
    
    if not schedule_data:
        embed = discord.Embed(
            title="📋 No Schedule Available",
            description="No schedule has been generated yet.\nAsk an admin to run `!run-schedule`.",
            color=COLOR_WARNING
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
    
    if not today_chores:
        embed = discord.Embed(
            title="📅 No Chores Today",
            description="No chores are due today! 🎉",
            color=COLOR_SUCCESS
        )
        await ctx.send(embed=embed)
        return
    
    # Create embed
    now = datetime.now()
    embed = discord.Embed(
        title=f"📅 Chores for {now.strftime('%A, %B %d')}",
        description="Today's assignments:",
        color=COLOR_INFO,
        timestamp=now
    )
    
    deck_order = ["Zero Deck", "First Deck", "Second Deck", "Third Deck", "Other"]
    for deck in deck_order:
        if deck in today_chores:
            chores_text = ""
            for item in today_chores[deck]:
                assigned = ", ".join(item['assigned'])
                chores_text += f"• **{item['task']}**\n  └ {assigned}\n"
            
            embed.add_field(name=deck, value=chores_text, inline=False)
    
    embed.set_footer(text=f"Total: {sum(len(c) for c in today_chores.values())} chores")
    await ctx.send(embed=embed)


@bot.command(name='ping')
async def ping(ctx):
    """Check if bot is responsive"""
    latency_ms = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        color=COLOR_SUCCESS if latency_ms < 200 else COLOR_WARNING
    )
    embed.add_field(name="Latency", value=f"{latency_ms}ms", inline=True)
    embed.add_field(name="Status", value="✅ Online", inline=True)
    
    # Add schedule file status
    schedule_exists = os.path.exists('schedule.json')
    embed.add_field(
        name="Schedule",
        value="✅ Available" if schedule_exists else "❌ Not generated",
        inline=True
    )
    
    embed.set_footer(text=f"Scheduled run: Sundays at {RUN_TIME_HOUR:02d}:{RUN_TIME_MINUTE:02d}")
    await ctx.send(embed=embed)


# Run the bot
if __name__ == "__main__":
    print("🚀 Starting Discord bot...")
    print(f"📋 Configuration:")
    print(f"   Channel ID: {CHANNEL_ID}")
    print(f"   Run Time: {RUN_TIME_HOUR:02d}:{RUN_TIME_MINUTE:02d}")
    print(f"   Script: {SCRIPT_PATH}")
    print(f"   Python: {PYTHON_CMD}")
    print(f"   Max Retries: {MAX_RETRIES}")
    print(f"   Retry Delay: {RETRY_DELAY}s")
    bot.run(DISCORD_TOKEN)
