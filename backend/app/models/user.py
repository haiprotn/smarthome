from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id:            Mapped[int]      = mapped_column(Integer, primary_key=True)
    username:      Mapped[str]      = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]   = mapped_column(String(255), nullable=False)
    is_admin:      Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at:    Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    devices: Mapped[list] = relationship("Device", back_populates="owner", lazy="select")
