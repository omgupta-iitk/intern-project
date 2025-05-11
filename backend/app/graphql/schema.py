import traceback
from typing import List, Optional

import strawberry
from app.core.auth import get_current_clerk_id
from dotenv import load_dotenv
from strawberry.types import Info

from ..services.database import get_supabase

load_dotenv("/home/om/temp/intern-project/backend/.env")


@strawberry.type
class UserType:
    id: int
    clerk_id: str
    fullName: str
    publicEmail: str
    phoneNumber: str
    created_at: str


@strawberry.type
class MessageType:
    id: int
    content: str
    senderId: int
    receiverId: int
    createdAt: str
    isRead: bool


async def get_user_from_token(info: Info) -> Optional[UserType]:
    request = info.context["request"]
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        print("No Authorization header")
        return None

    try:
        token = auth_header.split(" ")[1]

        clerk_id = await get_current_clerk_id(token)

        if not clerk_id:
            print("Invalid token or clerk_id not found")
            return None

        supabase = get_supabase()
        user_data = (
            supabase.table("users").select("*").eq("clerk_id", clerk_id).execute()
        )

        if not user_data.data:
            print(f"No user found for clerk_id: {clerk_id}")
            return None

        return UserType(**user_data.data[0])
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        traceback.print_exc()
        return None


@strawberry.type
class Query:
    @strawberry.field
    async def messages(
        self, info: Info, receiverId: Optional[int] = None
    ) -> List[MessageType]:
        current_user = await get_user_from_token(info)
        if not current_user:
            raise Exception("Not authenticated")

        supabase = get_supabase()

        if receiverId:
            # Only fetch messages between current user and specified receiver
            query = (
                supabase.table("messages")
                .select("id, content, sender_id, receiver_id, created_at, is_read")
                .or_(
                    f"and(sender_id.eq.{current_user.id},receiver_id.eq.{receiverId}),and(sender_id.eq.{receiverId},receiver_id.eq.{current_user.id})"
                )
                .order("created_at", desc=True)
            )
        else:
            # Fetch all messages for current user
            query = (
                supabase.table("messages")
                .select("id, content, sender_id, receiver_id, created_at, is_read")
                .or_(f"sender_id.eq.{current_user.id},receiver_id.eq.{current_user.id}")
                .order("created_at", desc=True)
            )

        messages_data = query.execute()

        messages = []
        for msg in messages_data.data:
            message = MessageType(
                id=msg["id"],
                content=msg["content"],
                senderId=msg["sender_id"],
                receiverId=msg["receiver_id"],
                createdAt=msg["created_at"],
                isRead=msg["is_read"],
            )
            messages.append(message)

        return messages


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def sendMessage(
        self, info: Info, receiverId: int, content: str
    ) -> MessageType:
        current_user = await get_user_from_token(info)
        if not current_user:
            raise Exception("Not authenticated")

        if len(content.strip()) == 0:
            raise Exception("Message content cannot be empty")

        supabase = get_supabase()

        # Check if receiver exists
        receiver_data = (
            supabase.table("users").select("id").eq("id", receiverId).execute()
        )
        if not receiver_data.data:
            raise Exception("Receiver not found")

        # Insert message
        message_data = {
            "content": content,
            "sender_id": current_user.id,
            "receiver_id": receiverId,
            "is_read": False,
        }

        new_message = supabase.table("messages").insert(message_data).execute()

        if not new_message.data:
            raise Exception("Failed to create message")

        message_id = new_message.data[0]["id"]

        # Get the message details
        message_data = (
            supabase.table("messages")
            .select("id, content, sender_id, receiver_id, created_at, is_read")
            .eq("id", message_id)
            .single()
            .execute()
        )

        msg = message_data.data

        # Create message object
        message = MessageType(
            id=msg["id"],
            content=msg["content"],
            senderId=msg["sender_id"],
            receiverId=msg["receiver_id"],
            createdAt=msg["created_at"],
            isRead=msg["is_read"],
        )

        # Get sender and receiver data for WebSocket
        sender_data = (
            supabase.table("users")
            .select("id, fullName")
            .eq("id", current_user.id)
            .single()
            .execute()
        )
        receiver_data = (
            supabase.table("users")
            .select("id, fullName")
            .eq("id", receiverId)
            .single()
            .execute()
        )

        # Send message via WebSocket to the receiver
        try:
            from main import manager

            # Format message for WebSocket
            ws_message = {
                "id": msg["id"],
                "content": msg["content"],
                "senderId": msg["sender_id"],
                "receiverId": msg["receiver_id"],
                "createdAt": msg["created_at"],
                "isRead": msg["is_read"],
                # Include sender and receiver info for display
                "sender": {
                    "id": sender_data.data["id"],
                    "fullName": sender_data.data["fullName"],
                },
                "receiver": {
                    "id": receiver_data.data["id"],
                    "fullName": receiver_data.data["fullName"],
                },
            }
            # Send to receiver
            await manager.send_message(ws_message, str(receiverId))
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Failed to send WebSocket message: {e}")

        return message


schema = strawberry.Schema(query=Query, mutation=Mutation)
