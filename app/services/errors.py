"""Businessfouten; de API-laag bepaalt bijbehorende HTTP-statuscodes."""


class PlayerNotFoundError(Exception):
    def __init__(self, player_id: int) -> None:
        super().__init__(f"Speler met ID {player_id} is niet gevonden.")


class DuplicateUsernameError(Exception):
    def __init__(self) -> None:
        super().__init__("Deze gebruikersnaam bestaat al.")
