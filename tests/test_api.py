from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from backend.app import create_app


def make_client(tmp_path):
    return TestClient(create_app(tmp_path / "test.db"))


def test_transaction_updates_summary(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/transaction",
        json={"requestId": "req-001", "userId": "alice", "amount": 120, "type": "purchase"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["transaction"]["pointsDelta"] == 120
    assert body["summary"]["totalPoints"] == 120
    assert body["summary"]["transactionCount"] == 1


def test_duplicate_request_is_idempotent(tmp_path):
    client = make_client(tmp_path)
    payload = {"requestId": "req-duplicate", "userId": "alice", "amount": 75, "type": "purchase"}

    first = client.post("/transaction", json=payload)
    second = client.post("/transaction", json=payload)
    summary = client.get("/summary/alice")

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["transaction"]["duplicate"] is True
    assert summary.json()["totalPoints"] == 75
    assert summary.json()["transactionCount"] == 1


def test_invalid_input_returns_422(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/transaction",
        json={"requestId": "short", "userId": "a!", "amount": -1, "type": "purchase"},
    )

    assert response.status_code == 422


def test_ranking_uses_multiple_factors(tmp_path):
    client = make_client(tmp_path)
    transactions = [
        {"requestId": "req-a-1", "userId": "alice", "amount": 100, "type": "purchase"},
        {"requestId": "req-a-2", "userId": "alice", "amount": 20, "type": "refund"},
        {"requestId": "req-b-1", "userId": "bobby", "amount": 95, "type": "purchase"},
        {"requestId": "req-b-2", "userId": "bobby", "amount": 5, "type": "purchase"},
    ]

    for payload in transactions:
        assert client.post("/transaction", json=payload).status_code == 201

    ranking = client.get("/ranking").json()

    assert ranking[0]["userId"] == "bobby"
    assert ranking[0]["score"] > ranking[1]["score"]


def test_concurrent_duplicate_requests_only_apply_once(tmp_path):
    client = make_client(tmp_path)
    payload = {"requestId": "req-concurrent", "userId": "carla", "amount": 42, "type": "purchase"}

    def send_request():
        return client.post("/transaction", json=payload).json()

    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(lambda _: send_request(), range(6)))

    summary = client.get("/summary/carla").json()

    assert summary["totalPoints"] == 42
    assert summary["transactionCount"] == 1
    assert sum(result["transaction"]["duplicate"] for result in results) == 5
