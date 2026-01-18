# Discord Bot Setup Guide

## Step 1: Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "House Duties Bot")
3. Go to the "Bot" tab on the left
4. Click "Add Bot" → "Yes, do it!"
5. Under "Token", click "Reset Token" and copy it (you'll need this!)
6. Enable these **Privileged Gateway Intents**:
   - ✅ MESSAGE CONTENT INTENT

## Step 2: Invite Bot to Your Server

1. Go to "OAuth2" → "URL Generator" in the left sidebar
2. Select scopes:
   - ✅ `bot`
3. Select bot permissions:
   - ✅ Send Messages
   - ✅ Read Messages/View Channels
   - ✅ Embed Links
4. Copy the generated URL at the bottom
5. Open it in your browser and invite the bot to your server

## Step 3: Get Your Channel ID

1. In Discord, enable Developer Mode:
   - Settings → Advanced → Developer Mode → ON
2. Right-click the channel where you want the bot to post
3. Click "Copy Channel ID"

## Step 4: Install Dependencies

```powershell
pip install discord.py
```

## Step 5: Configure the Bot

### Create Environment Configuration

1. Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and fill in your values:
   ```env
   # Required
   DISCORD_TOKEN=your_bot_token_from_step_1
   CHANNEL_ID=your_channel_id_from_step_3
   
   # Optional (defaults shown)
   RUN_TIME_HOUR=8
   RUN_TIME_MINUTE=0
   SCRIPT_PATH=house_duties.py
   PYTHON_CMD=python
   ```

3. **⚠️ IMPORTANT**: Keep your `.env` file secret! It's already in `.gitignore`.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | ✅ Yes | - | Your Discord bot token |
| `CHANNEL_ID` | ✅ Yes | - | Discord channel ID for posting |
| `RUN_TIME_HOUR` | No | 8 | Hour to run (0-23, 24-hour format) |
| `RUN_TIME_MINUTE` | No | 0 | Minute to run (0-59) |
| `SCRIPT_PATH` | No | house_duties.py | Path to scheduler script |
| `PYTHON_CMD` | No | python | Python command to execute |

**Examples:**
- Run at 9:30 AM: `RUN_TIME_HOUR=9` and `RUN_TIME_MINUTE=30`
- Run at 8:00 PM: `RUN_TIME_HOUR=20` and `RUN_TIME_MINUTE=0`
- Use Python 3.12: `PYTHON_CMD=python3.12`

## Step 6: Run the Bot

### Option A: Keep Terminal Open (Testing)
```powershell
python discord_bot.py
```

The bot will stay running and automatically post every Sunday at the configured time.

### Option B: Run as Background Service (Production)

#### Windows (using Task Scheduler):
1. Open Task Scheduler
2. Create Basic Task → "House Duties Bot"
3. Trigger: "When the computer starts"
4. Action: "Start a program"
   - Program: `C:\Python312\python.exe` (your Python path)
   - Arguments: `discord_bot.py`
   - Start in: `C:\Users\erick\OneDrive\Documents\Triangle Documents\House Duties Script`
5. Check "Run whether user is logged on or not"

#### Alternative: Keep Terminal Running with `nohup` (if using WSL/Linux):
```bash
nohup python discord_bot.py > bot.log 2>&1 &
```

## Step 7: Test the Bot

In Discord, type:
```
!ping
```

The bot should respond with "🏓 Pong!"

To manually trigger the schedule (admin only):
```
!runduries
```

## Troubleshooting

### Bot is offline
- Check that `discord_bot.py` is still running
- Verify your token is correct
- Check the console for error messages

### Bot doesn't post on Sunday
- Check `RUN_TIME_HOUR` and `RUN_TIME_MINUTE` are correct
- The bot checks every day at that time, but only posts on Sundays
- Verify your system clock is correct

### "Could not find channel"
- Make sure `CHANNEL_ID` is correct
- Ensure the bot has permission to view and send messages in that channel

### "Missing permissions"
- Go back to the OAuth2 URL Generator and make sure the bot has "Send Messages" permission
- Re-invite the bot with the updated permissions

## Running on a VPS/Cloud Server

For 24/7 uptime, consider running on:
- **Heroku**: Free tier available (with limitations)
- **DigitalOcean**: $5/month droplet
- **AWS EC2**: Free tier available for 12 months
- **Raspberry Pi**: Run it at home 24/7

### Example: Running on a VPS with systemd

1. Create `/etc/systemd/system/house-duties-bot.service`:
```ini
[Unit]
Description=House Duties Discord Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/House Duties Script
ExecStart=/usr/bin/python3 discord_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl enable house-duties-bot
sudo systemctl start house-duties-bot
sudo systemctl status house-duties-bot
```

## Commands

- `!ping` - Check if bot is online
- `!runduries` - Manually run the scheduler (requires admin permissions)

## Security Notes

1. **Never share your bot token** - treat it like a password
2. Add `.env` to `.gitignore` if using version control
3. If token is compromised, regenerate it in the Developer Portal
4. Only grant necessary permissions to the bot
