"""
Discord Bot for House Duties Scheduler
Automatically runs the scheduler every Sunday and posts to a Discord channel
"""

import discord
from discord.ext import commands, tasks
import asyncio
import subprocess
import json
from datetime import datetime, time as dt_time
import os
from dotenv import load_dotenv

load_dotenv()

# ===== CONFIGURATION =====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Replace with your bot token
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Replace with your channel ID
RUN_TIME_HOUR = 8  # 8 AM on Sundays
RUN_TIME_MINUTE = 0
SCRIPT_PATH = "house_duties.py"  # Path to the scheduler script
PYTHON_CMD = "python"  # or "python3" or full path like "C:/Python312/python.exe"
# ========================

# Bot setup with minimal intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'🤖 {bot.user} is now online!')
    print(f'📅 Scheduled to run every Sunday at {RUN_TIME_HOUR:02d}:{RUN_TIME_MINUTE:02d}')
    weekly_scheduler.start()


@tasks.loop(time=dt_time(hour=RUN_TIME_HOUR, minute=RUN_TIME_MINUTE))
async def weekly_scheduler():
    """Runs every day at the specified time, but only executes on Sundays"""
    now = datetime.now()
    
    # Only run on Sundays (weekday 6)
    if now.weekday() != 6:
        print(f"⏭️  Skipping - today is {now.strftime('%A')} (not Sunday)")
        return
    
    print(f"🏃 Running house duties scheduler on {now.strftime('%Y-%m-%d %H:%M')}")
    
    try:
        # Run the scheduler script
        result = subprocess.run(
            [PYTHON_CMD, SCRIPT_PATH],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode != 0:
            error_msg = f"❌ **Scheduler failed!**\n```\n{result.stderr}\n```"
            print(error_msg)
            await send_message(error_msg)
            return
        
        # Read the generated schedule
        schedule_text = result.stdout
        
        # Also read schedule.json for structured data
        with open('schedule.json', 'r') as f:
            schedule_data = json.load(f)
        
        # Format and send the schedule
        await send_schedule(schedule_text, schedule_data)
        
        print("✅ Schedule posted to Discord successfully!")
        
    except Exception as e:
        error_msg = f"❌ **Error running scheduler:**\n```\n{str(e)}\n```"
        print(error_msg)
        await send_message(error_msg)


async def send_schedule(terminal_output: str, schedule_data: list):
    """Format and send the schedule to Discord"""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Could not find channel with ID {CHANNEL_ID}")
        return
    
    # Send header message
    now = datetime.now()
    header = f"""
📋 **WEEKLY HOUSE DUTIES SCHEDULE**
Generated: {now.strftime('%B %d, %Y at %I:%M %p')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    await channel.send(header)
    
    # Group schedule by date and deck
    by_date = {}
    for item in schedule_data:
        date = item['due'].split(' ')[0]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(item)
    
    # Send schedule by date
    for date_str in sorted(by_date.keys()):
        dt = datetime.fromisoformat(date_str)
        dow = dt.strftime('%A')
        
        # Build message for this day
        day_msg = f"**{dow}, {dt.strftime('%B %d')}**\n"
        
        # Group by deck
        by_deck = {}
        for item in by_date[date_str]:
            deck = item['deck']
            if deck not in by_deck:
                by_deck[deck] = []
            by_deck[deck].append(item)
        
        # Add tasks by deck
        deck_order = ["Zero Deck", "First Deck", "Second Deck", "Third Deck", "Other"]
        for deck in deck_order:
            if deck in by_deck:
                day_msg += f"\n*{deck}*\n"
                for item in by_deck[deck]:
                    assigned = ", ".join(item['assigned'])
                    day_msg += f"• **{item['task']}**: {assigned}\n"
        
        # Split message if too long (Discord 2000 char limit)
        if len(day_msg) > 1900:
            chunks = [day_msg[i:i+1900] for i in range(0, len(day_msg), 1900)]
            for chunk in chunks:
                await channel.send(chunk)
        else:
            await channel.send(day_msg)
    
    # Send footer
    footer = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✅ Good luck with your duties this week!"
    await channel.send(footer)


async def send_message(text: str):
    """Send a simple message to the configured channel"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(text)


# Manual trigger command (optional - lets you test without waiting for Sunday)
@bot.command(name='runduries')
@commands.has_permissions(administrator=True)
async def manual_run(ctx):
    """Manually trigger the scheduler (admin only)"""
    await ctx.send("🔄 Running scheduler manually...")
    await weekly_scheduler()


# Test command
@bot.command(name='ping')
async def ping(ctx):
    """Check if bot is responsive"""
    await ctx.send(f'🏓 Pong! Latency: {round(bot.latency * 1000)}ms')


# Run the bot
if __name__ == "__main__":
    if DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Please set your Discord bot token in DISCORD_TOKEN")
        print("📖 See setup instructions in DISCORD_BOT_SETUP.md")
    else:
        print("🚀 Starting Discord bot...")
        bot.run(DISCORD_TOKEN)
