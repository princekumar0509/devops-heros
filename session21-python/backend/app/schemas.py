from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
Priority = Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
Category = Literal["GENERAL", "BUG", "BILLING", "ACCOUNT", "FEATURE_REQUEST"]

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = ""
    category: Category = "GENERAL"
    priority: Priority = "MEDIUM"
    requester_name: str = Field(min_length=1, max_length=120)
    requester_email: str = Field(pattern=EMAIL_PATTERN, max_length=254)
    agent: str | None = Field(default=None, max_length=120)


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    category: Category | None = None
    priority: Priority | None = None
    status: Status | None = None
    agent: str | None = Field(default=None, max_length=120)


class TicketOut(BaseModel):
    id: int
    subject: str
    description: str
    category: Category
    priority: Priority
    status: Status
    requester_name: str
    requester_email: str
    agent: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    comment_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    author: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1)
    internal: bool = False


class CommentOut(CommentCreate):
    id: int
    ticket_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    total: int
    open: int
    inProgress: int
    resolved: int
    closed: int
    urgentOpen: int
    unassigned: int
    byCategory: dict[str, int]
