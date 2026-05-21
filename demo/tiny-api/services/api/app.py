"""API gateway — routes and auth dependency."""

from packages.core.models import User


def get_current_user(token: str) -> User | None:
    if not token:
        return None
    return User(id="u1", email="demo@example.com")


def list_invoices_for_user(user: User) -> list[str]:
    from services.billing.invoices import fetch_invoices

    return [inv.id for inv in fetch_invoices(user.id)]
