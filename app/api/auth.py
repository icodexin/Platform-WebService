from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import TokenTypeEnum
from app.core import get_db
from app.core.security import create_access_token, create_refresh_token, oauth2_scheme
from app.schemas.token import TokenResponse
from app.services.auth import authenticate_user, revoke_token, verify_token

router = APIRouter(prefix="/auth")


@router.post("/token", response_model=TokenResponse)
async def token_endpoint(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户认证并颁发令牌"""
    # 表单数据中的username是统一身份ID
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    uid = user.id
    access_token = create_access_token(uid)
    refresh_token = create_refresh_token(uid)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    # 验证刷新令牌
    payload = await verify_token(refresh_token, TokenTypeEnum.refresh, db=db)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 拉黑旧令牌
    jti = payload["jti"]
    uid = payload["sub"]
    exp = datetime.fromtimestamp(payload["exp"])
    await revoke_token(jti, uid, TokenTypeEnum.refresh, exp, "Refresh token used", db=db)

    # 颁发新令牌
    new_access_token = create_access_token(uid)
    new_refresh_token = create_refresh_token(uid, expire_at=exp)
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout_endpoint(
    access_token: str = Depends(oauth2_scheme),
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """注销用户，撤销令牌"""
    # 验证访问令牌
    payload = await verify_token(access_token, TokenTypeEnum.access, db=db)
    if payload:
        # 拉黑访问令牌
        await revoke_token(
            jti=payload["jti"],
            user_id=payload["sub"],
            token_type=TokenTypeEnum.access,
            expires_at=datetime.fromtimestamp(payload["exp"]),
            revoked_reason="logout",
            db=db
        )

    # 验证刷新令牌
    payload = await verify_token(refresh_token, TokenTypeEnum.refresh, db=db)
    if payload:
        # 拉黑刷新令牌
        await revoke_token(
            jti=payload["jti"],
            user_id=payload["sub"],
            token_type=TokenTypeEnum.refresh,
            expires_at=datetime.fromtimestamp(payload["exp"]),
            revoked_reason="logout",
            db=db
        )
