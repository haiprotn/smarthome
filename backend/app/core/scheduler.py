"""Background task: kiểm tra schedules mỗi phút, publish MQTT command nếu đến giờ."""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.schedule import Schedule
from app.mqtt.client import publish_command

log = logging.getLogger(__name__)

_last_fired: set[tuple[int, str]] = set()  # (schedule_id, "YYYY-MM-DD HH:MM") đã chạy


async def scheduler_loop() -> None:
    log.info("[Scheduler] Started")
    while True:
        try:
            await _tick()
        except Exception:
            log.exception("[Scheduler] Error in tick")
        await asyncio.sleep(20)  # check mỗi 20s để không bỏ sót khi giây lẻ


async def _tick() -> None:
    now = datetime.now()  # local time
    hhmm = now.strftime("%H:%M")
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    fired_key_prefix = now.strftime("%Y-%m-%d ") + hhmm

    async with async_session_factory() as db:
        result = await db.execute(
            select(Schedule).where(Schedule.enabled == True, Schedule.time_hhmm == hhmm)
        )
        schedules = result.scalars().all()

    for s in schedules:
        if weekday not in (s.days or []):
            continue
        key = (s.id, fired_key_prefix)
        if key in _last_fired:
            continue  # đã chạy trong phút này rồi

        # Lấy device_id string từ DB
        async with async_session_factory() as db:
            from app.models.device import Device
            dev_result = await db.execute(select(Device).where(Device.id == s.device_id))
            device = dev_result.scalar_one_or_none()

        if device:
            value = s.value.get("v")
            await publish_command(device.device_id, s.dp_id, value)
            log.info("[Scheduler] Fired schedule %d → device %s dp%d=%s", s.id, device.device_id, s.dp_id, value)
            _last_fired.add(key)

    # Dọn cache cũ (giữ tối đa 500 entry)
    if len(_last_fired) > 500:
        _last_fired.clear()
