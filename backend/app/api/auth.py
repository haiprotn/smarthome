"""
Auth API:
  POST /api/auth/register  — Đăng ký tài khoản mới (email hoặc số điện thoại)
  POST /api/auth/login     — Đăng nhập, set HttpOnly cookie
  POST /api/auth/logout    — Xoá cookie
  GET  /api/auth/me        — Thông tin user hiện tại
"""
import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token, get_current_user,
    hash_password, verify_password,
)
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_PHONE_RE = re.compile(r'^(0|\+84)\d{9}$')


def _validate_identifier(value: str) -> str:
    """Trả về identifier đã chuẩn hoá, raise 400 nếu không hợp lệ."""
    value = value.strip()
    if _PHONE_RE.match(value):
        # Chuẩn hoá: bỏ khoảng trắng, giữ nguyên format 0xxxxxxxxx hoặc +84xxxxxxxxx
        return value
    if _EMAIL_RE.match(value):
        return value.lower()
    raise HTTPException(400, "Vui lòng nhập email hoặc số điện thoại hợp lệ (VD: 0901234567)")


class RegisterBody(BaseModel):
    username: str   # email hoặc số điện thoại
    password: str


class LoginBody(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    identifier = _validate_identifier(body.username)
    if len(body.password) < 6:
        raise HTTPException(400, "Mật khẩu tối thiểu 6 ký tự")

    result = await db.execute(select(User).where(User.username == identifier))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Tài khoản đã được đăng ký")

    count = (await db.execute(select(User))).scalars().all()
    is_admin = len(count) == 0

    user = User(username=identifier, hashed_password=hash_password(body.password), is_admin=is_admin)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login")
async def login(body: LoginBody, response: Response, db: AsyncSession = Depends(get_db)):
    identifier = _validate_identifier(body.username)
    result = await db.execute(select(User).where(User.username == identifier))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Tài khoản hoặc mật khẩu không đúng")

    token = create_access_token(user.id, user.is_admin)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    return {"ok": True, "username": user.username, "is_admin": user.is_admin}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
