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

Open `discord_bot.py` and edit:

```python
DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Paste your bot token from Step 1
CHANNEL_ID = 123456789012345678  # Paste your channel ID from Step 3
RUN_TIME_HOUR = 8  # Hour to run (24-hour format, e.g., 8 = 8 AM, 20 = 8 PM)
RUN_TIME_MINUTE = 0  # Minute to run
```

**⚠️ IMPORTANT**: Keep your token secret! Don't commit it to git.

### Better: Use Environment Variables

Instead of hardcoding the token, create a `.env` file:

```env
DISCORD_TOKEN=your_token_here
CHANNEL_ID=123456789012345678
```

Then install `python-dotenv`:
```powershell
pip install python-dotenv
```

And modify `discord_bot.py` to load from `.env`:
```python
from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
```

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
