# DEPLOYMENT — Lab 06 Production AI Agent

## Public URL

**Production URL:** https://ai-agent-production-ukv4.onrender.com

**Platform:** Render (Docker Web Service)

**Region:** Singapore (onrender.com)

**Deployed:** 2026-06-12

---

## Environment Variables (Render)

| Variable | Set? | Notes |
|----------|------|-------|
| `ENVIRONMENT` | ✅ | `production` |
| `AGENT_API_KEY` | ✅ | Set in Render Dashboard (auto-generated) |
| `PORT` | ✅ | Injected by Render |
| `REDIS_URL` | ⬜ | Not linked — app uses in-memory fallback (`storage: memory`) |
| `LOG_LEVEL` | ✅ | `INFO` |
| `MODEL_NAME` | ✅ | `mock-agent` |

---

## Test Commands

Replace `YOUR_API_KEY` with value from Render → Environment → `AGENT_API_KEY`.

```bash
curl https://ai-agent-production-ukv4.onrender.com/

curl https://ai-agent-production-ukv4.onrender.com/health

curl https://ai-agent-production-ukv4.onrender.com/ready

curl -X POST https://ai-agent-production-ukv4.onrender.com/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"user_id":"test","question":"Hello"}'
```

**Expected results (verified 2026-06-12):**

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /` | 200 | Service info JSON |
| `GET /health` | 200 | `"status":"ok"`, `"storage":"memory"` |
| `GET /ready` | 200 | `"ready":true` |
| `POST /ask` (no key) | 401 | Auth required |
| `POST /ask` (with key) | 200 | Mock agent response |

Raw curl output: [`screenshots/curl-output.txt`](screenshots/curl-output.txt)

---

## Screenshots

| File | Mô tả | Trạng thái |
|------|-------|------------|
| [`screenshots/dashboard.png`](screenshots/dashboard.png) | Render Dashboard — service overview | ⬜ **Cần chụp thủ công** (yêu cầu đăng nhập Render) |
| [`screenshots/running.png`](screenshots/running.png) | Production URL `/` — service đang chạy | ✅ |
| [`screenshots/health.png`](screenshots/health.png) | Browser `GET /health` | ✅ |
| [`screenshots/ready.png`](screenshots/ready.png) | Browser `GET /ready` | ✅ |
| [`screenshots/api-test.png`](screenshots/api-test.png) | Terminal curl `/health`, `/ready`, `POST /ask` | ✅ |

Hướng dẫn chụp ảnh còn thiếu: [`screenshots/README.md`](screenshots/README.md)

---

## Architecture (Render)

```
Internet → Render Load Balancer → Docker (FastAPI)
                                      ↓
                              In-memory store (REDIS_URL chưa set)
```

**TODO:** Link Render Key Value hoặc Upstash → set `REDIS_URL` → `/health` hiển thị `"storage":"redis"`.

---

## Redeploy

Push to `main` → Render auto-deploy (if enabled) hoặc Manual Deploy từ Dashboard.

Blueprint: `06-lab-complete/render.yaml`
