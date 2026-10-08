"""HTTP-stub voor offline tests; echte Auth en RLS moeten ook in Supabase worden getest."""

import json
import time
from uuid import UUID

import httpx


ALICE_ID = str(UUID(int=1))
BOB_ID = str(UUID(int=2))
TEST_PASSWORD = "AlleenVoorTest123!"


def user_record(user_id: str, email: str) -> dict:
    return {
        "id": user_id, "aud": "authenticated", "role": "authenticated",
        "email": email, "app_metadata": {}, "user_metadata": {},
        "created_at": "2026-10-08T00:00:00Z", "is_anonymous": False,
    }


class SupabaseStub:
    def __init__(self):
        self.users = {
            "alice@example.com": user_record(ALICE_ID, "alice@example.com"),
            "bob@example.com": user_record(BOB_ID, "bob@example.com"),
        }
        self.tokens = {"token-alice": ALICE_ID, "token-bob": BOB_ID}
        self.players = {
            1: {"id": 1, "username": "Alice", "owner_id": None},
            2: {"id": 2, "username": "Bob", "owner_id": None},
        }
        self.scores = {
            1: {"id": 1, "player_id": 1, "points": 100},
            2: {"id": 2, "player_id": 2, "points": 150},
        }
        self.next_player_id = 3
        self.next_score_id = 3
        self.calls = []
        self.signup_confirmation = True
        self.provider_failure = None

    def session(self, user_id: str) -> dict:
        user = next(user for user in self.users.values() if user["id"] == user_id)
        token = next(token for token, owner in self.tokens.items() if owner == user_id)
        return {
            "access_token": token, "refresh_token": "refresh-" + token,
            "token_type": "bearer", "expires_in": 1800,
            "expires_at": int(time.time()) + 1800, "user": user,
        }

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else {}
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        self.calls.append((request.method, request.url.path, token, body))
        if self.provider_failure:
            if self.provider_failure == "network":
                raise httpx.ConnectError("Testverbinding verbroken", request=request)
            return httpx.Response(self.provider_failure, json={
                "msg": "Provider-detail met vertrouwelijke invoer", "code": "over_request_rate_limit",
            })

        if request.url.path == "/auth/v1/signup":
            user = user_record(str(UUID(int=3)), body["email"])
            self.users[body["email"]] = user
            if self.signup_confirmation:
                return httpx.Response(200, json=user)
            self.tokens["token-new-user"] = user["id"]
            return httpx.Response(200, json=self.session(user["id"]))

        if request.url.path == "/auth/v1/token":
            if request.url.params.get("grant_type") == "refresh_token":
                old = body.get("refresh_token", "").removeprefix("refresh-")
                user_id = self.tokens.get(old)
            else:
                user = self.users.get(body.get("email"))
                user_id = user["id"] if user and body.get("password") == TEST_PASSWORD else None
            if user_id:
                return httpx.Response(200, json=self.session(user_id))
            return httpx.Response(400, json={"msg": "Invalid login credentials", "code": "invalid_credentials"})

        if request.url.path == "/auth/v1/user":
            user_id = self.tokens.get(token)
            if user_id:
                user = next(user for user in self.users.values() if user["id"] == user_id)
                return httpx.Response(200, json=user)
            return httpx.Response(401, json={"msg": "Invalid JWT", "code": "bad_jwt"})

        resource = request.url.path.removeprefix("/rest/v1/")
        if resource == "game_player_totals":
            rows = [
                {"id": row["id"], "username": row["username"], "score": sum(
                    score["points"] for score in self.scores.values() if score["player_id"] == row["id"]
                )}
                for row in self.players.values()
            ]
        elif resource == "game_players":
            if request.method == "POST":
                if any(row["username"].casefold() == body["username"].casefold() for row in self.players.values()):
                    return httpx.Response(409, json={"code": "23505", "message": "duplicate key", "details": None, "hint": None})
                if body["owner_id"] != self.tokens.get(token):
                    return httpx.Response(403, json={"code": "42501", "message": "RLS denied", "details": None, "hint": None})
                row = {"id": self.next_player_id, **body}
                self.next_player_id += 1
                self.players[row["id"]] = row
                return httpx.Response(201, json=[row])
            rows = list(self.players.values())
        elif resource == "game_scores":
            if request.method == "POST":
                row = {"id": self.next_score_id, **body}
                self.next_score_id += 1
                self.scores[row["id"]] = row
                return httpx.Response(201, json=[row])
            rows = list(self.scores.values())
        else:
            raise AssertionError("Onverwachte Supabase-request: " + str(request.url))

        for field in ("id", "player_id"):
            value = request.url.params.get(field)
            if value:
                rows = [row for row in rows if row.get(field) == int(value.removeprefix("eq."))]
        rows.sort(key=lambda row: row["id"])

        if request.method in {"PATCH", "DELETE"}:
            rows = [row for row in rows if row.get("owner_id") == self.tokens.get(token)]
            if request.method == "PATCH":
                if rows and any(
                    row["id"] != rows[0]["id"] and row["username"].casefold() == body["username"].casefold()
                    for row in self.players.values()
                ):
                    return httpx.Response(409, json={"code": "23505", "message": "duplicate key", "details": None, "hint": None})
                for row in rows:
                    row.update(body)
            else:
                for row in rows:
                    del self.players[row["id"]]
                    self.scores = {key: score for key, score in self.scores.items() if score["player_id"] != row["id"]}
            return httpx.Response(200, json=rows)

        start = int(request.url.params.get("offset", 0))
        limit = int(request.url.params.get("limit", len(rows)))
        return httpx.Response(200, json=rows[start:start + limit])
