"""Swiss QR-bill (QR-Rechnung) generation for invoice PDFs.

Builds a Swiss payment QR-bill and returns it as a PNG data URI that the PDF
template embeds. Wired into the core via its `register_pdf_context()` seam, so
it augments the invoice render context with `qr_bill_img` (a `data:` URI) for
Sales Invoices that have a creditor IBAN (Company.iban) and a CHF/EUR amount.

Reference type is auto-detected from the creditor account, per the QR-bill spec:

  * QR-IBAN (bank IID 30000-31999) -> QRR  (27-digit QR reference, mod-10 check)
  * regular IBAN                   -> SCOR (ISO 11649 'RF…' creditor reference)
  * (no usable invoice number)     -> NON  (no reference)

This is country-specific, so it lives in the deployment plugin, not the core.
Depends on `qrbill` and `cairosvg` (declared in this package's dependencies).
"""
import base64
import io

import cairosvg
from qrbill import QRBill
from qrbill.bill import esr

# Swiss QR-bills carry amounts in CHF or EUR only.
_QR_CURRENCIES = {"CHF", "EUR"}

# Country names -> ISO 3166-1 alpha-2 (the QR spec requires the 2-letter code).
_COUNTRY_CODES = {
    "switzerland": "CH", "schweiz": "CH", "suisse": "CH", "svizzera": "CH",
    "liechtenstein": "LI",
    "germany": "DE", "deutschland": "DE",
    "austria": "AT", "österreich": "AT", "oesterreich": "AT",
    "france": "FR", "italy": "IT", "italia": "IT",
}


def _country_code(value, default="CH"):
    v = (value or "").strip()
    if len(v) == 2 and v.isalpha():
        return v.upper()
    return _COUNTRY_CODES.get(v.lower(), default)


def _compact_iban(iban):
    return "".join((iban or "").split()).upper()


def _is_qr_iban(iban):
    """QR-IBAN: the bank IID (positions 5-9 of a CH/LI IBAN) is 30000-31999."""
    c = _compact_iban(iban)
    if len(c) < 9 or not c[4:9].isdigit():
        return False
    return 30000 <= int(c[4:9]) <= 31999


def _to_iso7064_digits(s):
    """Map A-Z -> 10-35 for the ISO 7064 mod-97 checksum; keep digits as-is."""
    out = ""
    for ch in s.upper():
        out += str(ord(ch) - 55) if ch.isalpha() else ch
    return out


def _scor_reference(invoice_no):
    """ISO 11649 structured creditor reference: RF + 2 check digits + base."""
    base = "".join(c for c in (invoice_no or "").upper() if c.isalnum())[:21]
    if not base:
        return None
    rem = int(_to_iso7064_digits(base + "RF00")) % 97
    return "RF" + str(98 - rem).zfill(2) + base


def _qrr_reference(invoice_no):
    """27-digit QR reference: invoice digits, right-justified, + mod-10 check."""
    digits = "".join(c for c in (invoice_no or "") if c.isdigit())[:26]
    if not digits:
        return None
    body = digits.zfill(26)
    return body + esr.calc_check_digit(body)


def _address(name, info):
    """Combined-address dict for qrbill from a master-record info dict."""
    info = info or {}
    line2 = "{} {}".format(info.get("zip_code", "") or "", info.get("city", "") or "").strip()
    return {
        "name": ((name or info.get("company_name") or "").strip() or "—")[:70],
        "line1": (info.get("address") or "").strip()[:70],
        "line2": line2[:70],
        "country": _country_code(info.get("country")),
    }


def qr_bill_provider(language="de"):
    """Build a register_pdf_context() provider that adds a Swiss QR-bill.

    `language` controls the payment-part labels (de/fr/it/en). Returns a
    `provider(doctype, name, context)` that yields `{"qr_bill_img": <data URI>}`
    for Sales Invoices with a creditor IBAN and a CHF/EUR amount, and None
    otherwise (so the template simply omits the bill).
    """

    def provider(doctype, name, context):
        if doctype not in ("Sales Invoice", "POS Invoice"):
            return None

        company_info = context.get("company_info") or {}
        iban = _compact_iban(company_info.get("iban"))
        if not iban:
            return None  # no creditor account -> no QR-bill

        currency = (context.get("currency") or "").upper()
        if currency not in _QR_CURRENCIES:
            return None

        doc = context.get("doc") or {}
        # Amount to pay: remaining balance if partially paid, else the full total.
        amount = doc.get("outstanding_amount")
        if amount is None or amount <= 0:
            amount = doc.get("grand_total") or 0
        amount = round(float(amount), 2)

        creditor = _address(context.get("company_name"), company_info)
        debtor = _address(context.get("party_name"), context.get("party_info"))
        # A debtor needs an address to be valid; leave it blank otherwise so the
        # payer fills it in by hand (a valid QR-bill variant).
        if not (debtor["line1"] or debtor["line2"]):
            debtor = None

        reference = _qrr_reference(name) if _is_qr_iban(iban) else _scor_reference(name)

        bill = QRBill(
            account=iban,
            creditor=creditor,
            amount="{:.2f}".format(amount),
            currency=currency,
            debtor=debtor,
            reference_number=reference,
            language=language,
        )

        svg = io.StringIO()
        bill.as_svg(svg)
        png = cairosvg.svg2png(bytestring=svg.getvalue().encode("utf-8"), output_width=2480)
        return {"qr_bill_img": "data:image/png;base64," + base64.b64encode(png).decode("ascii")}

    return provider
