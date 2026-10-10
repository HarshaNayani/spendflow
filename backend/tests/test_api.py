from conftest import ADMIN, MANAGER, login, register, submit


def test_register_and_login(client):
    register(client)
    res = client.post("/auth/login", json={"email": "emp@test.dev", "password": "Employee@123"})
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "employee"
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {res.json()['access_token']}"})
    assert me.json()["email"] == "emp@test.dev"


def test_login_with_wrong_password_fails(client):
    register(client)
    res = client.post("/auth/login", json={"email": "emp@test.dev", "password": "wrong-password"})
    assert res.status_code == 401


def test_register_always_creates_an_employee(client):
    res = client.post(
        "/auth/register",
        json={"name": "Sneaky", "email": "sneaky@test.dev", "password": "Secret@123", "role": "admin"},
    )
    assert res.status_code == 201
    assert res.json()["user"]["role"] == "employee"


def test_protected_routes_need_a_token(client):
    assert client.get("/expenses/mine").status_code == 401


def test_submit_expense_and_see_it_in_my_list(client):
    emp = register(client)
    created = submit(client, emp)
    assert created["status"] == "pending"
    assert created["category"] == "Travel"
    mine = client.get("/expenses/mine", headers=emp).json()
    assert len(mine) == 1 and mine[0]["id"] == created["id"]


def test_ai_unavailable_falls_back_to_manual_category(client):
    emp = register(client)
    res = client.post(
        "/ai/categorize",
        json={"description": "Taxi to airport", "amount": 800},
        headers=emp,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ai_available"] is False
    assert body["category"] is None
    # submitting without a category still works and defaults to Other
    created = submit(client, emp, category=None)
    assert created["category"] == "Other"


def test_manager_approves_and_expense_is_locked(client):
    emp = register(client)
    mgr = login(client, *MANAGER)
    expense = submit(client, emp)

    queue = client.get("/expenses/pending", headers=mgr).json()
    assert [e["id"] for e in queue] == [expense["id"]]

    res = client.patch(
        f"/expenses/{expense['id']}/decision",
        json={"decision": "approved", "comment": "Looks good"},
        headers=mgr,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "approved" and res.json()["locked"] is True

    edit = client.put(
        f"/expenses/{expense['id']}",
        json={"amount": 9, "description": "Changed after approval", "expense_date": "2026-10-05"},
        headers=emp,
    )
    assert edit.status_code == 403
    assert client.delete(f"/expenses/{expense['id']}", headers=emp).status_code == 403
    again = client.patch(
        f"/expenses/{expense['id']}/decision",
        json={"decision": "rejected", "comment": "Changed my mind"},
        headers=mgr,
    )
    assert again.status_code == 403


def test_employee_cannot_use_manager_endpoints(client):
    emp = register(client)
    expense = submit(client, emp)
    assert client.get("/expenses/pending", headers=emp).status_code == 403
    res = client.patch(
        f"/expenses/{expense['id']}/decision",
        json={"decision": "approved", "comment": ""},
        headers=emp,
    )
    assert res.status_code == 403


def test_reject_needs_a_comment_and_employee_can_resubmit(client):
    emp = register(client)
    mgr = login(client, *MANAGER)
    expense = submit(client, emp)

    no_comment = client.patch(
        f"/expenses/{expense['id']}/decision",
        json={"decision": "rejected", "comment": ""},
        headers=mgr,
    )
    assert no_comment.status_code == 422

    rejected = client.patch(
        f"/expenses/{expense['id']}/decision",
        json={"decision": "rejected", "comment": "Please attach the bill"},
        headers=mgr,
    )
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["manager_comment"] == "Please attach the bill"

    fixed = client.put(
        f"/expenses/{expense['id']}",
        json={
            "amount": 1400,
            "description": "Cab to the client office, bill attached",
            "expense_date": "2026-10-05",
            "category": "Travel",
        },
        headers=emp,
    )
    assert fixed.status_code == 200
    assert fixed.json()["status"] == "pending"
    assert fixed.json()["manager_comment"] == ""


def test_manager_cannot_approve_their_own_expense(client):
    mgr = login(client, *MANAGER)
    own = submit(client, mgr)
    res = client.patch(
        f"/expenses/{own['id']}/decision",
        json={"decision": "approved", "comment": ""},
        headers=mgr,
    )
    assert res.status_code == 403
    assert client.get("/expenses/pending", headers=mgr).json() == []


def test_high_amount_is_flagged_by_the_rules(client):
    emp = register(client)
    created = submit(client, emp, amount=85000, description="New laptop", category="Equipment")
    assert created["ai_flag"] is True
    assert "review limit" in created["ai_reason"]


def test_duplicate_claim_is_flagged(client):
    emp = register(client)
    submit(client, emp)
    second = submit(client, emp)
    assert second["ai_flag"] is True
    assert "duplicate" in second["ai_reason"].lower()


def test_flagged_claims_come_first_in_the_queue(client):
    emp = register(client)
    mgr = login(client, *MANAGER)
    normal = submit(client, emp, amount=500, description="Stationery for the team")
    flagged = submit(client, emp, amount=90000, description="Conference sponsorship")
    queue = client.get("/expenses/pending", headers=mgr).json()
    assert [e["id"] for e in queue] == [flagged["id"], normal["id"]]


def test_dashboard_is_admin_only_and_sums_approved_spend(client):
    emp = register(client)
    mgr = login(client, *MANAGER)
    admin = login(client, *ADMIN)
    expense = submit(client, emp, amount=2000)
    client.patch(
        f"/expenses/{expense['id']}/decision",
        json={"decision": "approved", "comment": ""},
        headers=mgr,
    )
    assert client.get("/dashboard/summary", headers=emp).status_code == 403
    assert client.get("/dashboard/summary", headers=mgr).status_code == 403
    summary = client.get("/dashboard/summary", headers=admin).json()
    assert summary["total_spend"] == 2000
    assert summary["approved_count"] == 1
    assert summary["spend_by_category"][0]["category"] == "Travel"
