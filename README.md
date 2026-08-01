# Nova World

Everything for Nova World in one repo: FastAPI backend, the user-facing web app, and the admin dashboard.
Deploy all three from a single Render Blueprint — no local build required.

```
nova-world/
├── backend/     FastAPI + Postgres API (auth, posts, DMs, stories, admin, push)
├── frontend/    Vite + React — builds to two pages: the main app and /admin
└── render.yaml  One Blueprint that provisions the DB + API + web app together
```

## Deploy (from GitHub, no local machine needed)
1. Unzip this into a new GitHub repo (e.g. via GitHub Codespaces — create the repo, upload/commit these files).
2. On Render: **New > Blueprint**, point it at the repo. `render.yaml` at the root provisions:
   - `nova-world-db` — Postgres
   - `nova-world-api` — the backend (runs Alembic migrations on every deploy)
   - `nova-world-web` — the static frontend, built from `frontend/`, serving the main app at `/` and the admin dashboard at `/admin`
3. Render will ask for the env vars marked `sync: false` in `render.yaml` — fill in:
   - `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_PUBLIC_BASE_URL` — from an S3-compatible bucket (Cloudflare R2 is free and easiest)
   - `FCM_SERVER_KEY` — optional, for push notifications; leave blank and push calls just no-op
4. Once `nova-world-api` is live, open its Render shell and run:
   `python -m scripts.make_admin you@example.com`
   That account can now log in and use `/admin`.
5. If your API's URL ends up different from `https://nova-world-api.onrender.com`, update the
   `VITE_API_BASE_URL` value in `render.yaml` (or in the Render dashboard for `nova-world-web`) to match,
   then redeploy the frontend.

## Local development
```bash
# backend
cd backend
pip install -r requirements.txt --break-system-packages
export DATABASE_URL=postgresql://...   # a local or Render Postgres instance
export JWT_SECRET_KEY=dev-secret
alembic upgrade head
uvicorn app.main:app --reload

# frontend, in a second terminal
cd frontend
npm install
cp .env.example .env   # point VITE_API_BASE_URL at your local backend
npm run dev
```

See `backend/README.md` for the full API reference, security notes, and scaling plan.
