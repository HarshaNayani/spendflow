"""Rule-based checks that run next to the AI, so flagging works even when the
AI is unavailable."""
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import HIGH_AMOUNT_THRESHOLD
from .models import Expense


def high_amount_reason(amount: float) -> str:
    if amount >= HIGH_AMOUNT_THRESHOLD:
        return (
            f"Amount ₹{amount:,.0f} is above the review limit of "
            f"₹{HIGH_AMOUNT_THRESHOLD:,.0f}"
        )
    return ""


def duplicate_reason(
    db: Session,
    user_id: int,
    amount: float,
    expense_date: date,
    exclude_id: Optional[int] = None,
) -> str:
    query = select(Expense.id).where(
        Expense.user_id == user_id,
        Expense.amount == amount,
        Expense.expense_date == expense_date,
    )
    if exclude_id is not None:
        query = query.where(Expense.id != exclude_id)
    if db.execute(query.limit(1)).first():
        return "Possible duplicate: same amount and date already submitted"
    return ""


def merge_flags(ai_result: dict, rule_reasons: list[str]) -> tuple[bool, str]:
    """Combine the AI verdict and rule reasons into (flagged, reason text)."""
    reasons = []
    if ai_result.get("is_unusual"):
        text = ai_result.get("reason") or "looks unusual"
        reasons.append(f"AI: {text}")
    reasons.extend(f"Rule: {r}" for r in rule_reasons if r)
    return bool(reasons), " | ".join(reasons)
