from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    """Naive UTC timestamp (works the same on SQLite and Postgres)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="employee")

    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="user", foreign_keys="Expense.user_id"
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="Other")
    expense_date: Mapped[date] = mapped_column(Date)
    # pending -> approved (locked) | rejected (employee can fix and resubmit)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    ai_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_reason: Mapped[str] = mapped_column(Text, default="")
    manager_comment: Mapped[str] = mapped_column(Text, default="")
    decided_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="expenses", foreign_keys=[user_id])
    decider: Mapped[Optional[User]] = relationship(foreign_keys=[decided_by])


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(50), unique=True)
    monthly_limit: Mapped[float] = mapped_column(Float)
