import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, List

import requests
from app.analyzers.Bills_analyzer import BillsAnalysis
from app.analyzers.feedback_analyzer import CommentFeedbackAnalyzer, FeedbackAnalyzer
from app.analyzers.Revenue_analyzer import RevenueAnalysis
from app.core.auth import get_current_user
from app.graphql.schema import schema
from app.models.feedback import CommentFeedbackCreate, FeedbackCreate
from app.models.message import User, UserCreate
from app.services.database import get_supabase
from app.services.feedback_enrichment import FeedbackEnrichment
from app.services.ocr_service import ReceiptOCRService, table_recognizer
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
)
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

# Get the absolute path of the current file (util.py)
current_file_path = Path(__file__).resolve()

# Navigate up the directory tree to reach the project root
env_path = current_file_path.parent / ".env"
load_dotenv(env_path)

INSTAGRAM_MEDIA_ID = os.getenv("INSTAGRAM_MEDIA_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_API_URL = os.getenv("INSTAGRAM_API_URL")

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

UPLOAD_DIR = f"{current_file_path.parent}/temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your React app's origin
    allow_credentials=True,
    allow_methods=["*"],  # Or specify ["GET", "POST", etc.]
    allow_headers=["*"],  # Or specify specific headers
)

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))


manager = ConnectionManager()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            # Process the message if needed
    except:
        manager.disconnect(user_id)


@app.post("/create-user/", response_model=User)
async def create_user(user: UserCreate, clerk_id: str = Depends(get_current_user)):
    supabase = get_supabase()

    # Check if user already exists
    existing_user = (
        supabase.table("users").select("*").eq("clerk_id", clerk_id).execute()
    )
    if existing_user.data:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    user_data = user.model_dump()
    user_data["clerk_id"] = clerk_id
    new_user = supabase.table("users").insert(user_data).execute()

    return new_user.data[0]


@app.get("/users/me", response_model=User)
async def read_current_user(clerk_id: str = Depends(get_current_user)):
    supabase = get_supabase()
    user = supabase.table("users").select("*").eq("clerk_id", clerk_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")
    return user.data[0]


@app.get("/users", response_model=list[User])
async def read_users(
    skip: int = 0, limit: int = 10, clerk_id: str = Depends(get_current_user)
):
    supabase = get_supabase()
    users = supabase.table("users").select("*").range(skip, skip + limit).execute()
    return users.data


@app.post("/bill-receipt-enrichment")
async def bill_receipt_enrichment(
    files: List[UploadFile] = File(...),
):
    UPLOAD_DIR = "tmp_uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    all_extracted_data = []

    try:
        # Process each file
        for file in files:
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # OCR Process
            ocr = ReceiptOCRService(file_path)
            extracted_text = ocr.process()

            # Add to collection
            if extracted_text:
                all_extracted_data.append(extracted_text)

            # Clean up
            os.remove(file_path)
        # If no data was extracted successfully
        if not all_extracted_data:
            return {"error": "Could not extract data from any of the provided files"}

        # Analyze the collected data
        analyzer = BillsAnalysis(all_extracted_data)
        analysis_results = analyzer.analyze()

        return {"structured_data": all_extracted_data, "analysis": analysis_results}

    except Exception as e:
        logger.error(f"Error processing bill receipts: {str(e)}")
        return {"error": f"An error occurred during processing: {str(e)}"}


@app.post("/feedback-enrichment")
async def feedback_enrichment(feedbacks: list[FeedbackCreate]):
    feedbacksData = []
    for feedback in feedbacks:
        # Validate and clean the feedback
        if not isinstance(feedback, FeedbackCreate):
            raise HTTPException(status_code=400, detail="Invalid feedback format")

        # Convert to dictionary and validate
        feedback_data = FeedbackEnrichment(feedback).get_data()
        feedbacksData.append(feedback_data)

    analyis = FeedbackAnalyzer(feedbacksData).analyze()

    return {
        "message": "Feedbacks processed successfully",
        "data": feedbacksData,
        "analysis": analyis,
    }


@app.post("/tabular_record")
async def tabular_record(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR Process
    df, data = table_recognizer(file_path)
    analyzer = RevenueAnalysis(df)
    basic_analysis = analyzer.analyze()
    recomendations = analyzer.generate_recommendations(basic_analysis)

    # Optionally delete after processing
    os.remove(file_path)

    return {
        "structured_data": data,
        "analysis": basic_analysis,
        "recommendations": recomendations,
    }


@app.get("/comment-persist-analyze")
async def comment_persist_analyze():
    supabase = get_supabase()

    comments_data = requests.get(
        "https://graph.instagram.com/"
        + INSTAGRAM_MEDIA_ID
        + "/comments?access_token="
        + INSTAGRAM_ACCESS_TOKEN
    ).json()

    comments = []
    for comment in comments_data["data"]:
        comment_id = comment["id"]
        content = requests.get(
            "https://graph.instagram.com/v22.0/"
            + comment_id
            + "?fields=id,text&access_token="
            + INSTAGRAM_ACCESS_TOKEN
        ).json()
        comments.append(content["text"])

    feedbacks = []
    for comment in comments:
        feedback = CommentFeedbackCreate(
            feedback=comment,
            sentiment="",
            sentiment_label="",
            word_count=0,
            adjectives=[],
        )
        feedbacks.append(feedback)
    feedbacksData = []
    for feedback in feedbacks:
        # Validate and clean the feedback
        if not isinstance(feedback, CommentFeedbackCreate):
            raise HTTPException(status_code=400, detail="Invalid feedback format")

        # Convert to dictionary and validate
        feedback_data = FeedbackEnrichment(feedback).get_data()
        feedbacksData.append(feedback_data)

    # Data persistence to Supabase database
    supabase.table("comment").insert(feedbacksData).execute()

    analyis = CommentFeedbackAnalyzer(feedbacksData).analyze()
    return {
        "message": "Comment Feedbacks processed successfully",
        "data": feedbacksData,
        "analysis": analyis,
    }
