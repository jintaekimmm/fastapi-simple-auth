from datetime import datetime

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import TokenExpiredException
from core.responses import ErrorJSONResponse
import crud
from dependencies.auth import AuthorizeRefreshToken, AuthorizeRefreshCookie
from dependencies.database import get_session
import models
import schemas
from utils.security.encryption import Hasher, AESCipher
from utils.security.token import create_new_jwt_token

router = APIRouter(prefix="/token", tags=["Token"])


@router.post(
    "/refresh/api",
    response_model=schemas.TokenSchema,
    responses={
        401: {"model": schemas.ErrorResponse},
        404: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse},
    },
)
async def api_token_refresh(
    *,
    refresh_token: str = Depends(AuthorizeRefreshToken()),
    session: AsyncSession = Depends(get_session),
):
    """
    TokenRefresh API

    refreshToken을 사용하여 새로운 토큰을 생성하여 반환한다
    """

    aes = AESCipher()
    user_dal = crud.UserDAL(session=session)
    token_dal = crud.TokenDAL(session=session)

    # 저장되어 있는 refreshToken을 조회한다
    saved_token: models.JWTToken = await token_dal.get(
        refresh_token_key=Hasher.hmac_sha256(refresh_token)
    )
    if not saved_token:
        return ErrorJSONResponse(
            message="인증 토큰이 존재하지 않습니다",
            success=False,
            error_code=1404,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if saved_token and saved_token.expires_at < datetime.now():
        logger.info(f'토큰이 만료되었습니다 { {"user_id": saved_token.user_id} }')
        raise TokenExpiredException()

    login_user: models.User = await user_dal.get_by_user_id(user_id=saved_token.user_id)
    if not login_user:
        logger.info(f'사용자를 찾을 수 없습니다. { {"user_id": saved_token.user_id} }')
        return ErrorJSONResponse(
            message="사용자를 찾을 수 없습니다",
            success=False,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=1404,
        )
    # 신규 accessToken을 생성한다
    # refreshToken 값은 갱신하지 않고, 만료 날짜만 늘린다
    new_token: schemas.TokenSchema = await create_new_jwt_token(
        sub=str(saved_token.user_id)
    )
    new_token.refresh_token = aes.decrypt(saved_token.refresh_token)

    update_token = schemas.TokenUpdateSchema(
        user_id=saved_token.user_id,
        access_token=new_token.access_token,
        refresh_token=saved_token.refresh_token,
        refresh_token_key=saved_token.refresh_token_key,
        expires_at=datetime.fromtimestamp(int(new_token.refresh_token_expires_in)),
    )

    try:
        await token_dal.update(update_token=update_token)

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return ErrorJSONResponse(
            message="토큰 갱신을 실패하였습니다",
            success=False,
            error_code=1500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        await session.close()

    logger.info(f'토큰을 갱신하였습니다. { {"user_id": saved_token.user_id} }')

    response = schemas.TokenSchema(**new_token.model_dump())

    return response


@router.post(
    "/refresh/web",
    response_model=schemas.TokenSchema,
    responses={
        401: {"model": schemas.ErrorResponse},
        404: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse},
    },
)
async def web_token_refresh(
    *,
    refresh_token: str = Depends(AuthorizeRefreshCookie()),
    session: AsyncSession = Depends(get_session),
):
    """
    TokenRefresh API

    refreshToken을 사용하여 새로운 토큰을 생성하여 반환한다
    """

    aes = AESCipher()
    user_dal = crud.UserDAL(session=session)
    token_dal = crud.TokenDAL(session=session)

    # 저장되어 있는 refreshToken을 조회한다
    saved_token: models.JWTToken = await token_dal.get(
        refresh_token_key=Hasher.hmac_sha256(refresh_token)
    )
    if not saved_token:
        return ErrorJSONResponse(
            message="인증 토큰이 존재하지 않습니다",
            success=False,
            error_code=1404,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if saved_token and saved_token.expires_at < datetime.now():
        logger.info(f'토큰이 만료되었습니다 { {"user_id": saved_token.user_id} }')
        raise TokenExpiredException()

    login_user: models.User = await user_dal.get_by_user_id(user_id=saved_token.user_id)
    if not login_user:
        logger.info(f'사용자를 찾을 수 없습니다. { {"user_id": saved_token.user_id} }')
        return ErrorJSONResponse(
            message="사용자를 찾을 수 없습니다",
            success=False,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=1404,
        )
    # 신규 accessToken을 생성한다
    # refreshToken 값은 갱신하지 않고, 만료 날짜만 늘린다
    new_token: schemas.TokenSchema = await create_new_jwt_token(
        sub=str(saved_token.user_id)
    )
    new_token.refresh_token = aes.decrypt(saved_token.refresh_token)

    update_token = schemas.TokenUpdateSchema(
        user_id=saved_token.user_id,
        access_token=new_token.access_token,
        refresh_token=saved_token.refresh_token,
        refresh_token_key=saved_token.refresh_token_key,
        expires_at=datetime.fromtimestamp(int(new_token.refresh_token_expires_in)),
    )

    try:
        await token_dal.update(update_token=update_token)

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return ErrorJSONResponse(
            message="토큰 갱신을 실패하였습니다",
            success=False,
            error_code=1500,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        await session.close()

    logger.info(f'토큰을 갱신하였습니다. { {"user_id": saved_token.user_id} }')

    token_response = schemas.TokenAccessOnlySchema(**new_token.model_dump())
    # accessToken은 json으로 반환한다
    response = JSONResponse(content=token_response.model_dump())
    # refreshToken은 Cookie로 반환한다
    response.set_cookie(
        key="refresh_token",
        value=f"{new_token.refresh_token}",
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response
