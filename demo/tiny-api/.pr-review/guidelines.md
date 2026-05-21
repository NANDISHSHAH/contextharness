# Tiny API — review guidelines

- **Auth:** Never bypass `get_current_user` for protected routes.
- **Billing:** Refunds must go through `refund_invoice`; no direct DB writes in API layer.
- **Imports:** `services/api` must not import billing internals except via public functions.
