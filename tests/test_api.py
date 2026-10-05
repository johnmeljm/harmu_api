import pytest
from fastapi.testclient import TestClient

from harmu_api.api import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def create(client: TestClient, **payload) -> dict:
    resp = client.post("/matches", json=payload)
    assert resp.status_code == 200
    return resp.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_match_with_defaults(client):
    body = create(client)
    assert body["match_id"] == "m1"
    assert body["round_number"] == 1
    assert body["status"] == "in_progress"
    assert body["winner"] is None
    assert set(body["players"]) == {"p1", "p2"}
    assert body["players"]["p1"]["resources"] == {
        "hp": 1,
        "money": 0,
        "knives": 0,
        "gunpowder": 0,
        "bombs": 0,
        "reflect_shields": 0,
    }


def test_create_match_with_custom_players_and_resources(client):
    body = create(
        client,
        players=[
            {"player_id": "alice", "name": "爱丽丝"},
            {"player_id": "bob"},
        ],
        initial_resources={"money": 2, "knives": 1},
    )
    assert set(body["players"]) == {"alice", "bob"}
    assert body["players"]["alice"]["name"] == "爱丽丝"
    assert body["players"]["bob"]["name"] == "玩家2"
    assert body["players"]["bob"]["resources"]["money"] == 2


def test_create_match_rejects_bad_initial_resources(client):
    assert client.post("/matches", json={"initial_resources": {"hp": 3}}).status_code == 400
    assert (
        client.post("/matches", json={"initial_resources": {"gold": 1}}).status_code == 400
    )
    assert (
        client.post("/matches", json={"initial_resources": {"money": -1}}).status_code == 400
    )


def test_round_settlement_flow(client):
    match_id = create(client)["match_id"]

    resp = client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p1", "action": "earn_money"},
    )
    body = resp.json()
    assert body["status"] == "waiting_opponent"
    assert body["match"]["submitted"] == ["p1"]
    assert body["match"]["round_number"] == 1

    resp = client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p2", "action": "earn_money"},
    )
    body = resp.json()
    assert body["status"] == "settled"
    assert body["round"]["round_number"] == 1
    assert body["round"]["match_status"] == "in_progress"
    assert len([e for e in body["round"]["events"] if e["type"] == "production"]) == 2
    assert body["match"]["round_number"] == 2
    assert body["match"]["players"]["p1"]["resources"]["money"] == 1


def test_full_kill_via_api(client):
    match_id = create(client, initial_resources={"knives": 1})["match_id"]
    client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p1", "action": "use_knife", "target_id": "p2"},
    )
    resp = client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p2", "action": "earn_money"},
    )
    body = resp.json()
    assert body["round"]["winner"] == "p1"
    assert body["round"]["deaths"] == ["p2"]
    assert body["match"]["status"] == "ended"

    resp = client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p2", "action": "earn_money"},
    )
    assert resp.status_code == 409


def test_error_mappings(client):
    match_id = create(client)["match_id"]

    resp = client.post("/matches/m999/actions", json={"player_id": "p1", "action": "earn_money"})
    assert resp.status_code == 404

    client.post(f"/matches/{match_id}/actions", json={"player_id": "p1", "action": "earn_money"})
    resp = client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p1", "action": "earn_money"},
    )
    assert resp.status_code == 409

    resp = client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p2", "action": "use_knife", "target_id": "p1"},
    )
    assert resp.status_code == 422
    assert "前置条件不满足" in resp.json()["error"]

    resp = client.post(
        f"/matches/{match_id}/actions",
        json={"player_id": "p2", "action": "earn_money", "target_id": "p1"},
    )
    assert resp.status_code == 400


def test_list_and_history(client):
    create(client)
    create(client)
    assert len(client.get("/matches").json()["matches"]) == 2

    match_id = create(client)["match_id"]
    client.post(f"/matches/{match_id}/actions", json={"player_id": "p1", "action": "earn_money"})
    client.post(f"/matches/{match_id}/actions", json={"player_id": "p2", "action": "earn_money"})
    history = client.get(f"/matches/{match_id}/history").json()
    assert history["match_id"] == match_id
    assert len(history["rounds"]) == 1
    assert history["rounds"][0]["round_number"] == 1
