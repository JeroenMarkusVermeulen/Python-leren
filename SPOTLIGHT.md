# Developer Spotlight — Mijn beste oplossing

**Onderwerp:** waarom ik scores als aparte records opsla.

**Duur:** ongeveer 2 tot 2,5 minuten inclusief demo.
**Laat zien:** `sprint4.py` bij `PlayerRow` en `ScoreRow`, daarna `/docs`.

## Spreektekst

In Sprint 3 werkte mijn Game Score API al. Ik kon een speler toevoegen en
punten geven. Maar de spelers en scores stonden in Python-lijsten. Als ik de
server opnieuw startte, begon alles weer bij Alice en Bob. Dat was het moment
waarop ik zag waarom een backend een database nodig heeft.

Mijn oplossing in Sprint 4 is een SQLite-database met twee tabellen. In de code
zie je `PlayerRow` en `ScoreRow`. Elke speler heeft een uniek ID. Elke score
heeft een `player_id`, die naar de speler verwijst. Dat is de Foreign Key.
Daardoor hoort elke score bij een bestaande speler.

Ik heb ook besloten de totaalscore niet apart op te slaan. De API telt de
score-rijen op. Als er bijvoorbeeld 10 en 25 punten zijn toegevoegd, geeft
`GET /players/{id}` een totaalscore van 35. Zo kan de totaalscore niet
achterlopen op de opgeslagen scores.

**[Demo: open `/docs`, maak een speler aan, voeg punten toe en haal de speler
weer op. Noteer het ID. Stop en herstart de API en haal hetzelfde ID opnieuw
op.]**

De speler en de punten zijn er nog. De request is dus niet alleen in een
Python-lijst terechtgekomen. Pydantic controleert eerst de JSON, daarna maakt
SQLAlchemy een database-rij en `commit()` slaat die op in SQLite.

Wat ik hiervan heb geleerd: het ontwerp van de tabellen bepaalt ook hoe
betrouwbaar je API is. Door spelers en scores te koppelen en het totaal uit de
scores te berekenen, heb ik minder kans op tegenstrijdige gegevens.

## Mogelijke vragen

- **Wat is het verschil tussen Primary Key en Foreign Key?** Een Primary Key
  identificeert een rij in zijn eigen tabel; een Foreign Key verwijst naar een
  rij in een andere tabel.
- **Waarom SQLite?** Voor dit leerproject is één databasebestand genoeg. Je
  hebt geen aparte databaseserver nodig.
- **Wat gebeurt er bij verwijderen?** De scores van de speler verdwijnen mee.
- **Wat deed AI?** AI hielp bij het uitwerken en testen van de implementatie.
  Het belangrijkste om zelf te begrijpen is de relatie tussen de tabellen en
  wanneer `commit()` de gegevens blijvend opslaat.
