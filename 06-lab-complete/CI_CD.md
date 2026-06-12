# Lab 6 — CI/CD Guide

Pipeline tự động cho `06-lab-complete/` dùng **GitHub Actions**.

## Tổng quan

| Workflow | File | Khi nào chạy | Mục đích |
|----------|------|--------------|----------|
| **CI** | `.github/workflows/lab6-ci.yml` | Push/PR vào `main` (paths `06-lab-complete/**`) | Verify code trước merge |
| **CD** | `.github/workflows/lab6-deploy-railway.yml` | Push `main` hoặc `workflow_dispatch` | Deploy lên Railway |

```
┌─────────────┐     push/PR      ┌──────────────────────────────────┐
│   Developer │ ───────────────► │  lab6-ci.yml                     │
└─────────────┘                  │  1. check_production_ready.py    │
                                 │  2. ruff lint                    │
                                 │  3. pytest                       │
                                 │  4. docker build                 │
                                 └──────────────────────────────────┘

┌─────────────┐     merge main   ┌──────────────────────────────────┐
│   main      │ ───────────────► │  lab6-deploy-railway.yml         │
└─────────────┘                  │  railway up --detach             │
                                 └──────────────────────────────────┘
```

## CI — Stages

### 1. Production readiness

```bash
cd 06-lab-complete
python check_production_ready.py
```

Kiểm tra Dockerfile, compose, security, endpoints trong code.

### 2. Lint (Ruff)

```bash
ruff check app/ tests/ check_production_ready.py
```

### 3. Unit tests (pytest)

```bash
pip install -r requirements.txt pytest httpx
AGENT_API_KEY=test-ci-key pytest tests/ -v
```

Tests: `/health`, `/ready`, `/ask` auth (401/200), validation.

### 4. Docker build

```bash
docker build -t lab6-agent:ci .
```

Verify multi-stage Dockerfile build thành công trên CI runner.

## CD — Deploy Railway

### Bước 1: Tạo project Railway (một lần)

```bash
npm i -g @railway/cli
cd 06-lab-complete
railway login
railway init
railway variables set AGENT_API_KEY=your-production-key
railway variables set ENVIRONMENT=production
railway variables set JWT_SECRET=your-jwt-secret
```

### Bước 2: Thêm GitHub Secrets

Vào **GitHub repo → Settings → Secrets and variables → Actions**:

| Secret | Mô tả |
|--------|-------|
| `RAILWAY_TOKEN` | Token từ [Railway Account Settings](https://railway.com/account/tokens) |
| `RAILWAY_PROJECT_ID` | (Optional) Project ID nếu chưa link sẵn |

### Bước 3: Trigger deploy

**Tự động:** push lên `main` khi có thay đổi trong `06-lab-complete/`

**Thủ công:** GitHub → Actions → **Lab 6 Deploy Railway** → **Run workflow**

### Bước 4: Verify sau deploy

```bash
curl https://<your-app>.up.railway.app/health
curl -X POST https://<your-app>.up.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"CI/CD works?"}'
```

## Chạy CI local (trước khi push)

```bash
cd 06-lab-complete

python check_production_ready.py
pip install ruff pytest httpx
pip install -r requirements.txt
ruff check app/ tests/
AGENT_API_KEY=test-ci-key pytest tests/ -v
docker build -t lab6-agent:local .
```

## Render (alternative CD)

Render hỗ trợ **auto-deploy từ GitHub** qua `render.yaml` — không cần GitHub Actions CD:

1. Push repo lên GitHub
2. Render Dashboard → New → Blueprint
3. Connect repo → Render đọc `06-lab-complete/render.yaml`

## Troubleshooting

| Lỗi | Cách xử lý |
|-----|------------|
| CI fail `check_production_ready` | Chạy script local, sửa các mục ❌ |
| CI fail pytest | `cd 06-lab-complete && pytest tests/ -v` |
| Deploy fail thiếu token | Thêm `RAILWAY_TOKEN` vào GitHub Secrets |
| Deploy fail link project | Thêm `RAILWAY_PROJECT_ID` hoặc chạy `railway init` local trước |
| Docker build fail | `docker build .` trong `06-lab-complete/` |

## Files liên quan

```
.github/workflows/lab6-ci.yml
.github/workflows/lab6-deploy-railway.yml
06-lab-complete/tests/test_main.py
06-lab-complete/check_production_ready.py
06-lab-complete/railway.toml
06-lab-complete/Dockerfile
```
