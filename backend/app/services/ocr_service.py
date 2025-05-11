import os
import re
import uuid

import cv2
import pandas as pd
from app.services.database import get_supabase
from dotenv import load_dotenv
from img2table.document import Image
from img2table.ocr import PaddleOCR
from paddleocr import PaddleOCR as PaddleOCRV2

load_dotenv("/home/om/temp/intern-project/backend/.env")

BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME")


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


class ReceiptOCRService:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.raw_text = ""
        self.structured_data = {}
        self.parsed = {"key_values": {}, "items": [], "meta": []}

    def run_ocr(self):
        img = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        if self.image_path is None:
            raise FileNotFoundError(f"Image not found at {self.image_path}")

        ocr = PaddleOCRV2(
            use_angle_cls=True,
            lang="en",
            use_gpu=False,
            enable_mkldnn=True,
        )
        result = ocr.ocr(img)

        self.raw_text = "\n".join(
            word_info[1][0] for line in result for word_info in line
        )
        return self.raw_text

    def parse_items(self):
        lines = [
            line.strip() for line in self.raw_text.strip().splitlines() if line.strip()
        ]
        i = 0
        while i < len(lines):
            line = lines[i].lower()

            # Match keyword: value, possibly on next line
            if ":" in line:
                match = re.split(r"[:]", lines[i], maxsplit=1)
                key = match[0].strip()
                value = match[1].strip()
                if not value and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    value = next_line
                    i += 1
                self.parsed["key_values"][key] = value
            elif re.match(r"^\d+\s*(x\s*)?.+", lines[i], re.IGNORECASE):
                quantity_match = re.match(
                    r"^(\d+)\s*(x\s*)?(.*)", lines[i], re.IGNORECASE
                )
                if quantity_match:
                    quantity = int(quantity_match.group(1))
                    name = quantity_match.group(3).strip()
                    price = None
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if re.match(r"^\$?\d+(\.\d{2})?$", next_line):
                            price = next_line
                            i += 1
                    if price:
                        self.parsed["items"].append(
                            {"quantity": quantity, "name": name, "price": price}
                        )
                    else:
                        self.parsed["meta"].append(lines[i])
            else:
                self.parsed["meta"].append(lines[i])
            i += 1
        return self.parsed

    def process(self):
        self.run_ocr()
        return self.parse_items()


def table_recognizer(image_path: str):
    """
    Recognizes tables in the image and returns structured data.
    """
    img = Image(src=image_path)

    ocr = PaddleOCR(lang="en")

    filename = f"{uuid.uuid4().hex}_table-record.xlsx"
    file_path = f"/home/om/temp/intern-project/backend/tmp_uploads/{filename}"
    img.to_xlsx(file_path, ocr=ocr)
    df = pd.read_excel(file_path)
    json_string = df.to_json()

    public_url = upload_excel_to_supabase_storage(file_path, filename)

    if public_url:
        print(f"File uploaded successfully: {public_url}")
    else:
        print("Failed to upload file.")

    return df, {"structured_data": json_string, "excel_public_url": public_url}
