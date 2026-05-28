# Smart Home Backend — Giai đoạn 2

FastAPI + MQTT + WebSocket + PostgreSQL + Redis

## Stack

| Service    | Image / Framework         | Port |
|------------|--------------------------|------|
| Mosquitto  | eclipse-mosquitto:2.0    | 1883 |
| PostgreSQL | postgres:16-alpine       | 5432 |
| Redis      | redis:7-alpine           | 6379 |
| Backend    | FastAPI + uvicorn        | 8000 |

## Chạy local

```bash
# 1. Copy env
cp .env.example .env   # chỉnh password nếu cần

# 2. Build + start
docker compose up --build

# 3. API docs
open http://localhost:8000/docs
```

## MQTT Topics

| Topic | Chiều | Mô tả |
|-------|-------|-------|
| `smarthome/{device_id}/state` | Device → Backend | DP thay đổi: `{"dp_id":1,"value":true}` |
| `smarthome/{device_id}/cmd`   | Backend → Device | Lệnh điều khiển: `{"dp_id":1,"value":true}` |
| `smarthome/{device_id}/online`| Device → Backend | Device vừa boot |
| `smarthome/{device_id}/lwt`   | Device → Backend | Last Will (offline) |

## REST API

```bash
# Đăng ký device mới
curl -X POST http://localhost:8000/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_id":"a4cb8f20d6c8","product_id":"switch_1g","product_name":"Smart Switch 1 Gang"}'
# → trả về mqtt_password để nạp vào device

# Danh sách devices
curl http://localhost:8000/api/devices/

# Gửi lệnh xuống device
curl -X POST http://localhost:8000/api/devices/a4cb8f20d6c8/cmd \
  -H "Content-Type: application/json" \
  -d '{"dp_id":1,"value":true}'

# Lịch sử DP
curl "http://localhost:8000/api/devices/a4cb8f20d6c8/history?dp_id=1&limit=50"
```

## WebSocket

```js
const ws = new WebSocket("ws://localhost:8000/ws/a4cb8f20d6c8");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
// {"type":"state","device_id":"a4cb8f20d6c8","dp_id":1,"value":true}
// {"type":"online","device_id":"a4cb8f20d6c8","online":false}
```
