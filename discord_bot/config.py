"""Configuration management for Discord bot."""
import os
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    """Discord bot configuration from environment variables."""
    
    def __init__(self):
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        self.CHANNEL_ID = os.getenv("CHANNEL_ID")
        self.RUN_TIME_HOUR = int(os.getenv("RUN_TIME_HOUR", "8"))
        self.RUN_TIME_MINUTE = int(os.getenv("RUN_TIME_MINUTE", "0"))
        self.SCRIPT_PATH = os.getenv("SCRIPT_PATH", "house_duties.py")
        self.PYTHON_CMD = os.getenv("PYTHON_CMD", "python")
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
        
        self._validate()
    
    def _validate(self):
        """Validate configuration values."""
        if not self.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required. See .env.example")
        
        if not self.CHANNEL_ID:
            raise ValueError("CHANNEL_ID environment variable is required. See .env.example")
        
        try:
            self.CHANNEL_ID = int(self.CHANNEL_ID)
        except ValueError:
            raise ValueError(f"CHANNEL_ID must be a valid integer, got: {self.CHANNEL_ID}")
        
        if not (0 <= self.RUN_TIME_HOUR <= 23):
            raise ValueError(f"RUN_TIME_HOUR must be 0-23, got: {self.RUN_TIME_HOUR}")
        
        if not (0 <= self.RUN_TIME_MINUTE <= 59):
            raise ValueError(f"RUN_TIME_MINUTE must be 0-59, got: {self.RUN_TIME_MINUTE}")


# Color constants for embeds
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
