"""Veilige foutmeldingen zonder wachtwoorden, tokens of provider-details."""


class AuthenticationError(Exception):
    def __init__(self) -> None:
        super().__init__("Geen geldige login. Log opnieuw in.")


class AuthorizationError(Exception):
    def __init__(self) -> None:
        super().__init__("Je mag alleen je eigen speler aanpassen.")


class RegistrationError(Exception):
    def __init__(self) -> None:
        super().__init__("Registratie niet mogelijk. Controleer je gegevens of probeer in te loggen.")


class UpstreamUnavailableError(Exception):
    def __init__(self) -> None:
        super().__init__("Supabase is tijdelijk niet bereikbaar. Probeer het later opnieuw.")


class RateLimitError(Exception):
    def __init__(self) -> None:
        super().__init__("Te veel pogingen. Wacht even voordat je opnieuw probeert.")
