# Game Score API

## Sprint 3

Een REST API beheert *resources* via URL's en HTTP-methoden. CRUD staat voor
Create, Read, Update en Delete. In deze API zijn spelers en scores de resources.
`GET` leest, `POST` maakt aan, `PUT` vervangt de bewerkbare spelergegevens en
`DELETE` verwijdert een speler. De server geeft JSON terug.

| Methode | Endpoint | Actie | Succes |
| --- | --- | --- | --- |
| GET | `/` | Controleer of de API werkt | 200 |
| GET | `/players` | Alle spelers | 200 |
| GET | `/players/{player_id}` | Eén speler | 200 |
| POST | `/players` | Speler maken | 201 |
| PUT | `/players/{player_id}` | Gebruikersnaam wijzigen | 200 |
| DELETE | `/players/{player_id}` | Speler en diens scores verwijderen | 204 |
| GET | `/scores` | Alle score-registraties | 200 |
| GET | `/players/{player_id}/scores` | Scores van één speler | 200 |
| POST | `/players/{player_id}/scores` | Punten toevoegen | 201 |
| GET | `/leaderboard` | Spelers op totaalscore, aflopend | 200 |

Een ontbrekende speler geeft **404**, een dubbele gebruikersnaam **400** en
ongeldige JSON-invoer **422**. `username` is verplicht, bevat na het weghalen
van spaties 1 tot 50 tekens en is uniek zonder onderscheid tussen hoofdletters.
`points` moet een positief geheel getal zijn. Nieuwe spelers beginnen met score
0. De twee voorbeeldspelers hebben elk één initiële score-registratie. Een
nieuwe registratie verhoogt de totaalscore van de speler. De data staat in het
geheugen en wordt bij een herstart teruggezet naar Alice en Bob.

### Starten

Gebruik Python 3.10 of nieuwer:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python sprint3.py
```

Open daarna [Swagger UI](http://127.0.0.1:8000/docs) voor de interactieve
documentatie. Kies een endpoint, klik op **Try it out** en voer JSON in. Je kunt
dezelfde requests ook met Postman sturen.

Voorbeeld voor `POST /players`:

```json
{"username": "Charlie"}
```

Voorbeeld voor `POST /players/3/scores`:

```json
{"points": 25}
```

Een handige Swagger-controle is: voeg Charlie toe (201), voeg 25 punten toe
(201), controleer `/players/3` en `/leaderboard` (200), wijzig de naam met
`PUT /players/3` (200), verwijder de speler (204) en controleer dat
`GET /players/3` daarna 404 geeft. Probeer ook `{"points": -1}` (422) en een
bestaande gebruikersnaam (400). De tests voeren deze requests automatisch uit:

```powershell
.\.venv\Scripts\python -m pytest -q
```

Sprint 2 blijft beschikbaar via `python sprint2.py` op poort 8001.

## Sprint 4: SQLite en SQLAlchemy

Sprint 3 bewaart lijsten in het geheugen; die beginnen na een herstart opnieuw.
Sprint 4 gebruikt een SQLite-bestand (`game_scores.db`) en SQLAlchemy om rijen
in tabellen te lezen en te schrijven. Een relationele database bewaart records
in tabellen met kolommen. Een ORM koppelt een Python-klasse aan zo'n tabel.

### Databaseontwerp

| Tabel | Kolom | Betekenis |
| --- | --- | --- |
| `players` | `id` | Primary Key: uniek nummer van de speler |
| `players` | `username` | Naam die de API toont |
| `players` | `username_key` | Unieke naam voor vergelijken zonder hoofdletterverschil |
| `scores` | `id` | Primary Key: uniek nummer van de score |
| `scores` | `player_id` | Foreign Key naar `players.id` |
| `scores` | `points` | Toegevoegde punten (positief geheel getal) |

Eén speler heeft nul of meer scores. `scores.player_id` verwijst naar precies
één speler. De Foreign Key voorkomt scores voor een niet-bestaande speler.
Als een speler wordt verwijderd, worden diens scores ook verwijderd. De
totaalscore in de API is de som van zijn score-rijen en staat daarom niet als
afzonderlijke kolom in `players`.

```text
players (id PK, username, username_key UNIQUE)
    1 ──────────────── 0..N
scores  (id PK, player_id FK → players.id, points)
```

De SQL achter de belangrijkste bewerkingen is `INSERT` voor POST, `SELECT`
voor GET, `UPDATE` voor PUT en `DELETE` voor DELETE. SQLAlchemy maakt die
queries uit de Python-modellen. Bij `POST /players/{id}/scores` verloopt het
pad zo: FastAPI ontvangt JSON → Pydantic valideert `points` → SQLAlchemy zoekt
de speler → een `ScoreRow` wordt toegevoegd → `session.commit()` schrijft de
rij naar SQLite → de API antwoordt met 201. Een volgende GET leest de rijen
opnieuw uit de database.

### Starten en controleren

Installeer de afhankelijkheden zoals hierboven en start vanuit deze map:

```powershell
.\.venv\Scripts\python sprint4.py
```

Open [Swagger UI](http://127.0.0.1:8000/docs). De routes en statuscodes zijn
gelijk aan Sprint 3. Bij de eerste start worden Alice en Bob één keer
aangemaakt. Het databasebestand staat naast `sprint4.py` en wordt niet naar
GitHub geüpload. Verwijderde voorbeeldspelers komen na een herstart niet terug.

Test de opslag zelf: maak met `POST /players` een speler, noteer diens ID, voeg
punten toe via `POST /players/{id}/scores`, stop de server met Ctrl+C en start
`sprint4.py` opnieuw. `GET /players/{id}` toont dezelfde speler en totaalscore.
Automatische tests doen dezelfde herstartcontrole met een tijdelijke database:

```powershell
.\.venv\Scripts\python -m pytest -q
```

Voor de korte terugblik na Sprint 4 staat een spreektekst met projectdemo in
[SPOTLIGHT.md](SPOTLIGHT.md).

Gerichte naslag: [FastAPI over SQL-databases](https://fastapi.tiangolo.com/tutorial/sql-databases/),
[SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/) en
[SQLite](https://www.sqlite.org/about.html).
