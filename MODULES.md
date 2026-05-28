# Smart Home — Module Progress

## Cấu trúc dự án

```
smarthome-backend/
├── backend/          ← FastAPI API (Python)
│   ├── app/          ← Source code chính
│   ├── firmware/     ← OTA binary files
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         ← React + Vite SPA
│   └── src/
├── mobile/           ← Flutter Mobile App
│   └── lib/
├── mosquitto/        ← MQTT Broker config
│   └── config/
├── devops/           ← Production deploy
│   ├── nginx/
│   │   └── nginx.conf
│   ├── docker-compose.prod.yml
│   └── .env.example
├── docker-compose.yml  ← Dev local
└── .gitignore
```

---

## Backend (B) — FastAPI

| Module | Mô tả | Trạng thái |
|--------|-------|-----------|
| B1 | Setup FastAPI + PostgreSQL + Redis + Mosquitto (Docker Compose local) | ✅ 2026-05-25 |
| B2 | Auth: register (email/SĐT), login, JWT HttpOnly cookie, admin role | ✅ 2026-05-25 |
| B3 | Device API: list, detail, command, DP state, history | ✅ 2026-05-25 |
| B4 | Admin API: quản lý user, gán device | ✅ 2026-05-25 |
| B5 | Schedule API: automation theo giờ/ngày + background runner | ✅ 2026-05-25 |
| B6 | OTA firmware: upload + trigger update qua MQTT | ⬜ Chưa làm |

---

## Frontend (F) — React + Vite

| Module | Mô tả | Trạng thái |
|--------|-------|-----------|
| F1 | Dashboard: danh sách device, realtime WebSocket, nhóm theo phòng | ✅ 2026-05-25 |
| F2 | Device Detail: DP states, toggle, history chart | ✅ 2026-05-25 |
| F3 | Auth: Login, register với email/SĐT, JWT cookie | ✅ 2026-05-25 |
| F4 | Admin Panel: quản lý user, gán device | ✅ 2026-05-25 |
| F5 | Schedule Panel: tạo/sửa/xóa automation | ✅ 2026-05-25 |
| F6 | Notification Panel | ⬜ Chưa làm |

---

## Mobile (M) — Flutter

| Module | Mô tả | Trạng thái |
|--------|-------|-----------|
| M1 | Login screen + AuthProvider + Splash | ✅ 2026-05-27 |
| M2 | Dashboard: danh sách device, realtime WS, nhóm theo phòng | ✅ 2026-05-27 |
| M3 | Device Detail: DP toggle, history chart (fl_chart) | ✅ 2026-05-27 |
| M4 | Schedule screen | ⬜ Chưa làm |
| M5 | Admin screen | ⬜ Chưa làm |
| M6 | Push notification (FCM) | ⬜ Chưa làm |
| M7 | Build APK production + publish | ⬜ Chưa làm |

---

## Deploy (D) — VPS

| Module | Mô tả | Trạng thái |
|--------|-------|-----------|
| D1 | VPS setup: Docker, UFW, user admin | ✅ 2026-05-28 |
| D2 | Docker Compose prod: postgres, redis, mosquitto, backend, nginx | ✅ 2026-05-28 |
| D3 | Domain + HTTPS: Cloudflare DNS → VPS, Nginx SSL | 🔄 Đang làm |
| D4 | Frontend build trong Dockerfile (multi-stage, React → static) | ⬜ Chưa làm |
| D5 | CI/CD: GitHub Actions auto-deploy khi push main | ⬜ Chưa làm |
| D6 | Flutter production build kết nối production URL | ⬜ Chưa làm |

---

## Firmware (FW) — ESP32-C3 Rust

| Module | Mô tả | Trạng thái |
|--------|-------|-----------|
| FW1 | SoftAP provisioning, GPIO (button, relay, LED) | ✅ 2026-05-24 |
| FW2 | HTTP REST API local control | ✅ 2026-05-24 |
| FW3 | MQTT remote control + LWT online/offline | ✅ 2026-05-24 |
| FW4 | OTA firmware update qua MQTT | ⬜ Chưa làm |

---

## VPS Info

- **IP:** 160.187.1.239
- **OS:** Ubuntu 20.04 LTS
- **SSH:** `ssh vps` (WSL config: Host vps → 160.187.1.239, User admin)
- **Repo trên VPS:** `~/SmartHome/smarthome-backend/`
- **Health check:** `http://160.187.1.239/health`

## Deploy commands (VPS)

```bash
# Connect
ssh vps

# Update code
cd ~/SmartHome/smarthome-backend
git pull

# Restart prod
cd devops
docker compose -f docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker-compose.prod.yml logs -f backend
```
