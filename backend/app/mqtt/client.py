"""
MQTT client chạy background — subscribe tất cả topic smarthome/#
Khi nhận message:
  - smarthome/{device_id}/state  → lưu DB + push WebSocket
  - smarthome/{device_id}/lwt    → đánh dấu offline
  - smarthome/{device_id}/online → đánh dấu online
"""
import asyncio
import json
import logging
from datetime import datetime

import aiomqtt
import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.device import Device, DpState, DpHistory

log = logging.getLogger(__name__)

TOPIC_PREFIX = "smarthome"


async def _get_or_none(session, device_id: str) -> Device | None:
    result = await session.execute(select(Device).where(Device.device_id == device_id))
    return result.scalar_one_or_none()


async def handle_state(device_id: str, payload: str, redis: aioredis.Redis) -> None:
    """Xử lý message state từ device: lưu DB và push WebSocket qua Redis pub/sub"""
    try:
        data = json.loads(payload)
        dp_id = int(data["dp_id"])
        value = data["value"]
    except (json.JSONDecodeError, KeyError, ValueError):
        log.warning("[MQTT] Invalid state payload from %s: %s", device_id, payload)
        return

    async with AsyncSessionLocal() as db:
        device = await _get_or_none(db, device_id)
        if not device:
            log.warning("[MQTT] Unknown device: %s", device_id)
            return

        # Upsert DpState
        stmt = insert(DpState).values(
            device_id=device.id, dp_id=dp_id,
            value={"v": value}, updated_at=datetime.utcnow()
        ).on_conflict_do_update(
            index_elements=["device_id", "dp_id"],
            set_={"value": {"v": value}, "updated_at": datetime.utcnow()},
        )
        await db.execute(stmt)

        # Append history
        db.add(DpHistory(device_id=device.id, dp_id=dp_id, value={"v": value}))

        # Update last_seen
        device.last_seen = datetime.utcnow()
        device.is_online = True
        await db.commit()

    # Push real-time update tới WebSocket clients qua Redis
    event = json.dumps({"type": "state", "device_id": device_id, "dp_id": dp_id, "value": value})
    await redis.publish(f"ws:{device_id}", event)
    log.debug("[MQTT] State saved: %s dp%d = %s", device_id, dp_id, value)


async def handle_online(device_id: str, online: bool, redis: aioredis.Redis) -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(is_online=online, last_seen=datetime.utcnow())
        )
        await db.commit()

    event = json.dumps({"type": "online", "device_id": device_id, "online": online})
    await redis.publish(f"ws:{device_id}", event)
    log.info("[MQTT] Device %s → %s", device_id, "online" if online else "offline")


async def mqtt_loop(redis: aioredis.Redis) -> None:
    """Vòng lặp MQTT chính — tự reconnect khi mất kết nối"""
    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.mqtt_host,
                port=settings.mqtt_port,
                username=settings.mqtt_username,
                password=settings.mqtt_password,
            ) as client:
                log.info("[MQTT] Connected to broker %s:%d", settings.mqtt_host, settings.mqtt_port)
                await client.subscribe(f"{TOPIC_PREFIX}/#")

                async for message in client.messages:
                    topic = str(message.topic)
                    payload = message.payload.decode(errors="replace")
                    parts = topic.split("/")

                    # smarthome/{device_id}/state|online|lwt
                    if len(parts) != 3 or parts[0] != TOPIC_PREFIX:
                        continue

                    device_id, event_type = parts[1], parts[2]

                    if event_type == "state":
                        await handle_state(device_id, payload, redis)
                    elif event_type == "online":
                        await handle_online(device_id, True, redis)
                    elif event_type == "lwt":
                        await handle_online(device_id, False, redis)

        except aiomqtt.MqttError as e:
            log.error("[MQTT] Connection error: %s — retry in 5s", e)
            await asyncio.sleep(5)


async def publish_command(device_id: str, dp_id: int, value) -> None:
    """Gửi lệnh xuống device qua MQTT"""
    payload = json.dumps({"dp_id": dp_id, "value": value})
    async with aiomqtt.Client(
        hostname=settings.mqtt_host,
        port=settings.mqtt_port,
        username=settings.mqtt_username,
        password=settings.mqtt_password,
    ) as client:
        await client.publish(f"{TOPIC_PREFIX}/{device_id}/cmd", payload, qos=1)
    log.info("[MQTT] Command → %s dp%d = %s", device_id, dp_id, value)
