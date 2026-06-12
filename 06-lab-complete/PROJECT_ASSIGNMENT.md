# PROJECT_ASSIGNMENT — Production-ready AI Agent

## Project Name

**Production-ready AI Agent**

## Mục tiêu

Xây dựng REST API agent production-ready, tích hợp toàn bộ kiến thức Day 12:

- Container hóa multi-stage Docker
- Config từ environment variables (12-factor)
- API key authentication
- Rate limiting và cost guard
- Health/readiness probes
- Graceful shutdown
- Stateless design với Redis (conversation, rate, cost)
- Load balancing Nginx + scale horizontal

## Kiến trúc

```
Client
  │
  ▼
Nginx (port 80) ── round-robin ──► Agent x N (port 8000)
  │                                      │
  └──────────────────────────────────────┼──► Redis
                                         │      ├── conversation:{user_id}
                                         │      ├── rate:{user_id}:{minute}
                                         │      └── cost:{user_id}:{YYYY-MM}
                                         ▼
                                    Mock LLM / OpenAI
```

**Components**

| Service | Role |
|---------|------|
| `nginx` | Load balancer, public entrypoint |
| `agent` | FastAPI app, stateless workers |
| `redis` | Shared state for history, rate limit, cost |

## Productionization Steps

1. **Config** — all secrets and limits from env vars (`.env.example`)
2. **Security** — `X-API-Key` header, no hardcoded secrets
3. **Observability** — JSON structured logs, `/health`, `/ready`
4. **Resilience** — SIGTERM graceful shutdown, readiness checks Redis
5. **Scale** — stateless agents + Redis + Nginx LB
6. **CI/CD** — GitHub Actions lint/test/build (see `CI_CD.md`)
7. **Deploy** — Railway or Render blueprint

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Service info |
| GET | `/health` | No | Liveness probe |
| GET | `/ready` | No | Readiness probe (Redis ping) |
| POST | `/ask` | `X-API-Key` | Ask agent a question |

### POST `/ask`

**Request**

```json
{
  "question": "Hello",
  "user_id": "user1"
}
```

**Headers:** `X-API-Key: secret`

**Response (200)**

```json
{
  "answer": "...",
  "user_id": "user1",
  "conversation_length": 1,
  "metadata": {
    "environment": "production",
    "model": "mock-agent",
    "cost_usd": 0.001
  }
}
```

**Error codes**

| Code | Condition |
|------|-----------|
| 401 | Missing/invalid API key |
| 402 | Monthly budget exceeded ($10/user) |
| 429 | Rate limit exceeded (10 req/min/user) |
| 503 | Not ready (Redis unavailable) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `AGENT_API_KEY` | — | API key for `/ask` |
| `LOG_LEVEL` | `INFO` | Log level |
| `RATE_LIMIT_PER_MINUTE` | `10` | Per-user rate limit |
| `MONTHLY_BUDGET_USD` | `10` | Per-user monthly budget |
| `ENVIRONMENT` | `production` | Environment name |
| `MODEL_NAME` | `mock-agent` | Model identifier |
| `OPENAI_API_KEY` | — | Optional; uses mock if empty |

## Docker Commands

```bash
cd 06-lab-complete

# Build and run full stack (3 agent instances)
docker compose up --build --scale agent=3

# Stop
docker compose down

# Production readiness check
python check_production_ready.py
```

## Test Commands

```bash
curl http://localhost/health
curl http://localhost/ready

curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret" \
  -d '{"question":"Hello","user_id":"user1"}'

curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello","user_id":"user1"}'
# Expected: 401
```

## Deploy — Railway

```bash
npm i -g @railway/cli
cd 06-lab-complete
railway login
railway init
railway variables set AGENT_API_KEY=your-production-key
railway variables set ENVIRONMENT=production
railway variables set REDIS_URL=redis://...
railway up
railway domain
```

GitHub Actions CD: set secret `RAILWAY_TOKEN` (see `CI_CD.md`).

## Deploy — Render

Chi tiết: **[RENDER_DEPLOY.md](RENDER_DEPLOY.md)**

1. Push repo to GitHub
2. Render Dashboard → **New → Blueprint**
3. Blueprint path: `06-lab-complete/render.yaml`
4. Apply → chờ build
5. Copy `AGENT_API_KEY` từ Environment tab
6. Test public API (curl trong RENDER_DEPLOY.md)

**Blueprint tạo 2 services:** `lab6-redis` (Key Value) + `lab6-ai-agent` (Docker web)

## Public API URL

**TODO — update after deploy**

```
https://lab6-ai-agent.onrender.com
```

## Redis Key Design

| Key pattern | Purpose |
|-------------|---------|
| `conversation:{user_id}` | Conversation history (JSON list) |
| `rate:{user_id}:{minute}` | Request count per minute |
| `cost:{user_id}:{YYYY-MM}` | Accumulated cost per month |

## Deliverables Checklist

- [x] Modular `app/` package
- [x] Multi-stage Dockerfile
- [x] docker-compose (agent + redis + nginx)
- [x] Scale `--scale agent=3`
- [x] API key auth, rate limit, cost guard
- [x] Health + readiness with Redis check
- [x] JSON structured logging
- [x] Graceful shutdown
- [x] `check_production_ready.py`
- [x] CI/CD workflows
- [ ] Public URL + screenshots — TODO after deploy
