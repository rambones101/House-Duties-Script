"""Scheduler execution and schedule loading utilities."""
import subprocess
import asyncio
import json
import os
from typing import Optional, List, Dict, Tuple


async def load_schedule(filepath: str = "data/schedule.json") -> Optional[List[Dict]]:
    """Load schedule.json with error handling."""
    try:
        if not os.path.exists(filepath):
            print(f"❌ Schedule file not found: {filepath}")
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error: {filepath} is invalid JSON")
        return None
    except Exception as e:
        print(f"❌ Error loading schedule: {e}")
        return None


async def run_scheduler_with_retry(
    python_cmd: str,
    script_path: str,
    max_retries: int = 3,
    retry_delay: int = 5
) -> Tuple[bool, Optional[str], Optional[List[Dict]]]:
    """
    Run the scheduler with retry logic.
    
    Returns:
        Tuple of (success, error_message, schedule_data)
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🏃 Running scheduler (attempt {attempt}/{max_retries})...")
            
            result = subprocess.run(
                [python_cmd, script_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(script_path)),
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
                
                if attempt < max_retries:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    return False, error_msg, None
                    
        except subprocess.TimeoutExpired:
            error_msg = "Scheduler timed out after 60 seconds"
            print(f"⏱️ {error_msg}")
            
            if attempt < max_retries:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                return False, error_msg, None
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            
            if attempt < max_retries:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                return False, error_msg, None
    
    return False, "All retry attempts failed", None
