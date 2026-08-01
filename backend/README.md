# Nova World API

FastAPI backend for Nova World: auth, profiles, posts (photo/video), likes, comments, follows,
notifications, direct messages, stories, admin moderation, and push notifications.
Deploys the same way as NovaVPN — push to GitHub, Render builds and hosts it, no local machine needed.

## Stack
- **API**: FastAPI (Python), JWT auth (access + refresh tokens), bcrypt password hashing
- **Database**: Postgres (Render managed), schema managed by **Alembic migrations**
- **Media storage**: any S3-compatible bucket (Cloudflare R2 recommended — free egress, S3 API)
- **Push**: Firebase Cloud Messaging (covers iOS, Android, and web push from one API)
- **Hosting**: Render web service, auto-deploys from `main`

## Setup (all from GitHub, no local build needed)
1. Push this folder to a new GitHub repo (e.g. via GitHub Codespaces, like the NovaVPN project).
2. On Render: **New > Blueprint**, point it at the repo — `render.yaml` provisions the Postgres DB
   and web service together, and runs `alembic upgrade head` on every deploy so the schema stays in sync.
3. Create a Cloudflare R2 bucket (or S3/B2), get access keys, fill in the `S3_*` env vars in the
   Render dashboard.
4. (Optional, for push notifications) Create a Firebase project, get a server key, set `FCM_SERVER_KEY`
   in Render. Without it, push calls silently no-op — everything else still works.
5. Once deployed, promote yourself to admin from the Render shell:
   `python -m scripts.make_admin you@example.com`

## Database migrations
Schema changes go through Alembic instead of auto-created tables:
```bash
# after changing a model in app/models.py
alembic revision --autogenerate -m "add bio_link to users"
alembic upgrade head          # apply locally / in CI
```
Render runs `alembic upgrade head` automatically as part of every deploy's build step, so pushing a
migration alongside a model change is enough — no manual DB console work.

## API overview
| Endpoint | Method | Purpose |
|---|---|---|
| `/auth/signup` `/auth/login` `/auth/refresh` | POST | Account + tokens |
| `/users/me` | GET/PATCH | Own profile |
| `/users/{username}` | GET | Public profile |
| `/users/{username}/follow` | POST/DELETE | Follow / unfollow |
| `/posts` | POST | Upload photo/video + caption |
| `/posts/feed` `/posts/explore` | GET | Feeds (paginated via `cursor`) |
| `/posts/{id}/like` | POST/DELETE | Like / unlike |
| `/posts/{id}/comments` | GET/POST | Comments |
| `/stories` | POST | Post a 24h story |
| `/stories/feed` | GET | Active stories from people you follow |
| `/stories/{id}/view` | POST | Mark viewed |
| `/messages/threads` | GET | Inbox, one row per conversation |
| `/messages/{username}` | GET/POST | Conversation history / send DM |
| `/notifications` | GET | Likes, comments, follows on your posts |
| `/push/register` | POST | Register a device token for push |
| `/admin/users` | GET | List/search users (admin only) |
| `/admin/users/{id}/verify` `/unverify` | POST | Toggle verified badge |
| `/admin/users/{id}/ban` `/unban` | POST | Suspend / restore an account |
| `/admin/posts/{id}` | DELETE | Moderation removal of any post |
| `/admin/stats` | GET | Basic platform counts |

Interactive docs are auto-generated at `/docs` once deployed.

## Security notes
- Passwords are bcrypt-hashed, never stored or logged in plain text.
- Access tokens expire in 30 min; refresh tokens in 30 days.
- Banned users (`is_banned`) are rejected at the auth-dependency level, a ban takes effect on their
  very next request, no need to revoke tokens individually.
- Admin routes require `is_admin`, checked server-side on every request, there's no client-trusted
  "am I admin" flag.
- `CORSMiddleware` currently allows `*`, restrict `allow_origins` to your actual app domains before launch.
- File uploads are type- and size-validated server-side (25MB cap, image/video allowlist).

## Scaling plan
- **Now (MVP)**: single Render web service + single Postgres instance handles low thousands of users fine.
- **Media**: already offloaded to S3-compatible storage, put a CDN in front of `S3_PUBLIC_BASE_URL`
  (Cloudflare does this for free on R2).
- **Feed reads**: add Redis for feed/profile caching and move to write-time fan-out as post volume grows.
- **Stories cleanup**: expired stories are filtered out at query time (`expires_at > now()`) but not
  deleted, add a daily cron/worker to purge expired rows and their media from storage.
- **Web service**: stateless (JWT, no server-side sessions), so scaling to multiple Render instances is
  a config change, not a code change.
- **Database**: add read replicas and composite indexes on hot paths as write volume grows (foreign keys
  are already indexed).

## Not yet built
- Real-time delivery for DMs/notifications (currently pull-based, add WebSockets for live updates)
- Rate limiting / abuse prevention on signup, uploads, and messaging
- Admin audit log (who banned/verified whom, and when)
- Story highlights (keeping select stories past 24h)
