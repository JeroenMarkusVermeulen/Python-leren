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
