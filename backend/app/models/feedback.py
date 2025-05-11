from datetime import datetime

from pydantic import BaseModel


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


class CommentFeedbackCreate(BaseModel):
    feedback: str
    sentiment: str
    sentiment_label: str
    word_count: int
    adjectives: list[str]


class CommentFeedback(CommentFeedbackCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
