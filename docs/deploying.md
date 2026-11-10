# Deploying a Lambda ERP customer build

This example shows the **application** seams (plugin, branding). This doc covers
the **operational** part — getting a real, persistent deployment right. It's
provider-agnostic; adapt the specifics to your cloud.

> The one thing to get right is **persistence**. Everything else (build the
> image, run it behind TLS) is standard.

## The data model in one paragraph

The backend keeps *all* state in a single database. By default that database
is **SQLite** (`LAMBDA_ERP_DB` points at a file); on a managed platform it is
**PostgreSQL**. That choice shapes the rules below.

## Rule 1 — pick durable storage that SQLite can actually use, *or* use Postgres

SQLite needs real filesystem **file locks**. That has a sharp edge in the cloud:

- ✅ **A real local/block disk** (a VM's managed disk, a bare-metal volume): SQLite
  works perfectly. Point `LAMBDA_ERP_DB` at a file on it and you're done.
- ❌ **A network file share** (SMB/NFS "Azure Files", NFS mounts, many container
  platforms' only persistent-volume option): SQLite's locking does **not** work
  reliably. You'll get `database is locked` at startup — `PRAGMA journal_mode=WAL`
  fails outright (WAL needs a memory-mapped `-shm` file a network FS can't
  provide), and even plain writes fail on SMB. Do **not** put the SQLite file
  on a network share.

So on a platform whose *only* durable storage is a network share (e.g. Azure
Container Apps, many PaaS container hosts), don't fight SQLite — **use
PostgreSQL**:

```bash
pip install lambda-erp[postgres]          # pulls psycopg
export LAMBDA_ERP_DB="postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require"
```

This example already depends on `lambda-erp[postgres]`, so the image has the
driver. `lambda-erp` selects the backend from `LAMBDA_ERP_DB`: a
`postgresql://…` value uses Postgres; anything else is treated as a SQLite path.
No code change — same app, same seams. Put the URL (it contains a password) in a
**secret**, not a plaintext env var.

Rule of thumb:
- **VM / box with a disk** → SQLite is fine and simplest.
- **Managed container platform** → Postgres.

## Rule 2 — SQLite: one process; Postgres: as many as you like

- **SQLite** is single-writer: run **a single replica with `--workers 1`** and
  scale *up* (more CPU/RAM), not *out*.
- **Postgres** (lambda-erp >= 1.3): several workers and replicas can share one
  database, including an old and a new revision side by side during a deploy.
  Numbering, migrations and chat sessions are coordinated through the database.
  This requires a stable `JWT_SECRET_KEY` (Rule 3).

## Rule 3 — a stable `JWT_SECRET_KEY`

Set `JWT_SECRET_KEY` and keep it **constant across deploys** — a new value
invalidates every login cookie. If unset, the app generates one, which is fine
for local dev but means everyone is logged out on each restart, and with
Postgres it is required (each replica would generate a different one).

## Rule 4 — tell the app its public address

Behind a TLS proxy (any cloud load balancer or container platform) the app sees
plain `http://` requests. Set `OAUTH_REDIRECT_BASE` to the public
`https://` address: social sign-in uses it, and `app.py` passes it on as
`MCP_PUBLIC_URL`, which MCP / OAuth discovery advertises. Without it, connecting
the ERP to lambda.dev, Claude or ChatGPT (`https://<erp-host>/api/mcp`) fails
at sign-in. Set `MCP_PUBLIC_URL` yourself only if the two differ.

## Minimal production shape

One container, behind TLS, with the DB external:

```bash
docker build -t my-erp .
docker run -p 8000:8000 \
  -e LAMBDA_ERP_PLUGINS=acme \
  -e LAMBDA_ERP_DB="postgresql://erp:…@db.internal:5432/erp?sslmode=require" \
  -e JWT_SECRET_KEY="<stable-random>" \
  -e OAUTH_REDIRECT_BASE="https://erp.example.com" \
  -e OPENAI_API_KEY=… \
  my-erp
```

For a throwaway **demo**, ephemeral SQLite on the container's own disk is fine —
it just resets on each deploy. For anything you care about, follow Rule 1.

## Backups

- **Postgres**: use your provider's automated backups / point-in-time restore.
- **SQLite on a disk**: snapshot the volume, or copy the DB file (use the SQLite
  backup API / `VACUUM INTO` for a consistent copy while running).
