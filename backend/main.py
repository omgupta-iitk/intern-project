from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
import os
import uuid
import shutil
from app.services.ocr_service import ReceiptOCRService, table_recognizer
from app.models.message import User, UserCreate
from app.core.auth import get_current_user
from app.services.database import get_supabase
from app.graphql.schema import schema
from fastapi import HTTPException, Depends
from strawberry.fastapi import GraphQLRouter
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.models.feedback import Feedback, FeedbackCreate
from app.services.feedback_service import FeedbackAnalyzer
from app.services.trend_engagement_analyzer import RevenueAnalysis
import json
from typing import Dict

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

UPLOAD_DIR = "tmp_uploads"
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
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@app.post("/create-user/", response_model=User)
async def create_user(user: UserCreate, clerk_id: str = Depends(get_current_user)):
    supabase = get_supabase()

    # Check if user already exists
    existing_user = supabase.table("users").select("*").eq("clerk_id", clerk_id).execute()
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
async def read_users(skip: int = 0, limit: int = 10, clerk_id: str = Depends(get_current_user)):
    supabase = get_supabase()
    users = supabase.table("users").select("*").range(skip, skip + limit).execute()
    return users.data

@app.post("/extract_text_from_receipt")
async def extract_text_from_receipt(
    file: UploadFile = File(...),
):
    UPLOAD_DIR = "tmp_uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR Process
    ocr = ReceiptOCRService(file_path, tabular_format)
    extracted_text = ocr.process()

    # Optionally delete after processing
    os.remove(file_path)

    return {"structured_data": extracted_text}

@app.post("/feedback")
async def feedback(feedback: FeedbackCreate):
    supabase = get_supabase()

    feedbackAnalzer = FeedbackAnalyzer(feedback)
    analysed_feedback = feedbackAnalzer.get_data()
    supabase.table("feedback").insert(analysed_feedback).execute()

    return {"message": "Feedback processed successfully", "data": analysed_feedback}


@app.post("/tabular_record")
async def tabular_record(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR Process
    df, data = table_recognizer(file_path)
    print(data)
    analyzer = RevenueAnalysis(df)
    basic_analysis = analyzer.analyze()
    recomendations = analyzer.generate_recommendations(basic_analysis)

    # Optionally delete after processing
    os.remove(file_path)

    return {"structured_data": data, "analysis": basic_analysis, "recommendations": recomendations}