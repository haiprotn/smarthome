"""
Schedule API:
  GET    /api/devices/{device_id}/schedules         — Lịch của device
  POST   /api/devices/{device_id}/schedules         — Tạo lịch mới
  PATCH  /api/devices/{device_id}/schedules/{id}   — Sửa lịch
  DELETE /api/devices/{device_id}/schedules/{id}   — Xóa lịch
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.device import Device
from app.models.schedule import Schedule
from app.models.user import User

router = APIRouter(tags=["schedules"])

_TIME_RE = re.compile(r'^\d{2}:\d{2}$')


class ScheduleBody(BaseModel):
    dp_id: int
    value: bool | int
    days: list[int]         # [0..6]
    time_hhmm: str          # "HH:MM"
    label: str | None = None
    enabled: bool = True

    @field_validator("time_hhmm")
    @classmethod
    def validate_time(cls, v: str) -> str:
        if not _TIME_RE.match(v):
            raise ValueError("time_hhmm phải theo định dạng HH:MM")
        h, m = map(int, v.split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Giờ/phút không hợp lệ")
        return v

    @field_validator("days")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        if not v or not all(0 <= d <= 6 for d in v):
            raise ValueError("days phải là list các ngày 0-6")
        return sorted(set(v))


class SchedulePatch(BaseModel):
    dp_id: int | None = None
    value: bool | int | None = None
    days: list[int] | None = None
    time_hhmm: str | None = None
    label: str | None = None
    enabled: bool | None = None


class ScheduleOut(BaseModel):
    id: int
    dp_id: int
    value: bool | int
    days: list[int]
    time_hhmm: str
    label: str | None
    enabled: bool

    class Config:
        from_attributes = True


async def _get_device(device_id: str, user: User, db: AsyncSession) -> Device:
    from app.api.devices import _device_filter
    result = await db.execute(
        _device_filter(select(Device).where(Device.device_id == device_id), user)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")
    return device


@router.get("/api/devices/{device_id}/schedules", response_model=list[ScheduleOut])
async def list_schedules(device_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    device = await _get_device(device_id, current_user, db)
    result = await db.execute(select(Schedule).where(Schedule.device_id == device.id).order_by(Schedule.time_hhmm))
    schedules = result.scalars().all()
    return [
        ScheduleOut(id=s.id, dp_id=s.dp_id, value=s.value["v"], days=s.days,
                    time_hhmm=s.time_hhmm, label=s.label, enabled=s.enabled)
        for s in schedules
    ]


@router.post("/api/devices/{device_id}/schedules", response_model=ScheduleOut, status_code=201)
async def create_schedule(device_id: str, body: ScheduleBody, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    device = await _get_device(device_id, current_user, db)
    s = Schedule(
        device_id=device.id,
        user_id=current_user.id,
        dp_id=body.dp_id,
        value={"v": body.value},
        days=body.days,
        time_hhmm=body.time_hhmm,
        label=body.label,
        enabled=body.enabled,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return ScheduleOut(id=s.id, dp_id=s.dp_id, value=s.value["v"], days=s.days,
                       time_hhmm=s.time_hhmm, label=s.label, enabled=s.enabled)


@router.patch("/api/devices/{device_id}/schedules/{schedule_id}", response_model=ScheduleOut)
async def update_schedule(device_id: str, schedule_id: int, body: SchedulePatch, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    device = await _get_device(device_id, current_user, db)
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id, Schedule.device_id == device.id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Schedule not found")

    if body.dp_id is not None:
        s.dp_id = body.dp_id
    if body.value is not None:
        s.value = {"v": body.value}
    if body.days is not None:
        s.days = sorted(set(body.days))
    if body.time_hhmm is not None:
        s.time_hhmm = body.time_hhmm
    if body.label is not None:
        s.label = body.label or None
    if body.enabled is not None:
        s.enabled = body.enabled

    await db.commit()
    return ScheduleOut(id=s.id, dp_id=s.dp_id, value=s.value["v"], days=s.days,
                       time_hhmm=s.time_hhmm, label=s.label, enabled=s.enabled)


@router.delete("/api/devices/{device_id}/schedules/{schedule_id}")
async def delete_schedule(device_id: str, schedule_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    device = await _get_device(device_id, current_user, db)
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id, Schedule.device_id == device.id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Schedule not found")
    await db.delete(s)
    await db.commit()
    return {"ok": True}
