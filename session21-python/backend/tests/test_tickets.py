def test_create_ticket_defaults_to_open(make_ticket):
    ticket = make_ticket()
    assert ticket["id"] > 0
    assert ticket["status"] == "OPEN"
    assert ticket["resolved_at"] is None
    assert ticket["comment_count"] == 0


def test_create_ticket_rejects_invalid_payload(client):
    response = client.post(
        "/api/tickets",
        json={"subject": "x", "requester_name": "A", "requester_email": "not-an-email", "priority": "SUPER"},
    )
    assert response.status_code == 422
    fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"subject", "requester_email", "priority"} <= fields


def test_list_tickets_newest_first(client, make_ticket):
    first = make_ticket(subject="First ticket")
    second = make_ticket(subject="Second ticket")
    ids = [t["id"] for t in client.get("/api/tickets").json()]
    assert ids == [second["id"], first["id"]]


def test_list_tickets_filters_and_search(client, make_ticket):
    make_ticket(subject="Invoice charged twice", category="BILLING", priority="URGENT")
    make_ticket(subject="Dark mode please", category="FEATURE_REQUEST", priority="LOW")

    billing = client.get("/api/tickets", params={"category": "BILLING"}).json()
    assert [t["subject"] for t in billing] == ["Invoice charged twice"]

    urgent = client.get("/api/tickets", params={"priority": "URGENT"}).json()
    assert len(urgent) == 1

    search = client.get("/api/tickets", params={"q": "dark"}).json()
    assert [t["subject"] for t in search] == ["Dark mode please"]


def test_get_ticket_by_id(client, make_ticket):
    ticket = make_ticket()
    response = client.get(f"/api/tickets/{ticket['id']}")
    assert response.status_code == 200
    assert response.json()["subject"] == ticket["subject"]


def test_get_missing_ticket_returns_404(client):
    response = client.get("/api/tickets/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Ticket not found"


def test_update_ticket_assigns_agent_and_resolves(client, make_ticket):
    ticket = make_ticket()
    response = client.put(f"/api/tickets/{ticket['id']}", json={"agent": "Ravi", "status": "RESOLVED"})
    assert response.status_code == 200
    body = response.json()
    assert body["agent"] == "Ravi"
    assert body["status"] == "RESOLVED"
    assert body["resolved_at"] is not None


def test_reopening_ticket_clears_resolved_at(client, make_ticket):
    ticket = make_ticket()
    client.put(f"/api/tickets/{ticket['id']}", json={"status": "RESOLVED"})
    reopened = client.put(f"/api/tickets/{ticket['id']}", json={"status": "OPEN"}).json()
    assert reopened["status"] == "OPEN"
    assert reopened["resolved_at"] is None


def test_update_missing_ticket_returns_404(client):
    assert client.put("/api/tickets/9999", json={"status": "CLOSED"}).status_code == 404


def test_delete_ticket(client, make_ticket):
    ticket = make_ticket()
    assert client.delete(f"/api/tickets/{ticket['id']}").status_code == 204
    assert client.get(f"/api/tickets/{ticket['id']}").status_code == 404
    assert client.delete(f"/api/tickets/{ticket['id']}").status_code == 404


def test_stats_counts_by_status_and_category(client, make_ticket):
    a = make_ticket(priority="URGENT", category="BUG")
    make_ticket(priority="URGENT", category="BUG", agent="Ravi")
    c = make_ticket(category="BILLING")
    client.put(f"/api/tickets/{c['id']}", json={"status": "RESOLVED"})
    client.put(f"/api/tickets/{a['id']}", json={"status": "IN_PROGRESS"})

    stats = client.get("/api/tickets/stats").json()
    assert stats["total"] == 3
    assert stats["open"] == 1
    assert stats["inProgress"] == 1
    assert stats["resolved"] == 1
    assert stats["urgentOpen"] == 2
    assert stats["unassigned"] == 1
    assert stats["byCategory"] == {"BUG": 2, "BILLING": 1}


def test_comments_round_trip(client, make_ticket):
    ticket = make_ticket()
    response = client.post(
        f"/api/tickets/{ticket['id']}/comments", json={"author": "Asha Verma", "body": "Still broken today."}
    )
    assert response.status_code == 201

    comments = client.get(f"/api/tickets/{ticket['id']}/comments").json()
    assert [c["body"] for c in comments] == ["Still broken today."]
    assert client.get(f"/api/tickets/{ticket['id']}").json()["comment_count"] == 1


def test_agent_reply_moves_ticket_in_progress(client, make_ticket):
    ticket = make_ticket(agent="Ravi")
    client.post(f"/api/tickets/{ticket['id']}/comments", json={"author": "Ravi", "body": "Looking into it."})
    assert client.get(f"/api/tickets/{ticket['id']}").json()["status"] == "IN_PROGRESS"


def test_internal_note_does_not_change_status(client, make_ticket):
    ticket = make_ticket(agent="Ravi")
    client.post(
        f"/api/tickets/{ticket['id']}/comments", json={"author": "Ravi", "body": "Escalate to infra.", "internal": True}
    )
    assert client.get(f"/api/tickets/{ticket['id']}").json()["status"] == "OPEN"


def test_deleting_ticket_removes_comments(client, make_ticket):
    ticket = make_ticket()
    client.post(f"/api/tickets/{ticket['id']}/comments", json={"author": "Asha", "body": "Hello"})
    client.delete(f"/api/tickets/{ticket['id']}")
    assert client.get(f"/api/tickets/{ticket['id']}/comments").status_code == 404
