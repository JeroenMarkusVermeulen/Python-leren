"""Supabase Auth regelt accounts, wachtwoordhashing en het controleren van JWTs."""

from supabase_auth.errors import AuthApiError, AuthRetryableError, AuthUnknownError

from app.supabase_api.database import RequestContext
from app.supabase_api.errors import (
    AuthenticationError, RateLimitError, RegistrationError, UpstreamUnavailableError,
)
from app.supabase_api.schemas import AuthUser, RegisterRequest, RegistrationResult, Token


def token_response(session) -> Token:
    return Token(
        access_token=session.access_token, refresh_token=session.refresh_token,
        token_type=session.token_type, expires_in=session.expires_in,
    )


class AuthService:
    def __init__(self, context: RequestContext) -> None:
        self.context = context

    @staticmethod
    def _check_provider_error(exc: AuthApiError) -> None:
        if exc.status == 429:
            raise RateLimitError() from exc
        if exc.status >= 500:
            raise UpstreamUnavailableError() from exc

    def register(self, data: RegisterRequest) -> RegistrationResult:
        try:
            result = self.context.client.auth.sign_up({
                "email": str(data.email), "password": data.password.get_secret_value(),
            })
        except AuthApiError as exc:
            self._check_provider_error(exc)
            raise RegistrationError() from exc
        except (AuthRetryableError, AuthUnknownError) as exc:
            raise UpstreamUnavailableError() from exc
        return RegistrationResult(
            message="Registratie ontvangen. Bevestig zo nodig je e-mailadres en log in.",
            confirmation_required=result.session is None,
            session=token_response(result.session) if result.session else None,
        )

    def login(self, email: str, password: str) -> Token:
        if not email or len(email) > 254 or not password or len(password) > 128:
            raise AuthenticationError()
        try:
            result = self.context.client.auth.sign_in_with_password({
                "email": email.strip(), "password": password,
            })
        except AuthApiError as exc:
            self._check_provider_error(exc)
            raise AuthenticationError() from exc
        except (AuthRetryableError, AuthUnknownError) as exc:
            raise UpstreamUnavailableError() from exc
        if result.session is None:
            raise AuthenticationError()
        return token_response(result.session)

    def current_user(self) -> AuthUser:
        if not self.context.access_token:
            raise AuthenticationError()
        try:
            result = self.context.client.auth.get_user(self.context.access_token)
        except AuthApiError as exc:
            self._check_provider_error(exc)
            raise AuthenticationError() from exc
        except (AuthRetryableError, AuthUnknownError) as exc:
            raise UpstreamUnavailableError() from exc
        if result.user is None or result.user.is_anonymous:
            raise AuthenticationError()
        return AuthUser(id=result.user.id, email=result.user.email)

    def refresh(self, refresh_token: str) -> Token:
        try:
            result = self.context.client.auth.refresh_session(refresh_token)
        except AuthApiError as exc:
            self._check_provider_error(exc)
            raise AuthenticationError() from exc
        except (AuthRetryableError, AuthUnknownError) as exc:
            raise UpstreamUnavailableError() from exc
        if result.session is None:
            raise AuthenticationError()
        return token_response(result.session)
