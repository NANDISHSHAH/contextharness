"""Expected behaviour for Tiny API."""

from services.api.app import get_current_user, list_invoices_for_user


def test_get_current_user_rejects_empty_token():
    assert get_current_user("") is None


def test_list_invoices_for_authenticated_user():
    user = get_current_user("valid")
    assert user is not None
    ids = list_invoices_for_user(user)
    assert len(ids) >= 1
