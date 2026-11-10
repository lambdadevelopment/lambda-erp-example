# Acme ERP — example deployment on the lambda-erp open-core

A minimal, **working example of a customer deployment** built on top of the
published Lambda ERP packages. It depends on the **published** artifacts — it
does **not** fork or vendor the core repo:

| Layer | Depends on | From |
|-------|-----------|------|
| Backend | `lambda-erp[postgres]==1.4.1` | PyPI |
| Frontend | `@lambda-development/erp-core@1.4.1` | npm |

It doubles as the **template** a real (private) customer repo copies. Core fixes
arrive via a version bump in `pyproject.toml` / `frontend/package.json` — never a
merge into a fork. Bump both to the same version, and read the core's
CHANGELOG for anything a deployment has to change.

## What it customizes

All overrides go through the public extension seams — zero core files touched.

**Backend** (`acme/`, loaded via `LAMBDA_ERP_PLUGINS=acme`):
- `acme/sales_invoice.py` — `AcmeSalesInvoice(SalesInvoice)` overriding
  `_get_gl_entries` (the **replace** seam).
- `acme/plugin.py` — `register()` wires it up with `register_doctype("Sales
  Invoice", AcmeSalesInvoice)` and adds a `register_hook("Sales
  Invoice:after_submit", …)` side-effect (the **extend** seam).
- `acme/pdf_templates/` — custom **PDF** templates, wired via
  `register_pdf_template_dir(…)` in `register()` (the **PDF override** seam):
  `document.html` (invoices, orders, offers), `delivery_note.html`,
  `proposal.html` and `reservation.html`. Each started as a copy of the core's
  template and gets the same render context, so you restyle the same data
  (logo, letterhead, CSS). Keep the blocks that print document content: the
  core checks every rendered PDF against the document and refuses an export
  that leaves something out. These files are also the "Standard" layout under
  Settings → PDF Templates.
- `acme/swiss_qr.py` — a Swiss QR-bill on invoices via `register_pdf_context`,
  plus `register_pdf_template_requirement` so every invoice layout prints it.

**Frontend** (`frontend/src/`):
- `plugin.tsx` — `configureBranding` (name + brand colour), `configureApiBase`,
  `registerComponent("Dashboard", AcmeDashboard)`, and a page of its own with
  `registerRoute` + `registerNavItem`.
- `dashboard.tsx` — the replacement dashboard; `kpis.tsx` — the added page.
- `brand.css` — overrides the `--brand` CSS token for first paint.

## Layout

```
lambda-erp-example/
  pyproject.toml          # lambda-erp[postgres]==1.4.1 (the backend core)
  app.py                  # ASGI entry: core app + serves THIS frontend build
  acme/
    plugin.py             # register() — overrides + hooks + PDF template dir
    sales_invoice.py      # AcmeSalesInvoice(SalesInvoice)
    swiss_qr.py           # QR-bill on invoices (register_pdf_context)
    pdf_templates/        # custom PDFs (register_pdf_template_dir)
      document.html  delivery_note.html  proposal.html  reservation.html
  frontend/
    package.json          # @lambda-development/erp-core 1.4.1 + its peers
    tailwind.config.ts    # scans the core dist + uses its preset
    src/{main,plugin,dashboard,kpis}.tsx, brand.css
  Dockerfile              # one container: builds frontend, serves via backend
  .env.example
```

## Run it

### Local dev (two processes)

```bash
# 1) Backend — installs lambda-erp from PyPI + the acme plugin
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env                 # LAMBDA_ERP_PLUGINS=acme is the key line
export $(grep -v '^#' .env | xargs)  # or use your preferred env loader
uvicorn app:app --reload --port 8000

# 2) Frontend — installs the core npm lib + peers, proxies /api to :8000
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

### One container (production shape)

```bash
docker build -t acme-erp .
docker run -p 8000:8000 -v acme-data:/data acme-erp   # http://localhost:8000
```

The image builds the frontend (core npm package + overrides) and serves it from
the backend (core pip package + the acme plugin) at one origin.

> **Going to production?** Read [docs/deploying.md](docs/deploying.md) first —
> it covers the one thing that bites: **persistence**. SQLite needs a real disk
> (it can't get file locks on a network share like Azure Files), so on a managed
> container platform you point `LAMBDA_ERP_DB` at **PostgreSQL** instead. Also
> covers replicas, the stable `JWT_SECRET_KEY`, and the public address needed
> to connect the ERP to lambda.dev, Claude or ChatGPT.

## How the pieces fit

- **Plugin loading:** the core reads `LAMBDA_ERP_PLUGINS` on startup and calls
  each module's `register()`. That's the single entry point for backend
  overrides + hooks.
- **Serving the frontend:** the core only auto-serves a frontend that sits next
  to its own installed package, so this repo's `app.py` imports the core
  FastAPI `app` and mounts **this** repo's `frontend/dist` (with an SPA
  fallback). Run the backend from the repo root so the relative path resolves.
- **Styling ("consumer scans source"):** our own Tailwind build generates the
  utilities, scanning the core's built JS (`tailwind.config.ts` `content`) and
  using its shared `tailwind-preset`. We import the core's `styles.css` (tokens
  + base layers) and override the `--brand` token.

## License

MIT. See [LICENSE](LICENSE) for the full text.

## Trademarks and affiliations

Lambda ERP and lambda.dev are product and trade names of TORUS INVESTMENTS AG. It is not affiliated with, endorsed by, or sponsored by OpenAI, Anthropic, SAP, Oracle, Microsoft, or any other company named in this repository. SAP, Business One, S/4HANA, Oracle, NetSuite, Microsoft, Dynamics, OpenAI, GPT, Anthropic, and Claude are trademarks of their respective owners and are referenced here only for descriptive and comparative purposes (nominative fair use). The ERP uses the OpenAI API as a customer; you supply your own API key.
