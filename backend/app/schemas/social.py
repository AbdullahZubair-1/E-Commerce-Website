import uuid
from datetime import datetime
from pydantic import BaseModel


class UserSearchResult(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str

    model_config = {"from_attributes": True}


class FriendRequestCreate(BaseModel):
    addressee_id: uuid.UUID


class FriendRequestActionResponse(BaseModel):
    id: uuid.UUID
    status: str


class FriendRequestResponse(BaseModel):
    id: uuid.UUID
    requester_id: uuid.UUID
    addressee_id: uuid.UUID
    status: str
    created_at: datetime
    # Denormalized display info for the OTHER person in the request, filled
    # in by the service layer (not derived automatically by the ORM).
    other_user_id: uuid.UUID
    other_user_name: str
    other_user_email: str

    model_config = {"from_attributes": True}


class FriendResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    recipient_id: uuid.UUID
    content: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    content: str
    created_at: datetime
    read_at: datetime | None = None

    model_config = {"from_attributes": True}