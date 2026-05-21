"""Authentication module for the sample API."""

class AuthMiddleware:
    """Validates bearer tokens on each request."""

    def authenticate(self, token: str) -> bool:
        return bool(token)


class SessionStore:
    def create_session(self, user_id: str) -> str:
        return f"session-{user_id}"
