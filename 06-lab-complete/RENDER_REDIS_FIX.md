# Fix nhanh: REDIS_URL is not set (Render)

## ✅ Deploy ngay được (code mới nhất)

Sau khi **push code mới** và redeploy, app sẽ **khởi động được** ngay cả khi chưa có `REDIS_URL` (dùng in-memory tạm).

Kiểm tra:
```bash
curl https://<service>.onrender.com/ready
# {"ready":true,"redis":"memory","storage":"memory",...}
```

`"storage":"memory"` = chưa có Redis thật → cần làm bước dưới để đạt yêu cầu lab (stateless Redis).

---

## Bật Redis thật trên Render (khuyến nghị cho Lab 6)

Lỗi deploy cũ:
```
ValueError: REDIS_URL is not set on Render.
```

**Nguyên nhân:** Web service **chưa có** biến `REDIS_URL` trỏ tới Redis thật.

---

## Cách A — Link Redis trong Dashboard (nhanh nhất)

### Bước 1: Tạo Redis nếu chưa có

1. Render Dashboard → **New +** → **Redis** (hoặc **Key Value**)
2. Name: `lab6-redis`
3. Region: **Singapore** (cùng region với web service)
4. Plan: Free
5. **Create**

Đợi status **Available**.

### Bước 2: Link REDIS_URL vào web service

1. Mở service **lab6-ai-agent** → tab **Environment**
2. **Add Environment Variable**
3. Chọn **Link existing service** (hoặc biểu tượng link)
4. Service: **lab6-redis**
5. Property: **Connection String** (Internal)
6. Key name: **`REDIS_URL`**
7. **Save Changes**

### Bước 3: Redeploy

**Manual Deploy** → Deploy latest commit.

Logs thành công:
```json
{"event": "ready", "redis": "redis"}
```

---

## Cách B — Paste URL thủ công

1. **lab6-redis** → **Connect** → copy **Internal Redis URL**  
   Ví dụ: `redis://red-abc123xyz:6379`
2. **lab6-ai-agent** → **Environment** → Add:
   - Key: `REDIS_URL`
   - Value: paste URL vừa copy
3. Save → Manual Deploy

**Không dùng:**
- `redis://localhost:6379/0`
- `redis://redis:6379/0`

---

## Cách C — Deploy lại bằng Blueprint (khuyến nghị lâu dài)

Nếu bạn tạo web service thủ công (không qua Blueprint), `REDIS_URL` sẽ **không tự link**.

1. Push code mới nhất lên GitHub
2. Dashboard → **New +** → **Blueprint**
3. Chọn repo → Blueprint path: **`06-lab-complete/render.yaml`**
4. **Apply** — tạo đồng thời `lab6-redis` + `lab6-ai-agent`
5. Blueprint tự set `REDIS_URL` qua `fromService`

> Nếu đã có service cũ trùng tên, xóa hoặc đổi tên trước khi Apply Blueprint.

---

## Kiểm tra sau fix

Tab **Environment** của `lab6-ai-agent` phải có:

| Key | Value (ví dụ) |
|-----|----------------|
| `REDIS_URL` | `redis://red-xxxxx:6379` |
| `AGENT_API_KEY` | (auto-generated) |
| `ENVIRONMENT` | `production` |

Test:
```bash
curl https://<your-service>.onrender.com/ready
```

Expected với Redis thật: `{"ready":true,"redis":"ok","storage":"redis",...}`

---

## Cách D — Upstash Redis (free, dễ nhất nếu Render Redis khó tạo)

1. Đăng ký [upstash.com](https://upstash.com) → **Create Database** → Region gần Singapore
2. Copy **Redis URL** (dạng `rediss://default:xxx@xxx.upstash.io:6379`)
3. Render → **lab6-ai-agent** → **Environment** → Add:
   - Key: `REDIS_URL`
   - Value: paste Upstash URL
4. Save → **Manual Deploy**
5. `curl .../ready` → `"storage":"redis"`
