# app/models/message.py
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    fullName: str
    publicEmail: EmailStr
    phoneNumber: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    clerk_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    content: str
    sender_id: int
    receiver_id: int


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True
