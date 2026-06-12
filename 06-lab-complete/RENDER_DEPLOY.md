# Deploy Lab 6 lên Render

Hướng dẫn deploy `06-lab-complete` lên [Render](https://render.com) bằng Blueprint (`render.yaml`).

## Kiến trúc trên Render

```
Internet
   │
   ▼
Render Web Service (Docker)     lab6-ai-agent.onrender.com
   │  FastAPI agent
   │  PORT do Render inject
   │
   └──► Render Key Value (Redis)   REDIS_URL (internal)
         conversation / rate / cost
```

> **Lưu ý:** Docker Compose (nginx + scale x3) chỉ dùng **local**. Trên Render chạy **1 web service** + **Key Value Redis**.

---

## Bước 1 — Push code lên GitHub

```bash
git add 06-lab-complete/
git commit -m "Prepare Lab 6 for Render deploy"
git push origin main
```

Repository phải **public** hoặc Render có quyền truy cập.

---

## Bước 2 — Tạo Blueprint trên Render

1. Vào [Render Dashboard](https://dashboard.render.com)
2. **New +** → **Blueprint**
3. Connect GitHub repo của bạn
4. **Blueprint path:** `06-lab-complete/render.yaml`
5. Review services:
   - `lab6-redis` — Key Value (Redis)
   - `lab6-ai-agent` — Web Service (Docker)
6. Click **Apply**

Render sẽ tự:
- Build Docker image từ `06-lab-complete/Dockerfile`
- Tạo Redis và inject `REDIS_URL` vào web service
- Generate `AGENT_API_KEY` ngẫu nhiên

---

## Bước 3 — Lấy API key

1. Dashboard → service **lab6-ai-agent** → **Environment**
2. Copy giá trị `AGENT_API_KEY` (Render auto-generate)
3. (Tuỳ chọn) Set `OPENAI_API_KEY` nếu dùng OpenAI thật — không set thì dùng mock agent

---

## Bước 4 — Chờ deploy xong

- **Logs:** service → **Logs** — tìm dòng `"event": "ready"` và `"redis": "redis"`
- **Health check:** Render dùng `GET /ready` (Redis ping)
- **URL:** dạng `https://lab6-ai-agent.onrender.com`

---

## Bước 5 — Test public API

Thay `YOUR_URL` và `YOUR_API_KEY`:

```bash
export URL=https://lab6-ai-agent.onrender.com
export API_KEY=<AGENT_API_KEY từ Render Dashboard>

curl "$URL/health"
curl "$URL/ready"

curl -X POST "$URL/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"question":"Hello","user_id":"user1"}'

# Expected: 401
curl -X POST "$URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello","user_id":"user1"}'
```

**Response mẫu (200):**

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

---

## Environment variables (render.yaml)

| Variable | Nguồn | Mô tả |
|----------|-------|-------|
| `REDIS_URL` | Auto từ `lab6-redis` | Internal Redis URL |
| `AGENT_API_KEY` | Auto-generate | API key cho `/ask` |
| `ENVIRONMENT` | `production` | |
| `RATE_LIMIT_PER_MINUTE` | `10` | |
| `MONTHLY_BUDGET_USD` | `10` | |
| `OPENAI_API_KEY` | Set thủ công | Optional |

---

## Troubleshooting

### `Connection refused` to `localhost:6379` (phổ biến nhất)

Log:
```
Could not connect to Redis at 'redis://localhost:6379/0'
Error 111 connecting to localhost:6379. Connection refused.
```

**Nguyên nhân:** Web service **không có** `REDIS_URL` từ Render Key Value — app fallback về localhost.

**Fix nhanh (Render Dashboard):**

1. Kiểm tra có service **lab6-redis** (Key Value) chưa
   - Nếu chưa có → tạo lại bằng **Blueprint** (`06-lab-complete/render.yaml`)
2. Vào **lab6-redis** → tab **Connect** → copy **Internal Redis URL**  
   (dạng `redis://red-xxxxxxxx:6379`)
3. Vào **lab6-ai-agent** → **Environment**
4. Set / sửa `REDIS_URL` = Internal URL vừa copy
5. **Xóa** mọi giá trị `redis://localhost:6379/0` hoặc `redis://redis:6379/0`
6. **Manual Deploy** → Deploy latest commit

### Startup failed — hostname `redis` not known

```
Error -2 connecting to redis:6379. Name or service not known
```

**Nguyên nhân:** `REDIS_URL=redis://redis:6379/0` (chỉ dùng được trong Docker Compose local).

**Fix:** Dùng Internal URL từ **lab6-redis**, không dùng hostname `redis`.

### Deploy failed — port binding

App phải listen `$PORT` do Render inject. Dockerfile đã dùng:

```dockerfile
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Health check failed

Render check `/ready` — cần Redis connected. Xem Logs nếu Key Value chưa provision xong; redeploy sau khi `lab6-redis` status **Available**.

### Cold start (Free/Starter)

Free tier web service sleep sau idle — request đầu có thể chậm 30–60s.

---

## Cập nhật sau deploy

Ghi public URL vào:
- `PROJECT_ASSIGNMENT.md` → Public API URL
- `Solution.md` → DEPLOYMENT section
- `DEPLOYMENT.md` (repo root nếu có)

**Public API URL:** TODO — cập nhật sau khi deploy thành công

---

## Redeploy

Push lên `main` → auto-deploy (nếu `autoDeploy: true`).

Hoặc Dashboard → **Manual Deploy** → **Deploy latest commit**.
