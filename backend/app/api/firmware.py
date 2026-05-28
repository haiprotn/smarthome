"""
Firmware OTA API:
  POST  /api/firmware/upload              — Upload file .bin lên server
  GET   /api/firmware/latest              — Lấy thông tin firmware mới nhất
  GET   /api/firmware/{filename}          — Download file firmware
  POST  /api/devices/{device_id}/ota      — Ra lệnh OTA cho device qua MQTT
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.config import settings
from app.mqtt.client import publish_command

router = APIRouter(prefix="/api/firmware", tags=["firmware"])

FIRMWARE_DIR = Path("/app/firmware")
FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)


def _firmware_url(filename: str) -> str:
    """Tạo URL public cho file firmware"""
    host = os.environ.get("PUBLIC_HOST", "192.168.1.100")
    port = os.environ.get("PUBLIC_PORT", "8000")
    return f"http://{host}:{port}/api/firmware/{filename}"


# ─── Upload firmware ──────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_firmware(
    file: UploadFile = File(...),
    product_id: str = Form(...),        # "switch_1g"
    version: str = Form(...),           # "1.1.0"
):
    """Upload file firmware .bin cho product"""
    if not file.filename.endswith(".bin"):
        raise HTTPException(400, "Chỉ chấp nhận file .bin")

    # Lưu theo tên chuẩn: {product_id}_v{version}.bin
    filename = f"{product_id}_v{version}.bin"
    dest = FIRMWARE_DIR / filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    size_kb = dest.stat().st_size // 1024
    url = _firmware_url(filename)

    return {
        "ok": True,
        "filename": filename,
        "product_id": product_id,
        "version": version,
        "size_kb": size_kb,
        "url": url,
    }


# ─── Lấy firmware mới nhất ───────────────────────────────────────────────────

@router.get("/latest")
async def get_latest_firmware(product_id: str, version: str = "0.0.0"):
    """
    Trả về thông tin firmware mới nhất cho product.
    Tham số version: firmware hiện tại của device (để so sánh).
    """
    bins = sorted(FIRMWARE_DIR.glob(f"{product_id}_v*.bin"), reverse=True)
    if not bins:
        raise HTTPException(404, f"Chưa có firmware cho product '{product_id}'")

    latest = bins[0]
    latest_version = latest.stem.split("_v", 1)[-1]
    size_kb = latest.stat().st_size // 1024
    url = _firmware_url(latest.name)

    needs_update = latest_version != version

    return {
        "product_id": product_id,
        "current_version": version,
        "latest_version": latest_version,
        "needs_update": needs_update,
        "filename": latest.name,
        "size_kb": size_kb,
        "url": url if needs_update else None,
    }


# ─── Download firmware ────────────────────────────────────────────────────────

@router.get("/{filename}")
async def download_firmware(filename: str):
    """Phục vụ file firmware để ESP32 download khi OTA"""
    path = FIRMWARE_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(404, f"File '{filename}' không tồn tại")
    # Bảo vệ path traversal
    if not path.resolve().is_relative_to(FIRMWARE_DIR.resolve()):
        raise HTTPException(400, "Invalid filename")
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=filename,
    )


# ─── Trigger OTA qua MQTT ─────────────────────────────────────────────────────

@router.post("/trigger/{device_id}")
async def trigger_ota(device_id: str, product_id: str, version: str):
    """
    Gửi lệnh OTA xuống device qua MQTT.
    Device sẽ tự download firmware từ URL trả về.
    """
    bins = sorted(FIRMWARE_DIR.glob(f"{product_id}_v{version}.bin"))
    if not bins:
        raise HTTPException(404, f"Firmware {product_id} v{version} chưa được upload")

    url = _firmware_url(bins[0].name)

    # Publish MQTT command: {"action": "ota", "url": "http://..."}
    # Dùng dp_id=255 làm OTA command đặc biệt
    await publish_command(device_id, 255, {"action": "ota", "url": url})

    return {
        "ok": True,
        "device_id": device_id,
        "firmware_url": url,
        "message": "OTA command sent via MQTT",
    }
