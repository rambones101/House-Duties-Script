# Discord Bot Setup - Username Mapping

## The Problem
Discord usernames (like "Fagtive") don't match the names in your `brothers.txt` file. When someone uses `!my-chores`, the bot needs to know which brother name to look up in the schedule.

## The Solution
Edit `config/discord_mapping.json` to map Discord names to brother names.

## How to Fix

### Step 1: Find the Discord Username
- Have the person use `!my-chores` command
- Note their exact Discord username as shown in the server

### Step 2: Find Their Brother Name  
- Check `config/brothers.txt` for their actual name in the roster

### Step 3: Add the Mapping
Edit `config/discord_mapping.json`:

```json
{
  "mappings": {
    "Fagtive": "Henry",
    "Erick(Mr.RAmirez)": "Erick"
  }
}
```

Replace `"Fagtive": "Henry"` with the correct mapping.

### Step 4: Restart the Bot
After editing the file, restart the Discord bot for changes to take effect.

## Example Mappings

```json
{
  "mappings": {
    "Fagtive": "Henry",
    "Gabey": "Gabe", 
    "JP_Official": "Jean Paul",
    "TimTheMan": "Tim",
    "Erick(Mr.RAmirez)": "Erick",
    "MaddoxRocks": "Maddox",
    "KabirK": "Kabir",
    "YutoSan": "Yuto",
    "CarlosTheKing": "Carlos",
    "DanielDude": "Daniel",
    "JeffJeff": "Jeff",
    "SaltyBoy": "Sal",
    "AlexTheGreat": "Alex",
    "AkiraAkira": "Akira"
  }
}
```

## Matching Rules

The bot checks in this order:
1. **Exact match** with server nickname (display name)
2. **Exact match** with username
3. **Case-insensitive match** with either
4. **Fallback**: Uses Discord display name as-is

## Tips

- You don't need to add everyone - only people who want to use bot commands
- Names are case-insensitive ("fagtive" = "Fagtive" = "FAGTIVE")
- Both server nicknames and usernames work
- You can add multiple entries for the same person:
  ```json
  "Fagtive": "Henry",
  "Henry": "Henry",
  "HenryTheHenry": "Henry"
  ```

## Testing

After updating the mapping:
1. Restart the Discord bot
2. Have the person try `!my-chores` again
3. Should now show their assigned chores!

## Troubleshooting

**Still showing "No chores assigned"?**
- Check spelling of both Discord name and brother name
- Make sure brother name exactly matches `brothers.txt`
- Check that they're actually assigned chores in the current week's schedule
- Restart the bot after making changes
