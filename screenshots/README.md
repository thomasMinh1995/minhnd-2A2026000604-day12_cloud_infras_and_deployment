# Lab 06 — Screenshot Evidence

**Production URL:** https://ai-agent-production-ukv4.onrender.com

**Captured:** 2026-06-12

---

## Files in this folder

| File | Status | Source |
|------|--------|--------|
| `running.png` | ✅ Created | Browser — `GET /` (JSON service info) |
| `health.png` | ✅ Created | Browser — `GET /health` |
| `ready.png` | ✅ Created | Browser — `GET /ready` |
| `api-test.png` | ✅ Created | Terminal curl output (rendered from `curl-output.txt`) |
| `curl-output.txt` | ✅ Created | Raw `curl -i` responses |
| `dashboard.png` | ⬜ **Manual** | Render Dashboard (requires login) |

---

## Limitation

Cursor browser **cannot** capture Render Dashboard (`dashboard.png`) because it requires your Render account login. All public API endpoints were captured automatically.

---

## How to capture `dashboard.png` (manual)

1. Open [Render Dashboard](https://dashboard.render.com)
2. Select service **ai-agent-production** (or `lab6-ai-agent`)
3. Ensure status shows **Live** / green
4. Screenshot the page showing:
   - Service name
   - Public URL: `https://ai-agent-production-ukv4.onrender.com`
   - Last deploy time / commit
5. Save as **`screenshots/dashboard.png`**

**Optional `running.png` alternative:** Events tab or Logs tab showing successful deploy + `"event": "ready"` in logs.

---

## How screenshots were captured (automated)

### Browser (running, health, ready)

```
https://ai-agent-production-ukv4.onrender.com/
https://ai-agent-production-ukv4.onrender.com/health
https://ai-agent-production-ukv4.onrender.com/ready
```

Note: Render free tier may show loading page on first request (cold start). Wait ~30s and refresh.

### Terminal (api-test)

```bash
curl -i https://ai-agent-production-ukv4.onrender.com/health
curl -i https://ai-agent-production-ukv4.onrender.com/ready
curl -i -X POST https://ai-agent-production-ukv4.onrender.com/ask \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
```

Output saved to `curl-output.txt` and rendered to `api-test.png`.

---

## Verification summary (2026-06-12)

| Check | Result |
|-------|--------|
| `GET /` | 200 ✅ |
| `GET /health` | 200 ✅ (`storage: memory`) |
| `GET /ready` | 200 ✅ |
| `POST /ask` + API key | 200 ✅ |
| `POST /ask` no key | 401 ✅ |
