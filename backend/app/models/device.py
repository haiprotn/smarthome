from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # MAC address
    product_id: Mapped[str] = mapped_column(String(64))   # switch_1g, smart_plug, ...
    product_name: Mapped[str] = mapped_column(String(128))
    mqtt_password: Mapped[str] = mapped_column(String(128))  # plain text (stored in Mosquitto passwd)
    friendly_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    owner: Mapped["User | None"] = relationship("User", back_populates="devices")

    dp_states: Mapped[list["DpState"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    dp_history: Mapped[list["DpHistory"]] = relationship(back_populates="device", cascade="all, delete-orphan")


class DpState(Base):
    """Trạng thái hiện tại của từng Data Point — luôn là bản mới nhất"""
    __tablename__ = "dp_states"
    __table_args__ = (UniqueConstraint("device_id", "dp_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    dp_id: Mapped[int] = mapped_column(Integer)
    value: Mapped[dict] = mapped_column(JSON)        # {"v": true} hoặc {"v": 42}
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    device: Mapped["Device"] = relationship(back_populates="dp_states")


class DpHistory(Base):
    """Lịch sử thay đổi DP — mỗi lần thay đổi ghi một row"""
    __tablename__ = "dp_history"
    __table_args__ = (
        Index("ix_dp_history_device_dp_ts", "device_id", "dp_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    dp_id: Mapped[int] = mapped_column(Integer)
    value: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    device: Mapped["Device"] = relationship(back_populates="dp_history")
