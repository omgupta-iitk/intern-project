import os
from pathlib import Path

from app.services.database import get_supabase
from dotenv import load_dotenv

# Get the absolute path of the current file (util.py)
current_file_path = Path(__file__).resolve()

# Navigate up the directory tree to reach the project root
env_path = current_file_path.parent.parent / ".env"
load_dotenv(env_path)

BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")


def upload_to_supabase_storage(image_bytes, image_name):
    try:
        supabase = get_supabase()
        supabase.storage.from_(BUCKET_NAME).upload(image_name, image_bytes)

        # Get public URL
        response = supabase.storage.from_(BUCKET_NAME).get_public_url(image_name)
        return response
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None


def upload_excel_to_supabase_storage(file_path, filename, bucket_name=BUCKET_NAME):
    try:
        supabase = get_supabase()  # Assuming this returns your Supabase client

        # Read the file as bytes
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Upload to Supabase storage
        supabase.storage.from_(bucket_name).upload(filename, file_bytes)

        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        return public_url
    except Exception as e:
        print(f"Error uploading Excel file: {e}")
        return None
