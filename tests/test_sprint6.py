"""Test de werkelijke Supabase SDK via een HTTP-stub, zonder echte accounts te maken."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.supabase_api.config import Settings
from app.supabase_api.main import create_app
from tests.supabase_stub import ALICE_ID, BOB_ID, TEST_PASSWORD, SupabaseStub


@pytest.fixture
def api():
    backend = SupabaseStub()
    settings = Settings("https://example.supabase.co", "sb_publishable_test_key")
    with TestClient(create_app(settings, http_transport=httpx.MockTransport(backend))) as client:
        yield client, backend


def login(client, email="alice@example.com") -> dict:
    result = client.post("/auth/login", data={"username": email, "password": TEST_PASSWORD})
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def test_register_delegates_password_to_supabase_without_returning_it(api):
    client, backend = api
    response = client.post("/auth/register", json={"email": "new@example.com", "password": TEST_PASSWORD})
    assert response.status_code == 201
    assert response.json()["confirmation_required"] is True
    assert response.json()["session"] is None
    assert backend.calls[-1][1] == "/auth/v1/signup"
    assert backend.calls[-1][3]["password"] == TEST_PASSWORD
    assert TEST_PASSWORD not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_signup_without_confirmation_can_return_a_session(api):
    client, backend = api
    backend.signup_confirmation = False
    response = client.post("/auth/register", json={"email": "new@example.com", "password": TEST_PASSWORD})
    assert response.status_code == 201
    assert response.json()["confirmation_required"] is False
    assert response.json()["session"]["access_token"] == "token-new-user"


def test_login_current_user_refresh_and_client_isolation(api):
    client, backend = api
    alice = login(client)
    bob = login(client, "bob@example.com")
    assert client.get("/auth/me", headers=alice).json() == {"id": ALICE_ID, "email": "alice@example.com"}
    assert client.get("/auth/me", headers=bob).json() == {"id": BOB_ID, "email": "bob@example.com"}
    assert client.get("/auth/me").status_code == 401
    refresh = client.post("/auth/refresh", json={"refresh_token": "refresh-token-alice"})
    assert refresh.status_code == 200
    assert refresh.json()["expires_in"] == 1800
    assert refresh.headers["cache-control"] == "no-store"
    assert client.get("/players").status_code == 200
    assert backend.calls[-1][2] == "sb_publishable_test_key"


@pytest.mark.parametrize("email,password", [
    ("alice@example.com", "wrong-password"), ("missing@example.com", TEST_PASSWORD),
    ("alice@example.com", "x" * 129),
])
def test_bad_login_is_401_with_generic_message(api, email, password):
    client, _ = api
    response = client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert password not in response.text


@pytest.mark.parametrize("header", [None, "Bearer invalid-token", "Bearer expired-token", "Basic abc"])
def test_invalid_or_missing_token_is_rejected(api, header):
    client, _ = api
    response = client.get("/auth/me", headers={"Authorization": header} if header else {})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("method,url,body", [
    ("POST", "/players", {"username": "Charlie"}),
    ("PUT", "/players/1", {"username": "Charlie"}),
    ("DELETE", "/players/1", None),
    ("POST", "/players/1/scores", {"points": 25}),
])
def test_all_write_endpoints_require_login(api, method, url, body):
    client, backend = api
    assert client.request(method, url, json=body).status_code == 401
    assert not backend.calls


def test_owner_crud_scores_and_public_reads_still_work(api):
    client, backend = api
    owner = login(client)
    assert client.get("/").json() == {"message": "De Players API werkt!"}
    assert client.get("/players").json() == [
        {"id": 1, "username": "Alice", "score": 100},
        {"id": 2, "username": "Bob", "score": 150},
    ]
    created = client.post("/players", json={"username": " Charlie "}, headers=owner)
    assert created.status_code == 201
    assert created.headers["location"] == "/players/3"
    assert created.json() == {"id": 3, "username": "Charlie", "score": 0}
    assert backend.players[3]["owner_id"] == ALICE_ID
    added = client.post("/players/3/scores", json={"points": 25}, headers=owner)
    assert added.status_code == 201
    assert added.json() == {"id": 3, "player_id": 3, "points": 25}
    assert client.get("/players/3/scores").json() == [added.json()]
    assert len(client.get("/scores").json()) == 3
    assert client.get("/players/3").json()["score"] == 25
    assert client.put("/players/3", json={"username": "Dana"}, headers=owner).json() == {
        "id": 3, "username": "Dana", "score": 25,
    }
    assert [p["id"] for p in client.get("/leaderboard").json()] == [2, 1, 3]
    deleted = client.delete("/players/3", headers=owner)
    assert deleted.status_code == 204 and deleted.content == b""
    assert client.get("/players/3").status_code == 404
    assert len(client.get("/scores").json()) == 2


@pytest.mark.parametrize("method,url,body", [
    ("PUT", "/players/3", {"username": "Stolen"}),
    ("DELETE", "/players/3", None),
    ("POST", "/players/3/scores", {"points": 99}),
])
def test_another_user_cannot_modify_the_owner_player(api, method, url, body):
    client, backend = api
    owner = login(client)
    client.post("/players", json={"username": "Charlie"}, headers=owner)
    other = login(client, "bob@example.com")
    calls_before = len(backend.calls)
    assert client.request(method, url, json=body, headers=other).status_code == 403
    assert all(call[0] == "GET" for call in backend.calls[calls_before:])
    assert client.get("/players/3").json() == {"id": 3, "username": "Charlie", "score": 0}


def test_legacy_player_cannot_be_claimed_by_matching_auth_metadata(api):
    client, backend = api
    backend.users["alice@example.com"]["user_metadata"] = {"owner_id": ALICE_ID, "username": "Alice", "role": "admin"}
    owner = login(client)
    assert client.put("/players/1", json={"username": "Stolen"}, headers=owner).status_code == 403
    assert client.delete("/players/1", headers=owner).status_code == 403


def test_anonymous_supabase_accounts_are_rejected(api):
    client, backend = api
    backend.users["alice@example.com"]["is_anonymous"] = True
    assert client.get("/auth/me", headers={"Authorization": "Bearer token-alice"}).status_code == 401


def test_duplicate_names_and_missing_player_codes_are_preserved(api):
    client, _ = api
    owner = login(client)
    assert client.post("/players", json={"username": "alice"}, headers=owner).status_code == 400
    assert client.get("/players/999").status_code == 404
    assert client.put("/players/999", json={"username": "Nobody"}, headers=owner).status_code == 404
    assert client.delete("/players/999", headers=owner).status_code == 404
    assert client.post("/players/999/scores", json={"points": 1}, headers=owner).status_code == 404


@pytest.mark.parametrize("body", [
    {"email": "new@example.com", "password": "abc123"},
    {"email": "invalid", "password": TEST_PASSWORD},
    {"email": "new@example.com", "password": " " * 12},
    {"email": "new@example.com", "password": TEST_PASSWORD, "role": "admin"},
])
def test_registration_validation_never_echoes_passwords(api, body):
    client, backend = api
    response = client.post("/auth/register", json=body)
    assert response.status_code == 422
    assert body["password"] not in response.text
    assert not backend.calls


@pytest.mark.parametrize("url,body", [
    ("/players", {"username": "Charlie", "owner_id": BOB_ID}),
    ("/players", {"username": " "}),
    ("/players/1/scores", {"points": 0}),
    ("/players/1/scores", {"points": True}),
    ("/players/1/scores", {"points": "10"}),
])
def test_invalid_crud_bodies_are_422(api, url, body):
    client, _ = api
    assert client.post(url, json=body, headers=login(client)).status_code == 422


@pytest.mark.parametrize("failure,expected", [(429, 429), (500, 503), ("network", 503)])
def test_provider_failures_do_not_leak_details(api, failure, expected):
    client, backend = api
    backend.provider_failure = failure
    response = client.post("/auth/login", data={"username": "alice@example.com", "password": TEST_PASSWORD})
    assert response.status_code == expected
    assert "vertrouwelijke" not in response.text
    assert TEST_PASSWORD not in response.text


def test_docs_show_the_auth_endpoints_and_protected_operations(api):
    client, _ = api
    assert client.get("/docs").status_code == 200
    document = client.get("/openapi.json").json()
    assert document["paths"]["/auth/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert document["paths"]["/players"]["post"]["security"] == [{"HTTPBearer": []}]
    assert not document["paths"]["/players"]["get"].get("security")
    assert not document["paths"]["/auth/login"]["post"].get("security")
    assert set(document["paths"]["/players/{player_id}"]) == {"get", "put", "delete"}


@pytest.mark.parametrize("key", ["", "sb_secret_wrong", "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.sig"])
def test_privileged_keys_cannot_be_used_to_bypass_rls(key):
    with pytest.raises(ValueError, match="(?i)publishable"):
        Settings("https://example.supabase.co", key).validate()


def test_export_preserves_source_ids_and_does_not_change_sqlite(tmp_path):
    from fastapi.testclient import TestClient
    from scripts.export_sqlite import import_sql, read_snapshot
    from sprint4 import create_app as create_sqlite_app

    database = tmp_path / "source.db"
    with TestClient(create_sqlite_app(database)) as old:
        old.post("/players", json={"username": "Quoted ' player"})
    before = database.read_bytes()
    snapshot = read_snapshot(database)
    assert database.read_bytes() == before
    assert snapshot["players"][2]["id"] == 3
    assert snapshot["players"][2]["username"] == "Quoted ' player"
    generated = import_sql(snapshot)
    assert "jsonb_to_recordset" in generated
    assert "doeltabellen zijn niet leeg" in generated
    assert "on conflict" not in generated.lower()
    assert snapshot == json.loads(json.dumps(snapshot))
