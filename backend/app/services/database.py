# app/services/database.py
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv('/home/om/temp/intern-project/backend/.env')

def get_supabase():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(supabase_url, supabase_key)