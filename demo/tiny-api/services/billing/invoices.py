"""Billing service — invoice retrieval."""

from packages.core.models import Invoice, User


def fetch_invoices(user_id: str) -> list[Invoice]:
    return [
        Invoice(id="inv-1", user_id=user_id, amount_cents=1999),
        Invoice(id="inv-2", user_id=user_id, amount_cents=499),
    ]


def refund_invoice(invoice_id: str) -> bool:
    return invoice_id.startswith("inv-")
