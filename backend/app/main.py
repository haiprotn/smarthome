import asyncio
import logging
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, Base
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.devices import router as devices_router
from app.api.firmware import router as firmware_router
from app.api.schedules import router as schedules_router
from app.ws.router import router as ws_router
from app.mqtt.client import mqtt_loop
from app.core.scheduler import scheduler_loop

STATIC_DIR = Path(__file__).parent / "static"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.models import user as _  # noqa: ensure User model is registered
    from app.models import schedule as _s  # noqa: ensure Schedule model is registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE devices ADD COLUMN IF NOT EXISTS friendly_name VARCHAR(128)"))
        await conn.execute(text("ALTER TABLE devices ADD COLUMN IF NOT EXISTS room VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE devices ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"))
        # Rename email → username if old schema still exists
        await conn.execute(text("""
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name='users' AND column_name='email') THEN
                    ALTER TABLE users RENAME COLUMN email TO username;
                END IF;
            END $$;
        """))
    log.info("Database tables ready")

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    mqtt_task = asyncio.create_task(mqtt_loop(redis))
    scheduler_task = asyncio.create_task(scheduler_loop())
    log.info("MQTT + Scheduler background tasks started")

    yield

    mqtt_task.cancel()
    scheduler_task.cancel()
    await redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="Smart Home Backend",
    version="2.0.0",
    description="IoT backend — MQTT + WebSocket + REST API",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(devices_router)
app.include_router(schedules_router)
app.include_router(firmware_router)
app.include_router(ws_router)

# Serve React static assets (/assets/, /favicon.svg, ...)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon():
        return FileResponse(STATIC_DIR / "favicon.svg")

    @app.get("/icons.svg", include_in_schema=False)
    async def icons():
        return FileResponse(STATIC_DIR / "icons.svg")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


# SPA fallback — mọi route không khớp đều trả index.html
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    return FileResponse(STATIC_DIR / "index.html")
