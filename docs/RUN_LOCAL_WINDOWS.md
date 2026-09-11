# Run PAEOS locally on Windows

This guide takes you from a fresh Windows PC to a working PAEOS web app in your
browser: sign in, click through Inventory, and fulfil a sales order.

There are two parts, both required:

1. **Backend stack** (database + API) — run with **Docker Desktop**.
2. **Web UI** (the React frontend) — run with **Node.js**.

> **Why can't I just open the GitHub page?**
> GitHub only *stores* the code. GitHub Pages can only show static pages (the
> README). PAEOS is a full-stack app — it needs a live database and a running
> API — so it has to run on a computer. This guide runs it on yours.

---

## 0. Install the two tools (once)

| Tool | Download | Notes |
|------|----------|-------|
| **Docker Desktop** | <https://www.docker.com/products/docker-desktop/> | On Windows it uses **WSL2**. If the installer asks, let it enable WSL2 and reboot. After install, **open Docker Desktop and wait until it says "Engine running".** |
| **Node.js (LTS)** | <https://nodejs.org/> | Pick the **LTS** installer (20.x or newer). Accept defaults. |
| **Git** | <https://git-scm.com/download/win> | Only needed for the `git clone` step; you can also download the repo as a ZIP from GitHub instead. |

Verify all three from **PowerShell** (press `Start`, type *PowerShell*, Enter):

```powershell
docker --version
node --version
git --version
```

Each should print a version. If `docker --version` errors, Docker Desktop
isn't running yet — open it and wait for "Engine running".

---

## 1. Get the code

In PowerShell, pick a folder you like (here, your user folder) and clone:

```powershell
cd $HOME
git clone https://github.com/resitch-source/paeos-platform.git
cd paeos-platform
```

(Or download the ZIP from the GitHub repo's green **Code** button → *Download
ZIP*, unzip it, and `cd` into the folder.)

---

## 2. Start the backend (database + API)

From the repo root:

```powershell
cd infra
docker compose up --build
```

The first run downloads images and builds the API, so give it **3–10 minutes**.
Leave this window **open** — it's your running server. You'll know it's ready
when the log shows Alembic running the migrations (`Running upgrade …
0013_integration_iot`) followed by:

```
Uvicorn running on http://0.0.0.0:8000
```

The API container automatically runs the database migrations on start, so the
schema is built for you.

**Check it:** open <http://localhost:8000/docs> in your browser. You should see
the interactive **Swagger API** page. (Build info is at
<http://localhost:8000/api/v1/info>.)

---

## 3. Seed a demo tenant + admin login

Open a **second** PowerShell window (leave the first one running the server):

```powershell
cd $HOME\paeos-platform\infra
docker compose exec api python -m scripts.seed_demo
```

This prints the demo credentials. They are:

| Field | Value |
|-------|-------|
| Tenant | `farm` |
| Email | `admin@demofarm.ph` |
| Password | `supersecret123` |

The seed is safe to re-run — if the tenant already exists it just says so.

---

## 4. Start the web UI

In that second PowerShell window:

```powershell
cd $HOME\paeos-platform\frontend
npm ci
npm run dev
```

When it prints `Local: http://localhost:5173/`, open **<http://localhost:5173>**
in your browser.

> Leave `VITE_API_BASE` **unset** (don't create a `.env` for it). The dev server
> proxies `/api` to the backend on port 8000 for you; setting a base URL causes
> cross-origin (CORS) errors.

---

## 5. Click through it

1. **Sign in** with `farm` / `admin@demofarm.ph` / `supersecret123`.
2. **Inventory** → add an item (e.g. `COPRA`), add a warehouse (e.g.
   `WH-MAIN`), then **Stock in** 500. On-hand shows 500.
3. **Sales Orders** → create a customer → create an order on that warehouse →
   add a line for the item → **Confirm** → **Fulfil**. The order moves to
   *fulfilled* and stock is posted OUT through the central inventory service
   (on-hand drops accordingly).

That's the full loop — the same one shown working in the project screenshots.

---

## Stopping and restarting

- **Stop the UI / seed window:** press `Ctrl+C`.
- **Stop the backend:** in the first window press `Ctrl+C`, then optionally
  `docker compose down` to remove the containers. Your data is kept in a Docker
  volume (`pgdata`); `docker compose down -v` also **deletes the data**.
- **Start again later:** `cd infra; docker compose up` (no `--build` needed
  unless the code changed), then `npm run dev` in `frontend`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `docker : The term 'docker' is not recognized` | Docker Desktop isn't installed or its PowerShell integration isn't loaded. Reinstall, then restart PowerShell. |
| Compose hangs at `db … waiting` | Docker Desktop engine isn't running. Open Docker Desktop, wait for **Engine running**, retry. |
| `port is already allocated` (5432 / 8000 / 5173) | Another program uses that port. Close it, or stop other Postgres/Node instances. |
| Browser: **"API unreachable: Failed to fetch"** | The backend (step 2) isn't up yet, or you set `VITE_API_BASE`. Confirm <http://localhost:8000/docs> loads and remove any frontend `.env`. |
| `npm ci` errors about lockfile | Run `npm install` once instead, then `npm run dev`. |
| Swagger loads but login fails | You haven't run the seed (step 3). Run it, then sign in. |

---

## What's next

To make PAEOS reachable at a real public URL (from your phone, or to share),
it needs a host that runs full apps — e.g. Render or Railway — which is a
separate, **gated** deployment step. See `docs/DEPLOYMENT_RUNBOOK.md`.
