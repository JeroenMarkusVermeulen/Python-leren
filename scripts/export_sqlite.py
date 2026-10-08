"""Lees SQLite zonder te schrijven en genereer een gecontroleerde Postgres-import."""

import argparse
import json
import secrets
import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]


def read_snapshot(database: Path) -> dict:
    uri = database.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        players = [dict(row) for row in connection.execute(
            "SELECT id, username, username_key FROM players ORDER BY id"
        )]
        scores = [dict(row) for row in connection.execute(
            "SELECT id, player_id, points FROM scores ORDER BY id"
        )]
    player_ids = {row["id"] for row in players}
    for row in players:
        if type(row["id"]) is not int or row["id"] < 1:
            raise ValueError("Ongeldig speler-ID in de bron.")
        if not isinstance(row["username"], str) or not 1 <= len(row["username"].strip()) <= 50:
            raise ValueError("Ongeldige gebruikersnaam in de bron.")
    for row in scores:
        if type(row["id"]) is not int or row["id"] < 1:
            raise ValueError("Ongeldig score-ID in de bron.")
        if row["player_id"] not in player_ids or type(row["points"]) is not int or row["points"] <= 0:
            raise ValueError("Ongeldige score of spelerverwijzing in de bron.")
    return {"players": players, "scores": scores}


def import_sql(snapshot: dict) -> str:
    payload = json.dumps(snapshot, ensure_ascii=False)
    delimiter = "$sqlite_" + secrets.token_hex(8) + "$"
    while delimiter in payload:
        delimiter = "$sqlite_" + secrets.token_hex(8) + "$"
    quoted = delimiter + payload + delimiter
    return f"""-- Gegenereerd uit SQLite; bron-IDs worden behouden, geen bestaande rijen overschreven.
begin;
do $$
begin
    if exists (select 1 from public.game_players) or exists (select 1 from public.game_scores) then
        raise exception 'Import gestopt: de doeltabellen zijn niet leeg.';
    end if;
end;
$$;
insert into public.game_players (id, username, owner_id)
select id, username, null
from jsonb_to_recordset({quoted}::jsonb -> 'players') as p(id bigint, username text);
insert into public.game_scores (id, player_id, points)
select id, player_id, points
from jsonb_to_recordset({quoted}::jsonb -> 'scores') as s(id bigint, player_id bigint, points bigint);
select setval(pg_get_serial_sequence('public.game_players', 'id'),
    coalesce((select max(id) from public.game_players), 1),
    exists (select 1 from public.game_players));
select setval(pg_get_serial_sequence('public.game_scores', 'id'),
    coalesce((select max(id) from public.game_scores), 1),
    exists (select 1 from public.game_scores));
commit;
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=PROJECT_DIR / "game_scores.db")
    parser.add_argument("--output", type=Path, default=PROJECT_DIR / "migration-export.json")
    parser.add_argument("--sql-output", type=Path)
    args = parser.parse_args()
    snapshot = read_snapshot(args.database)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.sql_output:
        args.sql_output.write_text(import_sql(snapshot), encoding="utf-8")
    print(f"Export gereed: {len(snapshot['players'])} spelers, {len(snapshot['scores'])} scores.")


if __name__ == "__main__":
    main()
