from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Comment, Ticket
from .schemas import (
    Category,
    CommentCreate,
    CommentOut,
    Priority,
    StatsOut,
    Status,
    TicketCreate,
    TicketOut,
    TicketUpdate,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

ACTIVE_STATUSES = ("OPEN", "IN_PROGRESS")


def _get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def _to_out(ticket: Ticket) -> TicketOut:
    out = TicketOut.model_validate(ticket)
    out.comment_count = len(ticket.comments)
    return out


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status_: Status | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    category: Category | None = None,
    q: str | None = Query(default=None, description="Search subject, requester or agent"),
    db: Session = Depends(get_db),
):
    query = select(Ticket).order_by(Ticket.id.desc())
    if status_:
        query = query.where(Ticket.status == status_)
    if priority:
        query = query.where(Ticket.priority == priority)
    if category:
        query = query.where(Ticket.category == category)
    if q:
        like = f"%{q}%"
        query = query.where(
            or_(Ticket.subject.ilike(like), Ticket.requester_name.ilike(like), Ticket.agent.ilike(like))
        )
    return [_to_out(t) for t in db.scalars(query)]


@router.get("/stats", response_model=StatsOut)
def ticket_stats(db: Session = Depends(get_db)):
    by_status = dict(db.execute(select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)).all())
    by_category = dict(db.execute(select(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category)).all())
    urgent_open = db.scalar(
        select(func.count(Ticket.id)).where(Ticket.priority == "URGENT", Ticket.status.in_(ACTIVE_STATUSES))
    )
    unassigned = db.scalar(
        select(func.count(Ticket.id)).where(Ticket.agent.is_(None), Ticket.status.in_(ACTIVE_STATUSES))
    )
    return StatsOut(
        total=sum(by_status.values()),
        open=by_status.get("OPEN", 0),
        inProgress=by_status.get("IN_PROGRESS", 0),
        resolved=by_status.get("RESOLVED", 0),
        closed=by_status.get("CLOSED", 0),
        urgentOpen=urgent_open or 0,
        unassigned=unassigned or 0,
        byCategory=by_category,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return _to_out(_get_ticket_or_404(db, ticket_id))


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump(), status="OPEN")
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(ticket, key, value)
    if "status" in changes:
        # resolved_at tracks when the customer's issue was actually fixed (used for SLA reporting).
        if changes["status"] in ("RESOLVED", "CLOSED"):
            ticket.resolved_at = ticket.resolved_at or datetime.now(UTC)
        else:
            ticket.resolved_at = None
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    db.delete(ticket)
    db.commit()


@router.get("/{ticket_id}/comments", response_model=list[CommentOut])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    return _get_ticket_or_404(db, ticket_id).comments


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(ticket_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    ticket = _get_ticket_or_404(db, ticket_id)
    comment = Comment(ticket_id=ticket.id, **payload.model_dump())
    db.add(comment)
    # A public agent reply on a new ticket means work has started on it.
    if not payload.internal and ticket.status == "OPEN" and ticket.agent and payload.author == ticket.agent:
        ticket.status = "IN_PROGRESS"
    db.commit()
    db.refresh(comment)
    return comment
