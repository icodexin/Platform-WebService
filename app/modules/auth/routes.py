from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas import TokenResponse
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, oauth2_scheme
from app.core.utils import get_client_ip
from app.modules.auth.services import authenticate_user, verify_token, revoke_token, update_login_info

router = APIRouter(prefix="/auth")


@router.post("/token", response_model=TokenResponse)
async def login_endpoint(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """用户认证"""
    # 此处的 form_data.username 是学号/工号, 即 数据库中的 user_id
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.user_id)
    refresh_token = create_refresh_token(user.user_id)
    # 更新用户的最后登录信息
    await update_login_info(form_data.username, get_client_ip(request), datetime.now(), db=db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(refresh_token: str = Form(...), db: AsyncSession = Depends(get_db)):
    # 解码并验证令牌有效性
    payload = await verify_token(refresh_token, "refresh", db=db)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 拉黑旧令牌
    await revoke_token(payload["jti"], payload["sub"], "refresh", datetime.fromtimestamp(payload["exp"]), db=db)

    # 颁发新令牌
    new_access_token = create_access_token(payload["sub"])
    new_refresh_token = create_refresh_token(payload["sub"], expire_at=datetime.fromtimestamp(payload["exp"]))
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_endpoint(
        access_token: str = Depends(oauth2_scheme), refresh_token: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    """
    注销用户，撤销当前访问令牌和刷新令牌。
    """
    # 验证访问令牌
    payload = await verify_token(access_token, "access", db=db)
    if payload:
        # 拉黑访问令牌
        await revoke_token(jti=payload["jti"], user_id=payload["sub"], token_type="access",
                           expires_at=datetime.fromtimestamp(payload["exp"]), revoked_reason="logout", db=db)

    # 验证刷新令牌
    payload = await verify_token(refresh_token, "refresh", db=db)
    if payload:
        # 拉黑刷新令牌
        await revoke_token(jti=payload["jti"], user_id=payload["sub"], token_type="refresh",
                           expires_at=datetime.fromtimestamp(payload["exp"]), revoked_reason="logout", db=db)
