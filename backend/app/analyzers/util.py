from app.services.database import get_supabase
from dotenv import load_dotenv
import os

load_dotenv("/home/om/temp/intern-project/backend/.env")

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
