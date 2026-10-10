"""Demo data: three role accounts, budgets and sample expenses.

Run manually:  python -m app.seed --reset
It also runs automatically on startup when the database is empty and
SEED_DEMO=true, which keeps the demo working on hosts with a temporary disk.
"""
import argparse
from datetime import date

from sqlalchemy import func, select

from .config import HIGH_AMOUNT_THRESHOLD
from .database import Base, SessionLocal, engine
from .models import Budget, Expense, User, utcnow
from .security import hash_password

DEMO_USERS = [
    ("Ravi Kumar", "employee@spendflow.demo", "Employee@123", "employee"),
    ("Priya Sharma", "priya@spendflow.demo", "Employee@123", "employee"),
    ("Meera Nair", "manager@spendflow.demo", "Manager@123", "manager"),
    ("Arjun Rao", "admin@spendflow.demo", "Admin@123", "admin"),
]

BUDGETS = {
    "Travel": 40000,
    "Food": 15000,
    "Software": 30000,
    "Office Supplies": 10000,
    "Equipment": 60000,
    "Marketing": 25000,
    "Utilities": 12000,
    "Training": 20000,
    "Other": 8000,
}

LAPTOP_REASON = (
    f"Rule: Amount ₹85,000 is above the review limit of ₹{HIGH_AMOUNT_THRESHOLD:,.0f}"
)

# (owner email, amount, description, category, day of month, status, flagged, reason, comment)
EXPENSES = [
    ("employee@spendflow.demo", 4200, "Cab rides to client site", "Travel", 2, "approved", False, "", "Approved, thanks."),
    ("employee@spendflow.demo", 1850, "Team lunch with client", "Food", 3, "approved", False, "", ""),
    ("employee@spendflow.demo", 12999, "Annual design tool subscription", "Software", 4, "approved", False, "", ""),
    ("employee@spendflow.demo", 3200, "Printer paper and toner", "Office Supplies", 5, "pending", False, "", ""),
    ("employee@spendflow.demo", 85000, "New laptop for design work", "Equipment", 6, "pending", True, LAPTOP_REASON, ""),
    ("employee@spendflow.demo", 2500, "Misc expenses", "Other", 7, "pending", True, "AI: The description is too vague to verify", ""),
    ("employee@spendflow.demo", 6500, "Flight to Bengaluru conference", "Travel", 8, "rejected", False, "", "Please attach the approved travel request and resubmit."),
    ("priya@spendflow.demo", 9800, "Social media ad campaign", "Marketing", 3, "approved", False, "", ""),
    ("priya@spendflow.demo", 2300, "Monthly internet bill", "Utilities", 2, "approved", False, "", ""),
    ("priya@spendflow.demo", 7500, "Online course for the team", "Training", 5, "approved", False, "", ""),
    ("priya@spendflow.demo", 1200, "Client dinner", "Food", 6, "pending", False, "", ""),
    ("priya@spendflow.demo", 15000, "Cloud hosting credits", "Software", 7, "pending", False, "", ""),
]


def seed_demo(db) -> None:
    today = date.today()
    users = {}
    for name, email, password, role in DEMO_USERS:
        user = User(name=name, email=email, password_hash=hash_password(password), role=role)
        db.add(user)
        users[email] = user
    for category, limit in BUDGETS.items():
        db.add(Budget(category=category, monthly_limit=limit))
    db.flush()

    manager = users["manager@spendflow.demo"]
    for owner, amount, desc, category, day, status, flagged, reason, comment in EXPENSES:
        decided = status in ("approved", "rejected")
        db.add(
            Expense(
                user_id=users[owner].id,
                amount=amount,
                description=desc,
                category=category,
                expense_date=date(today.year, today.month, min(day, today.day)),
                status=status,
                ai_flag=flagged,
                ai_reason=reason,
                manager_comment=comment,
                decided_by=manager.id if decided else None,
                decided_at=utcnow() if decided else None,
            )
        )
    db.commit()


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(func.count(User.id))) == 0:
            seed_demo(db)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SpendFlow demo data")
    parser.add_argument("--reset", action="store_true", help="drop all tables first")
    args = parser.parse_args()
    if args.reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_if_empty()
    print("Demo data ready.")
    for name, email, password, role in DEMO_USERS:
        print(f"  {role:<9} {email:<26} {password}")
