# app/services/database.py
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Get the absolute path of the current file (util.py)
current_file_path = Path(__file__).resolve()

# Navigate up the directory tree to reach the project root
env_path = current_file_path.parent.parent.parent / ".env"
load_dotenv(env_path)


def get_supabase():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured")

    return create_client(supabase_url, supabase_key)
