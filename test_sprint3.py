"""HTTP-tests voor alle routes en de belangrijkste fouten van Sprint 3."""

import pytest
from fastapi.testclient import TestClient

import sprint3


@pytest.fixture(autouse=True)
def reset_data():
    sprint3.players[:] = [
        sprint3.Player(id=1, username="Alice", score=100),
        sprint3.Player(id=2, username="Bob", score=150),
    ]
    sprint3.scores[:] = [
        sprint3.Score(id=1, player_id=1, points=100),
        sprint3.Score(id=2, player_id=2, points=150),
    ]
    sprint3.next_player_id = 3
    sprint3.next_score_id = 3


client = TestClient(sprint3.app)


def test_sprint2_read_routes_still_work():
    assert client.get("/").json() == {"message": "De Players API werkt!"}
    assert client.get("/players").json() == [
        {"id": 1, "username": "Alice", "score": 100},
        {"id": 2, "username": "Bob", "score": 150},
    ]
    assert client.get("/players/1").json()["username"] == "Alice"
    assert [p["id"] for p in client.get("/leaderboard").json()] == [2, 1]


def test_player_crud_and_scores():
    created = client.post("/players", json={"username": " Charlie "})
    assert created.status_code == 201
    assert created.headers["location"] == "/players/3"
    assert created.json() == {"id": 3, "username": "Charlie", "score": 0}

    added = client.post("/players/3/scores", json={"points": 25})
    assert added.status_code == 201
    assert added.json() == {"id": 3, "player_id": 3, "points": 25}
    assert client.get("/players/3").json()["score"] == 25
    assert client.get("/players/3/scores").json() == [added.json()]
    assert len(client.get("/scores").json()) == 3

    updated = client.put("/players/3", json={"username": "Dana"})
    assert updated.status_code == 200
    assert updated.json() == {"id": 3, "username": "Dana", "score": 25}
    assert [p["id"] for p in client.get("/leaderboard").json()] == [2, 1, 3]

    deleted = client.delete("/players/3")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get("/players/3").status_code == 404
    assert client.get("/players/3/scores").status_code == 404
    assert len(client.get("/scores").json()) == 2


def test_missing_players_and_duplicate_names():
    for method, path, data in [
        ("get", "/players/99", None),
        ("put", "/players/99", {"username": "Nobody"}),
        ("delete", "/players/99", None),
        ("get", "/players/99/scores", None),
        ("post", "/players/99/scores", {"points": 10}),
    ]:
        assert client.request(method.upper(), path, json=data).status_code == 404

    assert client.post("/players", json={"username": "alice"}).status_code == 400
    assert client.put("/players/2", json={"username": " ALICE "}).status_code == 400


@pytest.mark.parametrize(
    "path,data",
    [
        ("/players", {}),
        ("/players", {"username": "   "}),
        ("/players", {"username": "x" * 51}),
        ("/players", {"username": "Charlie", "id": 99}),
        ("/players/1/scores", {"points": 0}),
        ("/players/1/scores", {"points": -5}),
        ("/players/1/scores", {"points": "10"}),
        ("/players/1/scores", {"points": 1.5}),
    ],
)
def test_invalid_request_body_returns_422(path, data):
    assert client.post(path, json=data).status_code == 422


def test_invalid_path_and_openapi():
    assert client.get("/players/0").status_code == 422
    assert client.get("/docs").status_code == 200
    routes = client.get("/openapi.json").json()["paths"]
    assert set(routes["/players"].keys()) == {"get", "post"}
    assert set(routes["/players/{player_id}"].keys()) == {"get", "put", "delete"}
