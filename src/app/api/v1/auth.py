import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
from core.exceptions import TokenExpiredException
from core.responses import ErrorJSONResponse, DefaultJSONResponse
import crud
from dependencies.auth import AuthorizeToken, AuthorizeRefreshToken
from dependencies.database import get_session
import models
import schemas
from utils.security.auth import authenticate
from utils.security.encryption import AESCipher, Hasher
from utils.security.token import create_new_jwt_token
from utils.strings import masking_str

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=schemas.RegisterResponseSchema,
    responses={
        404: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse},
    },
)
async def register_user(
    *,
    register_request: schemas.RegisterRequestSchema,
    session: AsyncSession = Depends(get_session),
):
    """
    Register API
    """

    aes = AESCipher()
    user_dal = crud.UserDAL(session=session)

    # 암호화된 이메일 검색을 위한 Index Key 생성
    email_key: str = Hasher.hmac_sha256(register_request.email)
    # 이미 등록된 이메일 주소인지 확인한다
    if await user_dal.exists_email(email_key=email_key):
        return ErrorJSONResponse(
            message="사용할 수 없는 이메일 주소입니다",
            success=False,
            status_code=status.HTTP_409_CONFLICT,
            error_code=1409,
        )

    mobile: str | None = None
    # 암호화된 핸드폰 번호 검색을 위한 Index Key 생성
    mobile_key: str | None = (
        Hasher.hmac_sha256(register_request.mobile) if register_request.mobile else None
    )
    # 핸드폰 번호를 입력하였다면, 이미 등록된 핸드폰 번호인지 확인한다
    if register_request.mobile:
        if await user_dal.exists_mobile(mobile_key=mobile_key):
            return ErrorJSONResponse(
                message="사용할 수 없는 핸드폰 번호입니다",
                success=False,
                status_code=status.HTTP_409_CONFLICT,
                error_code=1409,
            )
        else:
            mobile = aes.encrypt(register_request.mobile)

    new_register = schemas.RegisterInsertSchema(
        name=register_request.name,
        email=aes.encrypt(register_request.email),
        email_key=email_key,
        uuid=uuid.uuid4().bytes,
        mobile=mobile,
        mobile_key=mobile_key,
        password=Hasher.get_password_hash(register_request.password1),
        is_active=1,
    )

    try:
        result = await user_dal.insert_register(new_register=new_register)
        new_user_id = result.inserted_primary_key[0]

        await session.commit()

    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return ErrorJSONResponse(
            message="회원가입을 처리하는 도중에 문제가 발생하였습니다",
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=1500,
        )

    finally:
        await session.close()

    response = schemas.RegisterResponseSchema(
        id=new_user_id, success=True, message="회원가입을 환영합니다"
    )

    return response


###########################################################################
# API Authentication
###########################################################################
@router.post(
    "/api/login",
    response_model=schemas.TokenSchema,
    responses={
        400: {"model": schemas.ErrorResponse},
        403: {"model": schemas.ErrorResponse},
        404: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse},
    },
)
async def api_login(
    *,
    login_request: schemas.LoginSchema,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Login API

    로그인 후 토큰 정보를 JSON으로 반환한다
    accessToken, refreshToken 모두 JSON Body에 포함하여 반환한다
    """

    aes = AESCipher()
    user_dal = crud.UserDAL(session=session)
    user_login_dal = crud.UserLoginHistoryDAL(session=session)
    token_dal = crud.TokenDAL(session=session)

    try:
        login_user: models.User = await user_dal.get_by_email(
            email_key=Hasher.hmac_sha256(login_request.email)
        )

    except TypeError as e:
        logger.info(
            f'사용자를 조회하는 도중에 문제가 발생하였습니다. { {"email": masking_str(login_request.email)} }'
        )
        logger.exception(e)
        return ErrorJSONResponse(
            message="사용자를 조회하는 도중에 문제가 발생하였습니다",
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=1500,
        )

    if not login_user:
        logger.info(f'사용자를 찾을 수 없습니다. { {"email": masking_str(login_request.email)} }')
        return ErrorJSONResponse(
            message="사용자를 찾을 수 없습니다",
            success=False,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=1404,
        )

    if not login_user.is_active:
        logger.info(
            f'사용할 수 없는 아이디 입니다. { {"email": masking_str(login_request.email)} }'
        )
        return ErrorJSONResponse(
            message="사용할 수 없는 아이디 입니다",
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=1400,
        )

    if not await authenticate(
        plain_password=login_request.password, user_password=login_user.password
    ):
        logger.info(f'사용자 인증에 실패하였습니다. { {"email": masking_str(login_request.email)} }')
        return ErrorJSONResponse(
            message="사용자 인증에 실패하였습니다",
            success=False,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=1403,
        )

    # JWT Token쌍을 생성한다
    new_token: schemas.TokenSchema = await create_new_jwt_token(sub=str(login_user.id))

    # 생성한 RefreshToken을 DB에 저장하기 위한 스키마 생성
    new_refresh_token = schemas.TokenInsertSchema(
        user_id=login_user.id,
        access_token=new_token.access_token,
        refresh_token=aes.encrypt(new_token.refresh_token),
        refresh_token_key=Hasher.hmac_sha256(new_token.refresh_token),
        issued_at=datetime.fromtimestamp(int(new_token.iat)),
        expires_at=datetime.fromtimestamp(int(new_token.refresh_token_expires_in)),
    )

    try:
        # Token 정보 저장
        await token_dal.insert_token(new_token=new_refresh_token)

        # Login 이력 저장
        await user_login_dal.insert_login_history(
            login_history=schemas.LoginHistorySchema(
                user_id=login_user.id,
                login_time=datetime.now(),
                login_success=True,
                ip_address=request.client.host,
            )
        )

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return ErrorJSONResponse(
            message="로그인을 하는 도중에 문제가 발생하였습니다",
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=1500,
        )
    finally:
        await session.close()

    logger.info(
        f'사용자가 로그인하였습니다. { {"user_id": login_user.id, "email": masking_str(login_request.email), "name": masking_str(login_user.name)} }'
    )

    response = schemas.TokenSchema(**new_token.dict())

    return response


@router.post(
    "/api/logout",
    response_model=schemas.DefaultResponse,
    responses={
        401: {"model": schemas.ErrorResponse},
        403: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse},
    },
)
async def api_logout(
    *,
    user_token: schemas.AuthTokenSchema = Depends(AuthorizeToken()),
    session: AsyncSession = Depends(get_session),
):
    """
    Logout API

    Authorization Header에 포함된 accessToken으로 발급된 토큰을 조회하여 삭제하여
    로그아웃을 시킨다
    - accessToken은 만료시킬 수 없으므로 토큰의 남은 시간까지는 사용 가능한 문제가 있다
    - redis에 blackList를 생성하여 관리하는 방법으로 이를 해결할 수도 있다
    """

    token_dal = crud.TokenDAL(session=session)

    try:
        if await token_dal.exists(
            user_id=int(user_token.sub), access_token=user_token.access_token
        ):
            await token_dal.delete(
                user_id=int(user_token.sub), access_token=user_token.access_token
            )

            await session.commit()
        else:
            # Token을 찾을 수 없는 경우에는 Logging만 하고 정상 결과를 반환한다
            logger.info(f'사용자 토큰을 찾을 수 없습니다. { {"user_id": user_token.sub} }')
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return ErrorJSONResponse(
            message="토큰 정보를 찾을 수 없습니다",
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=1500,
        )
    finally:
        await session.close()

    logger.info(f'사용자가 로그아웃 하였습니다. { {"user_id": user_token.sub} }')

    return DefaultJSONResponse(message="로그아웃 하였습니다", success=True)


###########################################################################
# WEB Authentication
###########################################################################
@router.post(
    "/web/login",
    response_model=schemas.TokenAccessOnlySchema,
    responses={
        400: {"model": schemas.ErrorResponse},
        403: {"model": schemas.ErrorResponse},
        404: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse},
    },
)
async def web_login(
    *,
    login_request: schemas.LoginSchema,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Login API

    로그인 후 토큰 정보를 JSON과 Cookie로 반환한다
    accessToken은 JSON Body로 refreshToken은 Cookie로 반환한다
    Cookie에 secure, httpOnly 기능을 사용하여 브라우저에서 토큰에 접근하지 못하도록 한다
    """

    aes = AESCipher()
    user_dal = crud.UserDAL(session=session)
    user_login_dal = crud.UserLoginHistoryDAL(session=session)
    token_dal = crud.TokenDAL(session=session)

    try:
        login_user: models.User = await user_dal.get_by_email(
            email_key=Hasher.hmac_sha256(login_request.email)
        )

    except TypeError as e:
        logger.info(
            f'사용자를 조회하는 도중에 문제가 발생하였습니다. { {"email": masking_str(login_request.email)} }'
        )
        logger.exception(e)
        return ErrorJSONResponse(
            message="사용자를 조회하는 도중에 문제가 발생하였습니다",
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=1500,
        )

    if not login_user:
        logger.info(f'사용자를 찾을 수 없습니다. { {"email": masking_str(login_request.email)} }')
        return ErrorJSONResponse(
            message="사용자를 찾을 수 없습니다",
            success=False,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=1404,
        )

    if not login_user.is_active:
        logger.info(
            f'사용할 수 없는 아이디 입니다. { {"email": masking_str(login_request.email)} }'
        )
        return ErrorJSONResponse(
            message="사용할 수 없는 아이디 입니다",
            success=False,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=1400,
        )

    if not await authenticate(
        plain_password=login_request.password, user_password=login_user.password
    ):
        logger.info(f'사용자 인증에 실패하였습니다. { {"email": masking_str(login_request.email)} }')
        return ErrorJSONResponse(
            message="사용자 인증에 실패하였습니다",
            success=False,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=1403,
        )

    # JWT Token쌍을 생성한다
    new_token: schemas.TokenSchema = await create_new_jwt_token(sub=str(login_user.id))

    # 생성한 RefreshToken을 DB에 저장하기 위한 스키마 생성
    new_refresh_token = schemas.TokenInsertSchema(
        user_id=login_user.id,
        access_token=new_token.access_token,
        refresh_token=aes.encrypt(new_token.refresh_token),
        refresh_token_key=Hasher.hmac_sha256(new_token.refresh_token),
        issued_at=datetime.fromtimestamp(int(new_token.iat)),
        expires_at=datetime.fromtimestamp(int(new_token.refresh_token_expires_in)),
    )

    try:
        # Token 정보 저장
        await token_dal.insert_token(new_token=new_refresh_token)

        # Login 이력 저장
        await user_login_dal.insert_login_history(
            login_history=schemas.LoginHistorySchema(
                user_id=login_user.id,
                login_time=datetime.now(),
                login_success=True,
                ip_address=request.client.host,
            )
        )

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return ErrorJSONResponse(
            message="로그인을 하는 도중에 문제가 발생하였습니다",
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=1500,
        )
    finally:
        await session.close()

    logger.info(
        f'사용자가 로그인하였습니다. { {"user_id": login_user.id, "email": masking_str(login_request.email), "name": masking_str(login_user.name)} }'
    )

    token_response = schemas.TokenAccessOnlySchema(**new_token.dict())
    # accessToken은 json으로 반환한다
    response = JSONResponse(content=token_response.dict())
    # refreshToken은 Cookie로 반환한다
    response.set_cookie(
        key="refresh_token",
        value=f"{new_token.refresh_token}",
        httponly=True,
        secure=True,
        samesite="none",
    )

    return response


@router.post(
    "/web/logout",
    response_model=schemas.DefaultResponse,
    responses={
        401: {"model": schemas.ErrorResponse},
        403: {"model": schemas.ErrorResponse},
        500: {"model": schemas.ErrorResponse},
    },
)
async def web_logout(
    *,
    user_token: schemas.AuthTokenSchema = Depends(AuthorizeToken()),
    session: AsyncSession = Depends(get_session),
):
    """
    Logout API

    Authorization Header에 포함된 accessToken으로 발급된 토큰을 조회하여 삭제하여 로그아웃을 시킨다
    Cookie에 refreshToken을 삭제한다

    - accessToken은 만료시킬 수 없으므로 토큰의 남은 시간까지는 사용 가능한 문제가 있다
    - redis에 blackList를 생성하여 관리하는 방법으로 이를 해결할 수도 있다
    """

    token_dal = crud.TokenDAL(session=session)

    try:
        if await token_dal.exists(
            user_id=int(user_token.sub), access_token=user_token.access_token
        ):
            await token_dal.delete(
                user_id=int(user_token.sub), access_token=user_token.access_token
            )

            await session.commit()
        else:
            # Token을 찾을 수 없는 경우에는 Logging만 하고 정상 결과를 반환한다
            logger.info(f'사용자 토큰을 찾을 수 없습니다. { {"user_id": user_token.sub} }')
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return ErrorJSONResponse(
            message="토큰 정보를 찾을 수 없습니다",
            success=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=1500,
        )
    finally:
        await session.close()

    logger.info(f'사용자가 로그아웃 하였습니다. { {"user_id": user_token.sub} }')

    response = DefaultJSONResponse(message="로그아웃 하였습니다", success=True)
    response.delete_cookie(key="refresh_token")

    return response
