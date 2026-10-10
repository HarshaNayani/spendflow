from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .. import ai, flags
from ..config import CATEGORIES
from ..deps import get_current_user, get_db, require_roles
from ..models import Expense, User, utcnow
from ..schemas import DecisionIn, ExpenseIn, ExpenseOut

router = APIRouter(prefix="/expenses", tags=["expenses"])

LOCKED_MESSAGE = "Approved expenses are locked and cannot be changed"


def serialize(e: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=e.id,
        user_id=e.user_id,
        user_name=e.user.name if e.user else None,
        amount=e.amount,
        description=e.description,
        category=e.category,
        expense_date=e.expense_date,
        status=e.status,
        ai_flag=e.ai_flag,
        ai_reason=e.ai_reason or "",
        manager_comment=e.manager_comment or "",
        created_at=e.created_at,
        decided_at=e.decided_at,
        locked=e.status == "approved",
    )


def clean_category(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    if value not in CATEGORIES:
        raise HTTPException(
            422,
            f"Category must be one of: {', '.join(CATEGORIES)}",
        )
    return value


def review(db: Session, user_id: int, body: ExpenseIn, exclude_id: Optional[int] = None):
    """Run the AI check and the rule checks. Returns (category, flagged, reason)."""
    ai_result = ai.analyze_expense(body.description, body.amount)
    rule_reasons = [
        flags.high_amount_reason(body.amount),
        flags.duplicate_reason(db, user_id, body.amount, body.expense_date, exclude_id),
    ]
    flagged, reason = flags.merge_flags(ai_result, rule_reasons)
    category = clean_category(body.category) or ai_result["category"] or "Other"
    return category, flagged, reason


def get_expense_or_404(db: Session, expense_id: int) -> Expense:
    expense = db.scalar(
        select(Expense).options(joinedload(Expense.user)).where(Expense.id == expense_id)
    )
    if expense is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    return expense


# ---------- employee ----------
@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category, flagged, reason = review(db, user.id, body)
    expense = Expense(
        user_id=user.id,
        amount=body.amount,
        description=body.description.strip(),
        category=category,
        expense_date=body.expense_date,
        status="pending",
        ai_flag=flagged,
        ai_reason=reason,
    )
    db.add(expense)
    db.commit()
    return serialize(get_expense_or_404(db, expense.id))


@router.get("/mine", response_model=list[ExpenseOut])
def my_expenses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Expense)
        .options(joinedload(Expense.user))
        .where(Expense.user_id == user.id)
        .order_by(Expense.created_at.desc(), Expense.id.desc())
    ).all()
    return [serialize(e) for e in rows]


# ---------- manager / admin ----------
@router.get("/pending", response_model=list[ExpenseOut])
def pending_expenses(
    user: User = Depends(require_roles("manager", "admin")),
    db: Session = Depends(get_db),
):
    """Approval queue: flagged claims first, then oldest first. A reviewer
    never sees their own claims here."""
    rows = db.scalars(
        select(Expense)
        .options(joinedload(Expense.user))
        .where(Expense.status == "pending", Expense.user_id != user.id)
        .order_by(Expense.ai_flag.desc(), Expense.created_at.asc())
    ).all()
    return [serialize(e) for e in rows]


@router.patch("/{expense_id}/decision", response_model=ExpenseOut)
def decide(
    expense_id: int,
    body: DecisionIn,
    user: User = Depends(require_roles("manager", "admin")),
    db: Session = Depends(get_db),
):
    expense = get_expense_or_404(db, expense_id)
    if expense.user_id == user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You cannot approve or reject your own expense"
        )
    if expense.status == "approved":
        raise HTTPException(status.HTTP_403_FORBIDDEN, LOCKED_MESSAGE)
    if expense.status != "pending":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only pending expenses can be decided"
        )
    comment = body.comment.strip()
    if body.decision == "rejected" and len(comment) < 3:
        raise HTTPException(
            422, "Add a comment when rejecting an expense"
        )
    expense.status = body.decision
    expense.manager_comment = comment
    expense.decided_by = user.id
    expense.decided_at = utcnow()
    db.commit()
    return serialize(get_expense_or_404(db, expense.id))


@router.get("", response_model=list[ExpenseOut])
def all_expenses(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    query = select(Expense).options(joinedload(Expense.user))
    if status_filter:
        query = query.where(Expense.status == status_filter)
    rows = db.scalars(query.order_by(Expense.created_at.desc())).all()
    return [serialize(e) for e in rows]


# ---------- owner edit / delete (blocked once approved) ----------
@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    body: ExpenseIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fix and resubmit. A rejected expense goes back to pending."""
    expense = get_expense_or_404(db, expense_id)
    if expense.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own expenses")
    if expense.status == "approved":
        raise HTTPException(status.HTTP_403_FORBIDDEN, LOCKED_MESSAGE)
    category, flagged, reason = review(db, user.id, body, exclude_id=expense.id)
    expense.amount = body.amount
    expense.description = body.description.strip()
    expense.category = category
    expense.expense_date = body.expense_date
    expense.ai_flag = flagged
    expense.ai_reason = reason
    expense.status = "pending"
    expense.manager_comment = ""
    expense.decided_by = None
    expense.decided_at = None
    db.commit()
    return serialize(get_expense_or_404(db, expense.id))


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = get_expense_or_404(db, expense_id)
    if expense.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own expenses")
    if expense.status == "approved":
        raise HTTPException(status.HTTP_403_FORBIDDEN, LOCKED_MESSAGE)
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
