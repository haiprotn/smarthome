"""
WebSocket endpoints:
  ws://host/ws              — Global: nhận events của TẤT CẢ devices
  ws://host/ws/{device_id}  — Per-device: chỉ nhận events của 1 device
"""
import asyncio
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings

log = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_all(websocket: WebSocket):
    """Global WebSocket — nhận realtime events của TẤT CẢ devices."""
    await websocket.accept()
    log.info("[WS] Global client connected")

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.psubscribe("ws:*")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "pmessage":
                await websocket.send_text(message["data"])
            else:
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        log.info("[WS] Global client disconnected")
    finally:
        await pubsub.punsubscribe("ws:*")
        await redis.aclose()


@router.websocket("/ws/{device_id}")
async def websocket_device(websocket: WebSocket, device_id: str):
    """Per-device WebSocket — nhận events của 1 device cụ thể."""
    await websocket.accept()
    log.info("[WS] Client connected for device: %s", device_id)

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"ws:{device_id}")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                await websocket.send_text(message["data"])
            else:
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        log.info("[WS] Client disconnected: %s", device_id)
    finally:
        await pubsub.unsubscribe(f"ws:{device_id}")
        await redis.aclose()
