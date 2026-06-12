# Solution.md — Day 12 Lab Submission

> **AICB-P1 · VinUniversity 2026 — Infrastructure & Deployment**  
> Tài liệu tổng hợp đáp án Lab 1–5, căn theo [DAY12_DELIVERY_CHECKLIST.md](DAY12_DELIVERY_CHECKLIST.md).  
> Kết quả có bằng chứng thực tế ghi **PASS**; phần chưa chạy ghi **TODO**.

---

## Thông tin nộp bài

| Trường | Giá trị |
|--------|---------|
| **Student Name** | TODO: Need evidence |
| **Student ID** | TODO: Need evidence |
| **Date** | TODO: Need evidence |
| **Repository URL** | TODO: Need evidence |

---

## Submission Requirements

---

### 1. Mission Answers (40 points) — Lab 1 đến Lab 5

> Cấu trúc theo mẫu `MISSION_ANSWERS.md` trong [DAY12_DELIVERY_CHECKLIST.md](DAY12_DELIVERY_CHECKLIST.md).

---

#### Tổng quan lab

**Mục tiêu toàn bộ Infrastructure & Deployment**

- Hiểu khoảng cách **dev vs production** và nguyên tắc **12-Factor App**
- **Containerize** agent (Docker single-stage → multi-stage → Compose)
- **Deploy** lên cloud (Railway)
- **Bảo vệ API** (API Key, JWT, rate limit, cost guard)
- **Scale & reliability** (health check, graceful shutdown, stateless, load balancing)

**Stack sử dụng**

| Thành phần | Công nghệ |
|------------|-----------|
| App framework | FastAPI + Uvicorn |
| LLM | Mock LLM (`utils/mock_llm.py`) |
| Container | Docker, Docker Compose |
| Reverse proxy / LB | Nginx |
| Session / cache | Redis |
| Cloud (Lab 3) | Railway + Nixpacks + `railway.toml` |
| Auth | API Key (Lab 4 develop), JWT + PyJWT (Lab 4 production) |

**Khái niệm chính**

1. Config từ environment — không hardcode secrets  
2. Liveness (`/health`) vs readiness (`/ready`)  
3. Graceful shutdown  
4. Docker layer cache — copy `requirements.txt` trước source  
5. Multi-stage build — image nhỏ hơn, an toàn hơn  
6. Infrastructure as Code — `docker-compose.yml`, `railway.toml`  
7. API Gateway — auth → rate limit → cost guard  
8. Stateless design — state trong Redis  
9. Load balancing — Nginx round-robin  

---

## Part 1: Localhost vs Production

### Mục tiêu lab

- Hiểu vì sao *"it works on my machine"* là vấn đề  
- Nhận ra khác biệt dev vs production environment  
- Áp dụng 12-factor cơ bản: config từ env, secrets ngoài code, health check, graceful shutdown  

### File / folder quan trọng

| Path | Vai trò |
|------|---------|
| `01-localhost-vs-production/develop/app.py` | Anti-patterns — agent kiểu localhost |
| `01-localhost-vs-production/production/app.py` | 12-factor compliant agent |
| `01-localhost-vs-production/production/config.py` | Centralized config từ env vars |
| `01-localhost-vs-production/production/.env.example` | Template env |
| `utils/mock_llm.py` | Mock LLM dùng chung |

### Exercise 1.1: Anti-patterns found

1. API key và `DATABASE_URL` **hardcode** trong code (`develop/app.py`)  
2. Không có **config management** — `DEBUG=True`, port cứng  
3. Dùng **`print()`** thay logging — log cả API key ra terminal  
4. **Không có** `/health` — platform không biết khi nào restart  
5. Bind **`localhost`**, port **8000** cứng, **`reload=True`** — không phù hợp production/cloud  

### Exercise 1.2: Chạy develop + test

**Commands**

```bash
cd 01-localhost-vs-production/develop
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/ask?question=hello"
```

**Command output (evidence)**

| Test | HTTP | Output chính | Kết quả |
|------|------|--------------|---------|
| `GET /` | 200 | `{"message":"Hello! Agent is running on my machine :)"}` | PASS |
| `GET /health` | 404 | `{"detail":"Not Found"}` | PASS (đúng anti-pattern) |
| `POST /ask?question=hello` | 200 | mock answer | PASS |
| Log terminal | — | `[DEBUG] Using key: sk-hardcoded-fake-key-never-do-this` | PASS |

**Production commands**

```bash
cd 01-localhost-vs-production/production
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
python app.py
```

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"hello"}'
```

**Command output (evidence)**

| Test | HTTP | Output chính | Kết quả |
|------|------|--------------|---------|
| `GET /health` | 200 | `status: ok`, uptime | PASS |
| `GET /ready` | 200 | `ready: true` | PASS |
| `POST /ask` JSON | 200 | answer + model metadata | PASS |
| Log | — | Không in API key | PASS |

> **Lưu ý:** macOS Homebrew cần `venv` (PEP 668).

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode trong code | `config.py` + env vars | Đổi config không cần sửa code; secrets không vào git |
| Secrets | `sk-hardcoded-fake-key...` | `os.getenv("OPENAI_API_KEY")` | Tránh lộ key khi push public repo |
| Host / Port | `localhost:8000` cứng | `0.0.0.0` + `PORT` env | Cloud inject PORT; container nhận traffic bên ngoài |
| Health check | Không có | `/health`, `/ready`, `/metrics` | Platform biết restart / route traffic |
| Logging | `print()` + log secret | JSON structured | An toàn + parse được trong log aggregator |
| Shutdown | Đột ngột | Lifespan + SIGTERM graceful | Không cắt request đang xử lý |
| API `/ask` | Query param | JSON body | Contract rõ ràng cho client production |

**Screenshots**

- TODO: Need screenshot — develop log lộ API key  
- TODO: Need screenshot — production `/health` response  

### Bài học rút ra (Part 1)

1. Code chạy local ≠ sẵn sàng deploy cloud  
2. Hardcode secrets nguy hiểm cả trong code lẫn log  
3. Platform inject `PORT`; cần bind `0.0.0.0`  
4. `/health` bắt buộc cho orchestrator  

---

## Part 2: Docker

### Mục tiêu lab

- Hiểu container và tại sao cần nó  
- Dockerfile single-stage vs multi-stage  
- Docker Compose multi-service stack  
- Tối ưu image size (< 500 MB)  

### Exercise 2.1: Dockerfile questions

| Câu hỏi | Develop | Production |
|---------|---------|------------|
| Base image | `python:3.11` (~1 GB) | `python:3.11-slim` (builder + runtime) |
| Working directory | `/app` | `/app` |
| Tại sao COPY `requirements.txt` trước? | Tận dụng Docker layer cache — deps ít đổi hơn code | Giống develop |
| CMD | `python app.py` | `uvicorn main:app --host 0.0.0.0 --workers 2` |
| Build context | **Project root** | **Project root** |

**Paths**

- `02-docker/develop/Dockerfile` — single-stage  
- `02-docker/production/Dockerfile` — multi-stage, non-root `appuser`, HEALTHCHECK  
- `02-docker/production/docker-compose.yml` — agent + redis + qdrant + nginx  

### Exercise 2.2: Build và run

**Develop**

```bash
cd <project-root>
docker build -f 02-docker/develop/Dockerfile -t agent-develop .
docker images agent-develop
docker run --rm -d --name agent-develop-test -p 8000:8000 agent-develop
```

**Command output (evidence)**

```
agent-develop:latest  1.67GB
GET /        → 200  {"message":"Agent is running in a Docker container!"}
GET /health  → 200  {"status":"ok","container":true}
POST /ask?question=What%20is%20Docker? → 200  mock answer về Docker
```

**Production stack**

```bash
docker compose -f 02-docker/production/docker-compose.yml up -d --build
docker compose -f 02-docker/production/docker-compose.yml ps
docker compose -f 02-docker/production/docker-compose.yml down
```

**Command output (evidence)**

| Test | Kết quả |
|------|---------|
| Build `production-agent` | PASS — **262 MB** |
| Nginx `GET /health` | PASS — HTTP 200 |
| Nginx `POST /ask` JSON | PASS |
| Agent trực tiếp `:8000` | PASS — không kết nối (đúng thiết kế) |
| Compose auto-start | PARTIAL — qdrant unhealthy; start agent/nginx thủ công vẫn test được |

> **Setup khi chạy:** sửa `build.context: ../..`, thêm `requirements.txt`, `.env.local`.

### Exercise 2.3: Image size comparison

| Image | Size | Ghi chú |
|-------|------|---------|
| Develop (`agent-develop`) | **1.67 GB** | `python:3.11` full, single-stage |
| Production (`production-agent`) | **262 MB** | multi-stage + slim |
| Difference | **~84% nhỏ hơn** | (1.67 − 0.262) / 1.67 ≈ 84% |

### Vai trò nginx (production compose)

- Cổng duy nhất ra host: port **80**  
- Reverse proxy → `agent:8000`  
- Rate limiting 10 req/s/IP; `/health` không bị limit  
- Agent không expose port trực tiếp  

**Endpoint test**

```bash
curl http://localhost:8000/health          # develop container
curl http://localhost/health               # production qua nginx
curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Explain microservices"}'
```

**Screenshots**

- TODO: Need screenshot — `docker images` size comparison  
- TODO: Need screenshot — nginx health qua port 80  

### Bài học rút ra (Part 2)

1. Multi-stage: **1.67 GB → 262 MB**  
2. Build context phải khớp COPY paths  
3. Healthcheck sai có thể chặn cả Compose stack  
4. Client gọi qua nginx, không gọi thẳng backend  

---

## Part 3: Cloud Deployment

### Mục tiêu lab (Railway)

- Deploy agent lên cloud — public URL 24/7  
- Railway inject `PORT` tự động  
- Config qua `railway.toml`  
- Secrets qua dashboard/CLI  

### App chính Railway

**Path:** `03-cloud-deployment/railway/app.py`

- FastAPI; đọc `PORT`, bind `0.0.0.0`  
- Endpoints: `GET /`, `POST /ask` (JSON), `GET /health`  

### requirements.txt

**Path:** `03-cloud-deployment/railway/requirements.txt`

```text
fastapi==0.115.0
uvicorn[standard]==0.30.0
```

### railway.toml

| Cấu hình | Giá trị |
|----------|---------|
| Builder | NIXPACKS |
| Start command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Health check | `/health`, timeout 30s |
| Restart | ON_FAILURE, max 3 retries |

### Exercise 3.1: Railway deployment

**Command chạy local**

```bash
cd 03-cloud-deployment/railway
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PORT=8000 python app.py

curl http://localhost:8000/health
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"hello"}'
```

**Command output (local)**

- TODO: Need command output — chưa chạy local Railway app trong session lab  

**Các bước deploy Railway**

```bash
npm i -g @railway/cli
cd 03-cloud-deployment/railway
railway login
railway init
railway variables set AGENT_API_KEY=my-secret-key
railway up
railway domain
```

**Public URL**

- TODO: Need evidence — URL deploy thực tế chưa xác minh trong session lab  

**Test public URL**

```bash
curl https://<your-app>.up.railway.app/health
curl -X POST https://<your-app>.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Am I on the cloud?"}'
```

**Command output (cloud)**

- TODO: Need command output  

**Screenshots**

- TODO: Need screenshot — Railway dashboard  
- TODO: Need screenshot — public URL test  

### Bài học rút ra (Part 3)

1. Cloud inject `PORT` — app phải đọc từ env  
2. `/health` giúp Railway restart container unhealthy  
3. Secrets set qua CLI/dashboard — không hardcode  
4. Nixpacks deploy nhanh không cần Dockerfile  

---

## Part 4: API Security

### Mục tiêu lab

- Lớp bảo vệ trước agent trên public URL  
- API Key (develop)  
- JWT + rate limit + cost guard (production)  

### Develop app

**Path:** `04-api-gateway/develop/app.py`

- Auth: `X-API-Key` header  
- Env: `AGENT_API_KEY` (test: `my-secret-key`)  
- Protected: `POST /ask?question=` — Public: `/`, `/health`  

### Production app + modules

| File | Vai trò |
|------|---------|
| `production/app.py` | Full security stack, middleware headers |
| `production/auth.py` | JWT create/verify, demo users login |
| `production/rate_limiter.py` | Sliding window — user 10/min, admin 100/min |
| `production/cost_guard.py` | Budget $1/user/ngày, $10 global/ngày |

**auth.py** — tạo JWT (`create_token`), verify (`verify_token`), login (`authenticate_user`).

**rate_limiter.py** — sliding window; vượt limit → HTTP **429** + `X-RateLimit-*`.

**cost_guard.py** — `check_budget()` trước LLM; `record_usage()` sau; `GET /me/usage`.

### Exercise 4.1–4.3: Test results

**Develop — commands**

```bash
cd 04-api-gateway/develop
AGENT_API_KEY=my-secret-key python app.py

# Không key → 401
curl -X POST "http://localhost:8000/ask?question=hello"

# Key sai → 403
curl -X POST "http://localhost:8000/ask?question=hello" \
  -H "X-API-Key: wrong-key"

# Key đúng → 200
curl -X POST "http://localhost:8000/ask?question=hello" \
  -H "X-API-Key: my-secret-key"
```

**Develop — command output (evidence)**

| Case | HTTP | Output | Kết quả |
|------|------|--------|---------|
| Không API key | 401 | `Missing API key...` | PASS |
| API key sai | 403 | `Invalid API key.` | PASS |
| API key đúng | 200 | mock answer | PASS |

**Production — commands**

```bash
cd 04-api-gateway/production
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py

curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"student","password":"demo123"}'
# TOKEN=<access_token>

curl -X POST http://localhost:8000/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"what is docker?"}'

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/me/usage
```

**Production — command output (evidence)**

| Case | HTTP | Output | Kết quả |
|------|------|--------|---------|
| Không JWT | 401 | `Authentication required...` | PASS |
| JWT sai | 403 | `Invalid token.` | PASS |
| JWT đúng | 200 | answer + `requests_remaining: 9` | PASS |
| `/me/usage` | 200 | `budget_remaining_usd: 0.999981` | PASS |
| Rate limit (req #10 loop) | 429 | `Rate limit exceeded` | PASS |

> **Fix khi chạy:** `response.headers.pop("server")` → `del response.headers["server"]` (tránh 500).  
> **Python:** dùng 3.12 — pydantic fail trên 3.14.

**Screenshots**

- TODO: Need screenshot — 401 / 403 / 429 responses  

### Exercise 4.4: Cost guard implementation

**Approach (code hiện có trong `cost_guard.py`)**

- In-memory demo (production thật nên dùng Redis/DB)  
- `check_budget(user_id)` trước gọi LLM — vượt → **402** (user) hoặc **503** (global)  
- `record_usage()` sau LLM — mock token count từ word length  
- `GET /me/usage` — xem cost/budget còn lại  

**Test 402 (hết budget)**

- TODO: Need command output — chưa ép hết $1 budget trong session  

### Bài học rút ra (Part 4)

1. Public API cần auth trước LLM  
2. 401 (thiếu) vs 403 (sai)  
3. JWT cho multi-user; API Key cho MVP  
4. Rate limit + cost guard là lớp bảo vệ thứ 2, 3  
5. Middleware bug có thể làm toàn API 500  

---

## Part 5: Scaling & Reliability

### Mục tiêu lab

- Health check + graceful shutdown (develop)  
- Stateless + Redis + scale + Nginx LB (production)  

### Exercise 5.1: Health checks (develop)

**Commands**

```bash
cd 05-scaling-reliability/develop
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py

curl http://localhost:8000/health
curl http://localhost:8000/ready
curl -X POST "http://localhost:8000/ask?question=hello"
```

**Command output (evidence)**

| Endpoint | HTTP | Output chính | Kết quả |
|----------|------|--------------|---------|
| `GET /health` | 200 | `status: ok`, memory check 80.8% | PASS |
| `GET /ready` | 200 | `ready: true` | PASS |
| `POST /ask` | 200 | mock answer | PASS |

### Exercise 5.2: Graceful shutdown

**Command**

```bash
kill -SIGTERM <pid>
```

**Command output**

- TODO: Need command output — log graceful shutdown chưa capture trong session  

### Exercise 5.3: Stateless design (production)

**Stateless app** — session/conversation lưu **Redis** (`session:{session_id}`), không lưu trong RAM container.

**Vì sao cần nhiều instance** — throughput, failover; LB gửi request ngẫu nhiên tới replica.

**Paths:** `05-scaling-reliability/production/app.py`, `docker-compose.yml`, `nginx.conf`

### Exercise 5.4: Load balancing

**docker-compose scale**

```bash
cd 05-scaling-reliability/production
docker compose up --build --scale agent=3 -d
docker compose ps
```

**Command output (evidence)**

```
production-agent-1/2/3   Up (healthy)
production-redis-1         Up (healthy)
production-nginx-1         0.0.0.0:8080->80/tcp
```

**nginx load balancing** (`nginx.conf`)

```nginx
upstream agent_cluster {
    server agent:8000;
    keepalive 16;
}
add_header X-Served-By $upstream_addr always;
proxy_next_upstream error timeout http_503;
```

**Endpoint test qua LB**

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Docker?"}'
```

> Port **8080** (không phải 80): `8080:80` trong compose.

**Command output (evidence)**

| Test | Kết quả |
|------|---------|
| `GET /health` | PASS — `redis_connected: true`, header `X-Served-By` |
| `POST /chat` | PASS — `served_by: instance-...`, `storage: redis` |

> **Setup khi chạy:** thêm `Dockerfile`, `requirements.txt`, `.env.local`; sửa path `advanced/` → `production/`.

### Exercise 5.5: Test stateless

**Command**

```bash
cd 05-scaling-reliability/production
python3 test_stateless.py
```

**Command output (evidence)**

```text
Instances used: {'instance-b50990', 'instance-6f3ec7', 'instance-1edae9'}
Total messages: 10
✅ Session history preserved across all instances via Redis!
```

**test_stateless.py kiểm tra**

1. 5 request `POST /chat` cùng `session_id`  
2. `served_by` khác nhau → LB + stateless  
3. `GET /chat/{session_id}/history` → 10 messages còn nguyên  

**Screenshots**

- TODO: Need screenshot — `docker compose ps` 3 agents  
- TODO: Need screenshot — `test_stateless.py` output  

### Bài học rút ra (Part 5)

1. Liveness vs readiness khác mục đích  
2. Scale bắt buộc stateless — Redis shared state  
3. `served_by` + `X-Served-By` chứng minh LB  
4. Đọc compose để biết đúng port (8080 vs 80)  

---

### 2. Full Source Code — Lab 06 Complete (60 points)

**Yêu cầu theo checklist:** production-ready agent trong `06-lab-complete/` với Dockerfile, compose, auth, rate limit, cost guard, health, stateless Redis, Nginx LB.

| Hạng mục | Trạng thái |
|----------|------------|
| Lab 06 source hoàn chỉnh | ✅ PASS — modular `app/` (9 modules) + `PROJECT_ASSIGNMENT.md` |
| Docker Compose (agent+redis+nginx) | ✅ PASS — `--scale agent=3` |
| Image < 500 MB | ✅ PASS — `06-lab-complete-agent` **272 MB** |
| `check_production_ready.py` | ✅ PASS — **36/36 (100%)** |
| pytest | ✅ PASS — **7/7** |
| CI pipeline (GitHub Actions) | ✅ cấu hình xong — TODO: screenshot Actions sau push |
| Public deploy Lab 06 | TODO: Need evidence (URL + curl cloud) |

#### Cấu trúc code (Final Project)

```
06-lab-complete/
├── app/
│   ├── main.py, config.py, auth.py
│   ├── rate_limiter.py, cost_guard.py
│   ├── schemas.py, redis_client.py, agent.py
│   └── logging_config.py
├── nginx/nginx.conf
├── Dockerfile, docker-compose.yml
├── PROJECT_ASSIGNMENT.md, README.md
└── check_production_ready.py
```

#### Chạy và test (evidence)

```bash
cd 06-lab-complete
docker compose up --build --scale agent=3 -d
python check_production_ready.py   # 36/36 PASS
AGENT_API_KEY=test-ci-key pytest tests/ -v   # 7/7 PASS
```

**docker compose ps**

```text
06-lab-complete-agent-1/2/3   Up (healthy)
06-lab-complete-redis-1       Up (healthy)
06-lab-complete-nginx-1       0.0.0.0:80->80/tcp
```

**curl /health**

```json
{"status":"ok","environment":"production","storage":"redis","uptime_seconds":13.5}
```

**curl /ready**

```json
{"ready":true,"redis":"ok","instance_id":"instance-3d1772"}
```

**curl POST /ask (X-API-Key: secret)**

```json
{
  "answer": "Đây là câu trả lời từ AI agent (mock)...",
  "user_id": "user1",
  "conversation_length": 1,
  "metadata": {"environment": "production", "model": "mock-agent", "cost_usd": 0.001}
}
```

**curl POST /ask (no API key) → HTTP 401**

```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```

**Conversation history (Redis `conversation:{user_id}`)**

- Request 2 cùng `user_id=user1` → `conversation_length: 2` ✅ PASS

#### Production features implemented

| # | Requirement | Implementation |
|---|-------------|----------------|
| 1 | REST API `/ask` | `app/agent.py` + mock LLM |
| 2 | Conversation history | Redis key `conversation:{user_id}` |
| 3 | Multi-stage Docker | `Dockerfile` builder + runtime |
| 4 | Env config | `app/config.py` |
| 5 | API key auth | `app/auth.py` → 401 |
| 6 | Rate limit 10/min | `app/rate_limiter.py` → 429 |
| 7 | Cost guard $10/month | `app/cost_guard.py` → 402 |
| 8 | `/health` | Liveness in `main.py` |
| 9 | `/ready` | Redis ping in `main.py` |
| 10 | Graceful shutdown | SIGTERM handler + uvicorn timeout |
| 11 | Stateless + Redis | `app/redis_client.py` |
| 12 | JSON logging | `app/logging_config.py` |
| 13 | Compose stack | agent + redis + nginx |
| 14 | Scale agent=3 | docker compose `--scale agent=3` |

#### CI/CD — Lab 06

| Workflow | File | Trigger |
|----------|------|---------|
| CI | `.github/workflows/lab6-ci.yml` | push/PR `main` |
| CD | `.github/workflows/lab6-deploy-railway.yml` | push `main` / manual |

Chi tiết: [`06-lab-complete/CI_CD.md`](06-lab-complete/CI_CD.md), [`06-lab-complete/PROJECT_ASSIGNMENT.md`](06-lab-complete/PROJECT_ASSIGNMENT.md)

**Screenshots**

- TODO: Need screenshot — GitHub Actions `Lab 6 CI` green  
- TODO: Need screenshot — Railway deploy + public URL  

---

### 3. Service Domain Link — DEPLOYMENT.md

**Public URL**

- TODO: Need evidence  

**Platform**

- Railway (Lab 3)

**Test commands (cloud)**

```bash
curl https://your-agent.railway.app/health

curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

**Environment variables set**

| Variable | Set? |
|----------|------|
| `PORT` | TODO: Need evidence |
| `REDIS_URL` | TODO: Need evidence (Lab 06) |
| `AGENT_API_KEY` | TODO: Need evidence |
| `LOG_LEVEL` | TODO: Need evidence |

**Screenshots**

- TODO: Need screenshot — `screenshots/dashboard.png`  
- TODO: Need screenshot — `screenshots/running.png`  
- TODO: Need screenshot — `screenshots/test.png`  

---

## Pre-Submission Checklist

| # | Mục | Trạng thái |
|---|-----|------------|
| 1 | Repository public / instructor có access | TODO: Need evidence |
| 2 | `MISSION_ANSWERS.md` / `Solution.md` đủ exercises | ✅ Lab 1–5 (Lab 3 cloud TODO) |
| 3 | `DEPLOYMENT.md` có public URL hoạt động | TODO: Need evidence |
| 4 | Source Lab 06 trong `app/` | ✅ `06-lab-complete/app/` |
| 11 | CI/CD GitHub Actions | ✅ workflows + local verify PASS; Actions TODO sau push |
| 5 | `README.md` hướng dẫn setup | ✅ root README có |
| 6 | Không commit `.env` | ✅ (chỉ `.env.example` / `.env.local` local) |
| 7 | Không hardcode secrets (production paths) | ✅ (develop cố ý anti-pattern) |
| 8 | Public URL accessible | TODO: Need evidence |
| 9 | Screenshots trong `screenshots/` | TODO: Need screenshot |
| 10 | Commit history rõ ràng | TODO: Need evidence |

---

## Self-Test

> Theo [DAY12_DELIVERY_CHECKLIST.md](DAY12_DELIVERY_CHECKLIST.md) — áp dụng sau khi có public URL.

| # | Test | Local (Lab 1–5) | Cloud deploy |
|---|------|-----------------|--------------|
| 1 | `GET /health` → 200 | ✅ PASS (local) | TODO: Need command output |
| 2 | `/ask` không auth → 401 | ✅ PASS (Lab 4 develop) | TODO: Need command output |
| 3 | `/ask` có API key → 200 | ✅ PASS (Lab 4 develop) | TODO: Need command output |
| 4 | Rate limit → 429 | ✅ PASS (Lab 4 production JWT) | TODO: Need command output |

**Self-test script (cloud — khi đã deploy)**

```bash
curl https://your-app.railway.app/health

curl https://your-app.railway.app/ask
# Expected: 401

curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
  -X POST -H "Content-Type: application/json" \
  -d '{"user_id":"test","question":"Hello"}'
# Expected: 200

for i in {1..15}; do
  curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
    -X POST -H "Content-Type: application/json" \
    -d '{"user_id":"test","question":"test"}'
done
# Expected: eventually 429
```

---

## Lab Progress Summary

| Lab | Đã chạy local | Đã test endpoint | Hiểu production concept | Trạng thái |
|-----|---------------|------------------|---------------------------|------------|
| **Lab 1** | ✅ | ✅ | ✅ | **Hoàn thành** |
| **Lab 2** | ✅ | ✅ | ✅ | **Hoàn thành** (qdrant healthcheck PARTIAL) |
| **Lab 3** | ⬜ | ⬜ | ✅ đọc config | **TODO: Need evidence** (deploy cloud) |
| **Lab 4** | ✅ | ✅ | ✅ | **Hoàn thành** (402 budget TODO) |
| **Lab 5** | ✅ | ✅ | ✅ | **Hoàn thành** (SIGTERM log TODO) |
| **Lab 6** | ✅ compose x3 | ✅ curl + pytest | ✅ full stack | **Hoàn thành local** — cloud TODO |

---

## Phụ lục: Fix / setup đã áp dụng khi chạy thực tế

| Lab | Thay đổi | Lý do |
|-----|----------|-------|
| Lab 2 | `docker-compose.yml` build context; `requirements.txt`, `.env.local` | Repo thiếu file; context sai |
| Lab 4 | `production/app.py` middleware headers | Bug `MutableHeaders.pop()` → 500 |
| Lab 5 | `Dockerfile`, `requirements.txt`, `.env.local`; sửa compose path | Repo thiếu build files |
| Lab 6 | Full modular app, Redis state, nginx LB, compose scale=3 | Final Project Part 6 |

---

*Cập nhật: macOS, Python 3.12/3.14, Docker Desktop. Căn cấu trúc [DAY12_DELIVERY_CHECKLIST.md](DAY12_DELIVERY_CHECKLIST.md).*
