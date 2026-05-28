"""
REST API cho devices:
  POST   /api/devices/register          — Đăng ký device mới
  GET    /api/devices/                  — Danh sách tất cả devices
  GET    /api/devices/{device_id}       — Chi tiết + DP states hiện tại
  POST   /api/devices/{device_id}/cmd   — Gửi lệnh xuống device
  GET    /api/devices/{device_id}/history — Lịch sử DP (có phân trang)
  DELETE /api/devices/{device_id}       — Xóa device
"""
import base64
import hashlib
import os
import secrets
import subprocess
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.device import Device, DpState, DpHistory
from app.models.user import User
from app.mqtt.client import publish_command
from app.core.config import settings

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _device_filter(query, user: User):
    """Admin thấy tất cả, user thường chỉ thấy device của mình."""
    if not user.is_admin:
        query = query.where(Device.user_id == user.id)
    return query


# ─── Schemas ──────────────────────────────────────────────────────────────────

class DeviceRegister(BaseModel):
    device_id: str       # MAC address, e.g. "a4cb8f20d6c8"
    product_id: str      # "switch_1g"
    product_name: str    # "Smart Switch 1 Gang"


class CommandRequest(BaseModel):
    dp_id: int
    value: bool | int | str


class DeviceUpdate(BaseModel):
    friendly_name: str | None = None
    room: str | None = None
    user_id: int | None = None  # admin only: gán device cho user (0 = bỏ gán)


class DeviceOut(BaseModel):
    device_id: str
    product_id: str
    product_name: str
    friendly_name: str | None
    room: str | None
    is_online: bool
    last_seen: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class DpStateOut(BaseModel):
    dp_id: int
    value: bool | int | str
    updated_at: datetime


class DeviceDetailOut(DeviceOut):
    dp_states: list[DpStateOut]


class HistoryItem(BaseModel):
    dp_id: int
    value: bool | int | str
    timestamp: datetime


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _extract_value(row: DpState | DpHistory) -> bool | int | str:
    return row.value.get("v")


PASSWD_FILE = "/mosquitto/config/passwd"
MOSQUITTO_CONTAINER = os.environ.get("MOSQUITTO_CONTAINER", "smarthome-backend-mosquitto-1")


def _mosquitto_hash(password: str) -> str:
    """Tạo Mosquitto PBKDF2-SHA512 password hash (format $7$iterations$salt$key)."""
    iterations = 101
    salt = os.urandom(12)
    dk = hashlib.pbkdf2_hmac("sha512", password.encode(), salt, iterations, dklen=64)
    return f"$7${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def _mosquitto_reload() -> None:
    """Gửi SIGHUP tới Mosquitto container để reload passwd file."""
    try:
        import httpx
        transport = httpx.HTTPTransport(uds="/var/run/docker.sock")
        with httpx.Client(transport=transport, timeout=5) as client:
            client.post(f"http://localhost/containers/{MOSQUITTO_CONTAINER}/kill?signal=SIGHUP")
    except Exception:
        pass


def _add_mosquitto_user(username: str, password: str) -> None:
    """Thêm/cập nhật user trong Mosquitto passwd file, sau đó reload broker."""
    try:
        passwd_hash = _mosquitto_hash(password)
        lines: list[str] = []
        try:
            with open(PASSWD_FILE, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass
        # Xoá dòng cũ nếu user đã tồn tại
        lines = [l for l in lines if not l.startswith(f"{username}:")]
        lines.append(f"{username}:{passwd_hash}\n")
        with open(PASSWD_FILE, "w") as f:
            f.writelines(lines)
        _mosquitto_reload()
    except OSError:
        pass


def _delete_mosquitto_user(username: str) -> None:
    try:
        lines: list[str] = []
        with open(PASSWD_FILE, "r") as f:
            lines = f.readlines()
        lines = [l for l in lines if not l.startswith(f"{username}:")]
        with open(PASSWD_FILE, "w") as f:
            f.writelines(lines)
        _mosquitto_reload()
    except OSError:
        pass


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register")
async def register_device(body: DeviceRegister, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Đăng ký device — idempotent: nếu đã tồn tại thì trả về credentials hiện có.
    ESP32 có thể gọi lại sau mỗi lần factory reset mà không bị lỗi.
    """
    result = await db.execute(select(Device).where(Device.device_id == body.device_id))
    existing = result.scalar_one_or_none()

    if existing:
        # Device đã đăng ký — trả về credentials cũ
        return {
            "device_id": existing.device_id,
            "mqtt_host": settings.mqtt_host,
            "mqtt_port": settings.mqtt_port,
            "mqtt_username": existing.device_id,
            "mqtt_password": existing.mqtt_password,
            "already_registered": True,
        }

    password = secrets.token_hex(16)
    device = Device(
        device_id=body.device_id,
        product_id=body.product_id,
        product_name=body.product_name,
        mqtt_password=password,
        user_id=current_user.id,
    )
    db.add(device)
    await db.commit()

    _add_mosquitto_user(body.device_id, password)
    _add_mosquitto_user(settings.mqtt_username, settings.mqtt_password)

    return {
        "device_id": body.device_id,
        "mqtt_host": settings.mqtt_host,
        "mqtt_port": settings.mqtt_port,
        "mqtt_username": body.device_id,
        "mqtt_password": password,
        "already_registered": False,
    }


@router.get("/", response_model=list[DeviceOut])
async def list_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = _device_filter(select(Device).order_by(Device.created_at.desc()), current_user)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{device_id}", response_model=DeviceDetailOut)
async def get_device(device_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = _device_filter(
        select(Device).where(Device.device_id == device_id).options(selectinload(Device.dp_states)),
        current_user,
    )
    result = await db.execute(q)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    dp_states = [
        DpStateOut(dp_id=s.dp_id, value=_extract_value(s), updated_at=s.updated_at)
        for s in sorted(device.dp_states, key=lambda x: x.dp_id)
    ]
    return DeviceDetailOut(**DeviceOut.model_validate(device).model_dump(), dp_states=dp_states)


@router.patch("/{device_id}")
async def update_device(device_id: str, body: DeviceUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(_device_filter(select(Device).where(Device.device_id == device_id), current_user))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")
    if body.friendly_name is not None:
        device.friendly_name = body.friendly_name or None
    if body.room is not None:
        device.room = body.room or None
    if body.user_id is not None and current_user.is_admin:
        device.user_id = body.user_id if body.user_id != 0 else None
    await db.commit()
    return {"ok": True}


@router.post("/{device_id}/cmd")
async def send_command(device_id: str, body: CommandRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(_device_filter(select(Device).where(Device.device_id == device_id), current_user))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    await publish_command(device_id, body.dp_id, body.value)
    return {"ok": True, "device_id": device_id, "dp_id": body.dp_id, "value": body.value}


@router.get("/{device_id}/history", response_model=list[HistoryItem])
async def get_history(
    device_id: str,
    dp_id: int | None = None,
    hours: int = 24,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(_device_filter(select(Device).where(Device.device_id == device_id), current_user))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    since = datetime.utcnow() - timedelta(hours=hours)
    query = select(DpHistory).where(
        DpHistory.device_id == device.id,
        DpHistory.timestamp >= since,
    )
    if dp_id is not None:
        query = query.where(DpHistory.dp_id == dp_id)
    query = query.order_by(DpHistory.timestamp.asc()).limit(limit)

    rows = await db.execute(query)
    return [
        HistoryItem(dp_id=r.dp_id, value=_extract_value(r), timestamp=r.timestamp)
        for r in rows.scalars()
    ]


@router.delete("/{device_id}")
async def delete_device(device_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(_device_filter(select(Device).where(Device.device_id == device_id), current_user))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    await db.delete(device)
    await db.commit()
    _delete_mosquitto_user(device_id)
    return {"ok": True}
