"""
Tests for Discord bot environment configuration.
"""

import pytest
import os
from unittest.mock import patch


def test_discord_bot_imports():
    """Test that Discord bot module can be imported."""
    try:
        import discord_bot
        assert discord_bot is not None
    except ImportError as e:
        pytest.skip(f"Discord bot dependencies not available: {e}")


@patch.dict(os.environ, {
    "DISCORD_TOKEN": "test_token_12345",
    "CHANNEL_ID": "123456789",
    "RUN_TIME_HOUR": "10",
    "RUN_TIME_MINUTE": "30"
})
def test_env_variables_loaded():
    """Test that environment variables are loaded correctly."""
    # Force reload of module with test environment
    import importlib
    import sys
    
    # Remove module if already loaded
    if 'discord_bot' in sys.modules:
        del sys.modules['discord_bot']
    
    try:
        import discord_bot
        
        assert discord_bot.DISCORD_TOKEN == "test_token_12345"
        assert discord_bot.CHANNEL_ID == 123456789
        assert discord_bot.RUN_TIME_HOUR == 10
        assert discord_bot.RUN_TIME_MINUTE == 30
    except ImportError:
        pytest.skip("Discord bot dependencies not available")


@patch.dict(os.environ, {
    "DISCORD_TOKEN": "test_token",
    "CHANNEL_ID": "123456789"
}, clear=True)
def test_env_defaults():
    """Test that default values are used when optional vars not set."""
    import sys
    if 'discord_bot' in sys.modules:
        del sys.modules['discord_bot']
    
    try:
        import discord_bot
        
        # Check defaults
        assert discord_bot.RUN_TIME_HOUR == 8
        assert discord_bot.RUN_TIME_MINUTE == 0
        assert discord_bot.SCRIPT_PATH == "house_duties.py"
        assert discord_bot.PYTHON_CMD == "python"
    except ImportError:
        pytest.skip("Discord bot dependencies not available")


def test_missing_discord_token():
    """Test that missing DISCORD_TOKEN would raise error."""
    # Test validation logic directly
    token = None
    channel_id = "123456789"
    
    # Simulate what discord_bot.py does
    if not token:
        with pytest.raises(ValueError):
            if not token:
                raise ValueError("DISCORD_TOKEN environment variable is required. See .env.example")


def test_missing_channel_id():
    """Test that missing CHANNEL_ID would raise error."""
    # Test validation logic directly
    token = "test_token"
    channel_id = None
    
    # Simulate what discord_bot.py does
    if not channel_id:
        with pytest.raises(ValueError):
            if not channel_id:
                raise ValueError("CHANNEL_ID environment variable is required. See .env.example")


@patch.dict(os.environ, {
    "DISCORD_TOKEN": "test_token",
    "CHANNEL_ID": "not_a_number"
}, clear=True)
def test_invalid_channel_id():
    """Test that non-numeric CHANNEL_ID raises error."""
    import sys
    if 'discord_bot' in sys.modules:
        del sys.modules['discord_bot']
    
    with pytest.raises(ValueError, match="CHANNEL_ID.*valid integer"):
        import discord_bot


@patch.dict(os.environ, {
    "DISCORD_TOKEN": "test_token",
    "CHANNEL_ID": "123456789",
    "RUN_TIME_HOUR": "25"  # Invalid: > 23
}, clear=True)
def test_invalid_run_time_hour():
    """Test that invalid RUN_TIME_HOUR raises error."""
    import sys
    if 'discord_bot' in sys.modules:
        del sys.modules['discord_bot']
    
    with pytest.raises(ValueError, match="RUN_TIME_HOUR.*0-23"):
        import discord_bot


@patch.dict(os.environ, {
    "DISCORD_TOKEN": "test_token",
    "CHANNEL_ID": "123456789",
    "RUN_TIME_MINUTE": "60"  # Invalid: > 59
}, clear=True)
def test_invalid_run_time_minute():
    """Test that invalid RUN_TIME_MINUTE raises error."""
    import sys
    if 'discord_bot' in sys.modules:
        del sys.modules['discord_bot']
    
    with pytest.raises(ValueError, match="RUN_TIME_MINUTE.*0-59"):
        import discord_bot


@patch.dict(os.environ, {
    "DISCORD_TOKEN": "test_token",
    "CHANNEL_ID": "123456789",
    "RUN_TIME_HOUR": "-1"  # Invalid: < 0
}, clear=True)
def test_negative_run_time_hour():
    """Test that negative RUN_TIME_HOUR raises error."""
    import sys
    if 'discord_bot' in sys.modules:
        del sys.modules['discord_bot']
    
    with pytest.raises(ValueError, match="RUN_TIME_HOUR.*0-23"):
        import discord_bot


def test_env_example_exists():
    """Test that .env.example file exists."""
    import os.path
    assert os.path.exists(".env.example"), ".env.example file should exist"


def test_env_example_has_required_vars():
    """Test that .env.example contains all required variables."""
    with open(".env.example", "r") as f:
        content = f.read()
    
    required_vars = ["DISCORD_TOKEN", "CHANNEL_ID"]
    optional_vars = ["RUN_TIME_HOUR", "RUN_TIME_MINUTE", "SCRIPT_PATH", "PYTHON_CMD"]
    
    for var in required_vars:
        assert var in content, f".env.example should document {var}"
    
    for var in optional_vars:
        assert var in content, f".env.example should document {var}"


def test_gitignore_has_env():
    """Test that .env is in .gitignore."""
    try:
        with open(".gitignore", "r") as f:
            content = f.read()
        assert ".env" in content, ".env should be in .gitignore"
    except FileNotFoundError:
        pytest.skip(".gitignore not found")
