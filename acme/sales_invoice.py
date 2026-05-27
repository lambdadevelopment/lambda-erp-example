"""Example backend override (the 'replace' seam).

Subclass a core document class and register it (see plugin.py). Once registered,
every loader path — create / load / update / submit / cancel — and document
conversions use this subclass instead of the core `SalesInvoice`. The same
pattern works for `validate()`, `on_submit()`, etc.
"""
from lambda_erp.accounting.sales_invoice import SalesInvoice


class AcmeSalesInvoice(SalesInvoice):
    def _get_gl_entries(self):
        gl = super()._get_gl_entries()
        # Customer-specific posting goes here. Returning the core entries
        # unchanged keeps the books balanced; append to / adjust `gl` to add,
        # e.g., a commission accrual or a statistical cost-center split. Keep
        # the voucher balanced — the engine rejects an imbalanced posting.
        return gl
