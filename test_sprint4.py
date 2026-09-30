"""HTTP- en persistentietests voor de SQLite-versie van de Game Score API."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from sprint4 import create_app


@pytest.fixture
def api(tmp_path):
    database = tmp_path / "game_scores.db"
    with TestClient(create_app(database)) as client:
        yield client, database


def test_existing_routes_and_crud(api):
    client, _ = api
    assert client.get("/").json() == {"message": "De Players API werkt!"}
    assert client.get("/players").json() == [
        {"id": 1, "username": "Alice", "score": 100},
        {"id": 2, "username": "Bob", "score": 150},
    ]
    assert [p["id"] for p in client.get("/leaderboard").json()] == [2, 1]
    assert client.get("/players/1").json()["username"] == "Alice"

    created = client.post("/players", json={"username": " Charlie "})
    assert created.status_code == 201
    assert created.headers["location"] == "/players/3"
    assert created.json() == {"id": 3, "username": "Charlie", "score": 0}

    added = client.post("/players/3/scores", json={"points": 25})
    assert added.status_code == 201
    assert added.json() == {"id": 3, "player_id": 3, "points": 25}
    assert client.get("/players/3/scores").json() == [added.json()]
    assert len(client.get("/scores").json()) == 3
    assert client.get("/players/3").json()["score"] == 25

    updated = client.put("/players/3", json={"username": "Dana"})
    assert updated.status_code == 200
    assert updated.json() == {"id": 3, "username": "Dana", "score": 25}
    assert [p["id"] for p in client.get("/leaderboard").json()] == [2, 1, 3]

    deleted = client.delete("/players/3")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get("/players/3").status_code == 404
    assert len(client.get("/scores").json()) == 2


def test_data_survives_app_restart_and_deletions_stay_deleted(tmp_path):
    database = tmp_path / "persistent.db"
    with TestClient(create_app(database)) as first:
        created = first.post("/players", json={"username": "Charlie"})
        player_id = created.json()["id"]
        assert first.post(f"/players/{player_id}/scores", json={"points": 25}).status_code == 201
        assert first.put(f"/players/{player_id}", json={"username": "Dana"}).status_code == 200
        assert first.delete("/players/1").status_code == 204

    assert database.is_file()
    with TestClient(create_app(database)) as restarted:
        assert restarted.get(f"/players/{player_id}").json() == {
            "id": player_id,
            "username": "Dana",
            "score": 25,
        }
        assert restarted.get(f"/players/{player_id}/scores").json()[0]["points"] == 25
        assert restarted.get("/players/1").status_code == 404
        assert restarted.get("/players/2").status_code == 200


def test_foreign_key_and_cascade_are_in_database(api):
    client, database = api
    with sqlite3.connect(database) as connection:
        columns = connection.execute("PRAGMA foreign_key_list(scores)").fetchall()
        assert columns[0][2:5] == ("players", "player_id", "id")
        connection.execute("PRAGMA foreign_keys=ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO scores (player_id, points) VALUES (999, 10)")

    assert client.delete("/players/1").status_code == 204
    assert all(score["player_id"] != 1 for score in client.get("/scores").json())


@pytest.mark.parametrize(
    "method,path,data,expected",
    [
        ("POST", "/players", {"username": "alice"}, 400),
        ("PUT", "/players/2", {"username": " ALICE "}, 400),
        ("GET", "/players/99", None, 404),
        ("PUT", "/players/99", {"username": "Nobody"}, 404),
        ("DELETE", "/players/99", None, 404),
        ("GET", "/players/99/scores", None, 404),
        ("POST", "/players/99/scores", {"points": 1}, 404),
        ("POST", "/players", {"username": "   "}, 422),
        ("POST", "/players", {"username": "x" * 51}, 422),
        ("POST", "/players", {"username": "A", "score": 99}, 422),
        ("POST", "/players/1/scores", {"points": 0}, 422),
        ("POST", "/players/1/scores", {"points": "10"}, 422),
        ("GET", "/players/0", None, 422),
    ],
)
def test_error_statuses(api, method, path, data, expected):
    client, _ = api
    assert client.request(method, path, json=data).status_code == expected


def test_swagger_routes_include_all_resources(api):
    client, _ = api
    assert client.get("/docs").status_code == 200
    routes = client.get("/openapi.json").json()["paths"]
    assert set(routes["/players"].keys()) == {"get", "post"}
    assert set(routes["/players/{player_id}"].keys()) == {"get", "put", "delete"}
    assert set(routes["/players/{player_id}/scores"].keys()) == {"get", "post"}
    assert set(routes["/scores"].keys()) == {"get"}
