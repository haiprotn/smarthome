"""
Admin API (yêu cầu quyền admin):
  GET    /api/admin/users              — Danh sách tất cả users
  PATCH  /api/admin/users/{user_id}   — Toggle admin role
  DELETE /api/admin/users/{user_id}   — Xóa user
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_admin_user
from app.core.database import get_db
from app.models.user import User
from app.models.device import Device

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserAdminOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    device_count: int

    class Config:
        from_attributes = True


@router.get("/users", response_model=list[UserAdminOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()

    # Đếm device cho từng user
    counts_result = await db.execute(
        select(Device.user_id, func.count(Device.id).label("cnt"))
        .where(Device.user_id.isnot(None))
        .group_by(Device.user_id)
    )
    counts = {row.user_id: row.cnt for row in counts_result}

    return [
        UserAdminOut(
            id=u.id,
            username=u.username,
            is_admin=u.is_admin,
            device_count=counts.get(u.id, 0),
        )
        for u in users
    ]


@router.patch("/users/{user_id}")
async def toggle_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    if user_id == current_admin.id:
        raise HTTPException(400, "Không thể thay đổi quyền của chính mình")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User không tồn tại")

    user.is_admin = not user.is_admin
    await db.commit()
    return {"ok": True, "is_admin": user.is_admin}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    if user_id == current_admin.id:
        raise HTTPException(400, "Không thể xóa chính mình")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User không tồn tại")

    await db.delete(user)
    await db.commit()
    return {"ok": True}
