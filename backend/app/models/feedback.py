from pydantic import BaseModel, EmailStr
from datetime import datetime

class feedbackBase(BaseModel):
    name: str
    rating: int
    visit_date: str
    feedback: str

class FeedbackCreate(feedbackBase):
    pass

class Feedback(feedbackBase):
    id: int
    created_at: datetime
    sentiment: str
    sentiment_label: str
    word_count: int
    adjectives: list[str]

    class Config:
        from_attributes = True