"""Plugin entry point for the example deployment.

The core imports every module named in `LAMBDA_ERP_PLUGINS` on startup (after
setup(), before any documents are created) and calls its `register()`. Point the
deployment at this module with `LAMBDA_ERP_PLUGINS=acme`.
"""
from api.services import register_doctype
from lambda_erp.hooks import register_hook

from .sales_invoice import AcmeSalesInvoice


def on_invoice_submitted(doc) -> None:
    # `after_submit` fires post-commit: the voucher is already durable, so this
    # is the place for side-effects (notifications, external sync). A raise here
    # does NOT roll back the committed invoice. (Use a `before_submit` hook for
    # guards that must abort the submit.)
    print(f"[acme] Sales Invoice {doc.name} submitted — would notify billing", flush=True)


def register() -> None:
    # 1) Replace the core Sales Invoice with our subclass (override logic).
    register_doctype("Sales Invoice", AcmeSalesInvoice)
    # 2) Add a side-effect on submit without replacing anything (extend).
    register_hook("Sales Invoice:after_submit", on_invoice_submitted)
