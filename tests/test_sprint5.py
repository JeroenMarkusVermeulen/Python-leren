"""Controleer databasecompatibiliteit, businessregels en foutafhandeling."""

import pytest
from fastapi.testclient import TestClient

from app.database import Database
from app.main import create_app
from app.schemas.player import PlayerCreate
from app.services.errors import DuplicateUsernameError, PlayerNotFoundError
from app.services.players import PlayerService
from sprint4 import create_app as create_sprint4_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "sprint5.db")) as api:
        yield api


def test_sprint4_database_is_reused_without_losing_data(tmp_path):
    database = tmp_path / "shared.db"
    with TestClient(create_sprint4_app(database)) as old_api:
        player_id = old_api.post("/players", json={"username": "Charlie"}).json()["id"]
        old_api.post(f"/players/{player_id}/scores", json={"points": 25})
        old_api.delete("/players/1")

    with TestClient(create_app(database)) as new_api:
        assert new_api.get(f"/players/{player_id}").json() == {
            "id": player_id, "username": "Charlie", "score": 25,
        }
        assert new_api.get("/players/1").status_code == 404
        assert new_api.put(f"/players/{player_id}", json={"username": "Dana"}).status_code == 200
        assert new_api.post(f"/players/{player_id}/scores", json={"points": 5}).status_code == 201

    with TestClient(create_sprint4_app(database)) as old_api:
        assert old_api.get(f"/players/{player_id}").json() == {
            "id": player_id, "username": "Dana", "score": 30,
        }
        assert old_api.get("/players/1").status_code == 404


def test_app_instances_use_separate_databases(tmp_path):
    with (
        TestClient(create_app(tmp_path / "first.db")) as first,
        TestClient(create_app(tmp_path / "second.db")) as second,
    ):
        assert first.post("/players", json={"username": "Charlie"}).status_code == 201
        assert first.delete("/players/1").status_code == 204
        assert second.get("/players").json() == [
            {"id": 1, "username": "Alice", "score": 100},
            {"id": 2, "username": "Bob", "score": 150},
        ]
        assert second.get("/players/3").status_code == 404


def test_service_rolls_back_duplicates_and_works_without_http(tmp_path):
    database = Database(tmp_path / "service.db")
    try:
        database.initialize()
        with database.session_factory() as session:
            service = PlayerService(session)
            with pytest.raises(DuplicateUsernameError):
                service.create_player(PlayerCreate(username=" ALICE "))
            with pytest.raises(DuplicateUsernameError):
                service.update_player(2, PlayerCreate(username="alice"))
            assert service.get_player(2).username == "Bob"
            assert service.get_player(2).score == 150
            player = service.create_player(PlayerCreate(username="Charlie"))
            assert player.username == "Charlie"
            assert player.score == 0
            with pytest.raises(PlayerNotFoundError):
                service.get_player(999)
    finally:
        database.close()


def test_business_errors_keep_the_existing_http_messages(client):
    missing = client.get("/players/999")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Speler met ID 999 is niet gevonden."}
    duplicate = client.post("/players", json={"username": "alice"})
    assert duplicate.status_code == 400
    assert duplicate.json() == {"detail": "Deze gebruikersnaam bestaat al."}
    assert client.get("/players/1").json() == {"id": 1, "username": "Alice", "score": 100}


def test_scores_add_up_and_leaderboard_breaks_ties_by_id(client):
    assert client.post("/players/1/scores", json={"points": 25}).status_code == 201
    assert client.post("/players/1/scores", json={"points": 25}).status_code == 201
    assert client.get("/leaderboard").json() == [
        {"id": 1, "username": "Alice", "score": 150},
        {"id": 2, "username": "Bob", "score": 150},
    ]
    assert client.get("/players/1").json()["score"] == 150
    assert len(client.get("/players/1/scores").json()) == 3
    assert set(client.get("/players/1").json()) == {"id", "username", "score"}
    assert set(client.get("/scores").json()[0]) == {"id", "player_id", "points"}


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("/players", {}),
        ("/players", {"username": None}),
        ("/players", {"username": 123}),
        ("/players/1/scores", {}),
        ("/players/1/scores", {"points": -1}),
        ("/players/1/scores", {"points": True}),
        ("/players/1/scores", {"points": 1.5}),
        ("/players/1/scores", {"points": 1, "player_id": 2}),
    ],
)
def test_additional_invalid_inputs_are_rejected(client, endpoint, payload):
    assert client.post(endpoint, json=payload).status_code == 422


def test_empty_database_is_not_reseeded_after_restart(tmp_path):
    database = tmp_path / "empty.db"
    with TestClient(create_app(database)) as first:
        assert first.delete("/players/1").status_code == 204
        assert first.delete("/players/2").status_code == 204
    with TestClient(create_app(database)) as restarted:
        assert restarted.get("/players").json() == []
        assert restarted.get("/scores").json() == []
        assert restarted.get("/leaderboard").json() == []
