# Lab 6 — Production-ready AI Agent

Final project combining all Day 12 concepts: Docker, Redis stateless design, API gateway patterns, health probes, and CI/CD.

## Structure

```
06-lab-complete/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── auth.py
│   ├── rate_limiter.py
│   ├── cost_guard.py
│   ├── schemas.py
│   ├── redis_client.py
│   ├── agent.py
│   └── logging_config.py
├── nginx/nginx.conf
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── check_production_ready.py
├── PROJECT_ASSIGNMENT.md
└── CI_CD.md
```

## Quick Start (Docker Compose)

```bash
cd 06-lab-complete
cp .env.example .env.local   # optional for local overrides
docker compose up --build --scale agent=3
```

Nginx listens on **http://localhost** (port 80).

## Test Commands

```bash
curl http://localhost/health
curl http://localhost/ready

curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret" \
  -d '{"question":"Hello","user_id":"user1"}'

# Expected: 401 without API key
curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello","user_id":"user1"}'
```

## Local Development (without Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export AGENT_API_KEY=test-key REDIS_URL=redis://localhost:6379/0
uvicorn app.main:app --reload --port 8000
```

## Production Readiness

```bash
python check_production_ready.py
```

## CI/CD

See [CI_CD.md](CI_CD.md) for GitHub Actions pipelines.

## Deploy

- **Railway:** `railway up` (see `railway.toml`)
- **Render:** Blueprint `render.yaml` — see **[RENDER_DEPLOY.md](RENDER_DEPLOY.md)**
- **Public URL:** TODO — update after deploy
