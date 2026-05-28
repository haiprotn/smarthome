from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, JSON, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Schedule(Base):
    """
    Lịch tự động cho device.
    days: JSON list các ngày trong tuần [0..6] (0=Thứ Hai, 6=Chủ Nhật)
    time_hhmm: "HH:MM" (VD: "07:30")
    dp_id: DP cần điều khiển
    value: giá trị cần set (bool/int)
    enabled: có đang bật không
    """
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    dp_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)   # {"v": true/false/int}
    days: Mapped[list] = mapped_column(JSON, nullable=False)    # [0,1,2,3,4] = T2-T6
    time_hhmm: Mapped[str] = mapped_column(String(5), nullable=False)  # "07:30"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    device: Mapped["Device"] = relationship("Device")  # type: ignore[name-defined]
