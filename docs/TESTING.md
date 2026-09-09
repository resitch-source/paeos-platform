# Testing PAEOS in a browser

PAEOS 1.0.0 ships a complete backend API (110 operations across all phases) plus
a small status-page frontend. Today the **testable web surface is the interactive
API docs (Swagger UI)**, where you can log in and exercise every feature from the
browser. (A click-through domain UI is being built separately — see the roadmap
note at the bottom.)

## Option A — Docker (one command, recommended)

Requires Docker + Docker Compose.

```bash
# 1. Bring up PostgreSQL+PostGIS, Redis, and the API (runs migrations on start).
cd infra && docker compose up --build

# 2. In another terminal, seed a demo tenant + admin.
docker compose exec api python -m scripts.seed_demo
```

The API is now at **http://localhost:8000** and the status-page frontend can be
run separately (Option C).

## Option B — Local (no Docker)

Requires Python 3.11 and a local PostgreSQL 16 + PostGIS 3.4.

```bash
make venv                     # one-time: create the backend virtualenv
export PAEOS_DATABASE_URL="postgresql+psycopg://<user>:<pass>@localhost:5432/<db>"
make migrate                  # apply all migrations
make seed                     # provision the demo tenant + admin
make run                      # start the API at http://localhost:8000
```

## Log in and click through the features (Swagger UI)

1. Open **http://localhost:8000/docs**.
2. Expand **POST `/api/v1/auth/login`**, click **Try it out**, and send:
   ```json
   {
     "tenant_slug": "farm",
     "email": "admin@demofarm.ph",
     "password": "supersecret123"
   }
   ```
   Copy the `access_token` from the response.
3. Click the green **Authorize** button (top right), paste the token, and
   authorize. Every endpoint you call now runs as the demo tenant's admin.
4. Exercise a real flow, for example:
   - `POST /api/v1/inventory/items` — create an item (e.g. code `COPRA`).
   - `POST /api/v1/inventory/warehouses` — create a warehouse.
   - `POST /api/v1/inventory/movements` — stock **IN** 500.
   - `GET /api/v1/inventory/stock?item_id=…&warehouse_id=…` — see 500.
   - `POST /api/v1/trading/customers`, then `POST /api/v1/trading/orders`.
   - `POST /api/v1/trading/orders/{id}/lines` — add 100 @ 80.00 PHP.
   - `GET /api/v1/trading/orders/{id}/total` — see `8000.00 PHP`.
   - `POST /api/v1/trading/orders/{id}/transition` `{"event":"confirm"}`, then
     `POST /api/v1/trading/orders/{id}/fulfill` — stock drops to 400.
   - Other areas to try: `/api/v1/agrisim/scenarios/run` (EOQ), `/api/v1/ai/…`
     (advisory agents), `/api/v1/agri/…`, `/api/v1/integration/messages` (IoT).
5. Platform build info (no auth): **`GET /api/v1/info`**, **`/api/v1/meta`**,
   **`/api/v1/health`**, **`/api/v1/ready`**.

### Demo credentials
| field | value |
|-------|-------|
| tenant_slug | `farm` |
| email | `admin@demofarm.ph` |
| password | `supersecret123` |

Override with `DEMO_SLUG`, `DEMO_NAME`, `DEMO_EMAIL`, `DEMO_PASSWORD` env vars
before running the seed. The seed is idempotent — re-running it is a no-op.

## Option C — Status-page frontend

The React frontend is a Foundation status shell (it reads `/api/v1/meta`):

```bash
cd frontend
npm ci
npm run dev            # http://localhost:5173, proxies /api to :8000
```

## Roadmap: click-through domain UI

The frontend was intentionally scaffolded as a status shell — domain screens were
out of scope for the FX→13 backend roadmap. A browser UI with real screens (login
→ dashboard → inventory → sales orders, …) is being added as a separate,
phase-gated effort; until those screens land, Swagger UI is the full-feature test
surface.
