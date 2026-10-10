import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address")
    return value


# ---------- auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=6, max_length=72)

    _email = field_validator("email")(_clean_email)


class LoginIn(BaseModel):
    email: str
    password: str

    _email = field_validator("email")(_clean_email)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- expenses ----------
class ExpenseIn(BaseModel):
    amount: float = Field(gt=0, le=10_000_000)
    description: str = Field(min_length=3, max_length=500)
    expense_date: date
    category: Optional[str] = None


class DecisionIn(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str = Field(default="", max_length=500)


class ExpenseOut(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    amount: float
    description: str
    category: str
    expense_date: date
    status: str
    ai_flag: bool
    ai_reason: str
    manager_comment: str
    created_at: datetime
    decided_at: Optional[datetime] = None
    locked: bool = False


# ---------- AI ----------
class CategorizeIn(BaseModel):
    description: str = Field(min_length=3, max_length=500)
    amount: float = Field(gt=0, le=10_000_000)


class CategorizeOut(BaseModel):
    category: Optional[str] = None
    is_unusual: bool = False
    reason: str = ""
    ai_available: bool = False


# ---------- dashboard ----------
class CategorySpend(BaseModel):
    category: str
    spend: float


class BudgetUsage(BaseModel):
    category: str
    monthly_limit: float
    spent: float
    used_pct: float


class SummaryOut(BaseModel):
    total_spend: float
    pending_count: int
    approved_count: int
    rejected_count: int
    flagged_count: int
    spend_by_category: list[CategorySpend]
    budget_vs_spend: list[BudgetUsage]
    flagged: list[ExpenseOut]
