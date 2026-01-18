"""Main Discord bot implementation with task scheduling."""
import discord
from discord.ext import commands, tasks
from datetime import datetime, time as dt_time

from .config import BotConfig, COLOR_ERROR, COLOR_WARNING, COLOR_INFO
from .commands import setup_commands, send_schedule_embeds
from .scheduler import run_scheduler_with_retry
from .embeds import create_status_embed, create_error_embed


# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load configuration
config = BotConfig()


@bot.event
async def on_ready():
    """Called when bot successfully connects to Discord."""
    print(f'🤖 {bot.user} is now online!')
    print(f'📅 Scheduled to run every Sunday at {config.RUN_TIME_HOUR:02d}:{config.RUN_TIME_MINUTE:02d}')
    print(f'💬 Command prefix: !')
    print(f'📝 Available commands: run-schedule, my-chores, chores-today, ping')
    weekly_scheduler.start()


@bot.event
async def on_command_error(ctx, error):
    """Global error handler for better error messages."""
    if isinstance(error, commands.MissingPermissions):
        embed = create_status_embed(
            "❌ Permission Denied",
            "You don't have permission to use this command.",
            "error"
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        embed = create_status_embed(
            "❓ Command Not Found",
            f"Use `!help` to see available commands.",
            "warning"
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = create_status_embed(
            "⚠️ Missing Argument",
            f"Missing required argument: `{error.param.name}`\nUse `!help {ctx.command}` for usage.",
            "warning"
        )
        await ctx.send(embed=embed)
    else:
        # Log unexpected errors
        print(f"❌ Unexpected error in {ctx.command}: {error}")
        embed = create_status_embed(
            "❌ Error",
            f"An unexpected error occurred: {str(error)}",
            "error"
        )
        await ctx.send(embed=embed)


@tasks.loop(time=dt_time(hour=config.RUN_TIME_HOUR, minute=config.RUN_TIME_MINUTE))
async def weekly_scheduler():
    """Runs every day at the specified time, but only executes on Sundays."""
    now = datetime.now()
    
    # Only run on Sundays (weekday 6)
    if now.weekday() != 6:
        print(f"⏭️  Skipping - today is {now.strftime('%A')} (not Sunday)")
        return
    
    print(f"📅 Sunday detected - running house duties scheduler")
    
    channel = bot.get_channel(config.CHANNEL_ID)
    if not channel:
        print(f"❌ Could not find channel with ID {config.CHANNEL_ID}")
        return
    
    # Send "generating" message
    status_msg = await channel.send(embed=create_status_embed(
        "🔄 Generating Schedule",
        "Please wait while the schedule is being generated...",
        "info"
    ))
    
    # Run scheduler with retry
    success, error, schedule_data = await run_scheduler_with_retry(
        config.PYTHON_CMD,
        config.SCRIPT_PATH,
        config.MAX_RETRIES,
        config.RETRY_DELAY
    )
    
    if success and schedule_data:
        # Delete status message
        await status_msg.delete()
        
        # Send schedule with embeds
        await send_schedule_embeds(channel, schedule_data)
        print("✅ Schedule posted to Discord successfully!")
    else:
        # Update status message with error
        await status_msg.edit(embed=create_error_embed(error, config.MAX_RETRIES))


def run_bot():
    """Start the Discord bot."""
    # Register commands
    setup_commands(bot, config)
    
    # Print startup info
    print("🚀 Starting Discord bot...")
    print(f"📋 Configuration:")
    print(f"   Channel ID: {config.CHANNEL_ID}")
    print(f"   Run Time: {config.RUN_TIME_HOUR:02d}:{config.RUN_TIME_MINUTE:02d}")
    print(f"   Script: {config.SCRIPT_PATH}")
    print(f"   Python: {config.PYTHON_CMD}")
    print(f"   Max Retries: {config.MAX_RETRIES}")
    print(f"   Retry Delay: {config.RETRY_DELAY}s")
    
    # Run bot
    bot.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()
