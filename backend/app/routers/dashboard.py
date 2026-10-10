from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..deps import get_db, require_roles
from ..models import Budget, Expense, User
from ..schemas import BudgetUsage, CategorySpend, SummaryOut
from .expenses import serialize

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=SummaryOut)
def summary(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    month_start = date.today().replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)

    counts = dict(
        db.execute(select(Expense.status, func.count(Expense.id)).group_by(Expense.status)).all()
    )
    total_spend = db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.status == "approved")
    ).scalar_one()
    flagged_count = db.execute(
        select(func.count(Expense.id)).where(Expense.ai_flag.is_(True))
    ).scalar_one()

    by_category = db.execute(
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.status == "approved")
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    ).all()

    month_spend = dict(
        db.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(
                Expense.status == "approved",
                Expense.expense_date >= month_start,
                Expense.expense_date < next_month,
            )
            .group_by(Expense.category)
        ).all()
    )
    budgets = db.scalars(select(Budget).order_by(Budget.category)).all()
    budget_rows = [
        BudgetUsage(
            category=b.category,
            monthly_limit=b.monthly_limit,
            spent=float(month_spend.get(b.category, 0) or 0),
            used_pct=round(
                float(month_spend.get(b.category, 0) or 0) / b.monthly_limit * 100, 1
            )
            if b.monthly_limit
            else 0.0,
        )
        for b in budgets
    ]

    flagged = db.scalars(
        select(Expense)
        .options(joinedload(Expense.user))
        .where(Expense.ai_flag.is_(True))
        .order_by(Expense.created_at.desc())
        .limit(10)
    ).all()

    return SummaryOut(
        total_spend=float(total_spend or 0),
        pending_count=counts.get("pending", 0),
        approved_count=counts.get("approved", 0),
        rejected_count=counts.get("rejected", 0),
        flagged_count=flagged_count,
        spend_by_category=[
            CategorySpend(category=c, spend=float(s or 0)) for c, s in by_category
        ],
        budget_vs_spend=budget_rows,
        flagged=[serialize(e) for e in flagged],
    )
