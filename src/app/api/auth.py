from datetime import datetime

from fastapi import APIRouter, Depends, status, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import TokenCredentialsException
from app.core.responses import CustomJSONResponse
from app.core.utils.masking import masking
from db.crud.crud_token import RefreshTokenDAL
from db.crud.crud_user import UserDAL
from app.core.auth import authenticate, create_new_jwt_token
from dependencies.auth import AuthorizeCookieUser, AuthorizeTokenUser, AuthorizeTokenRefresh, AuthorizeRefreshCookieUser
from dependencies.database import get_session
from schemas.auth import LoginRequestSchema
from app.core.security.encryption import AESCipher, Hasher
from schemas.response import ErrorResponse, DefaultResponse
from schemas.token import CreateTokenSchema, InsertTokenSchema, TokenUser, UpdateTokenSchema, TokenSchema

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/api/login',
             response_model=CreateTokenSchema,
             responses={
                 401: {
                     'model': ErrorResponse
                 },
                 500: {
                     'model': ErrorResponse
                 }
             })
async def api_login(*,
                    request: Request,
                    login_info: LoginRequestSchema,
                    session: AsyncSession = Depends(get_session)):
    """
    User Login API(API Version)

    로그인 정보로 인증 처리 후에 JWT Token을 반환한다

    Login Process
        1. 사용자 인증 정보 확인
        2. AccessToken과 RefreshToken을 쌍으로 발급한다(AccessToken은 10분, RefreshToken은 7일의 만료 시간을 갖는다)
        3. RefreshToken은 `token` 테이블에 저장한다: token 값은 암호화해서 저장한다
    """

    # AES Encryption Instance
    aes = AESCipher()

    # Database Instance
    user_dal = UserDAL(session=session)
    r_token_dal = RefreshTokenDAL(session=session)

    # 암호화된 이메일 검색을 위한 blind index 생성
    email_key = Hasher.hmac_sha256(login_info.email)
    # 사용자 이메일이 존재하는지 확인한다
    user = await user_dal.get_user_from_email(email_key)

    # 로그인 인증
    is_login = await authenticate(user, login_info.password)
    if not is_login:
        logger.info(f'incorrect username or password. { {"email": masking(login_info.email, rate=0.5)} }')
        return CustomJSONResponse(message='Incorrect username or password',
                                  status_code=status.HTTP_401_UNAUTHORIZED)

    # JWT Token 발급
    token = await create_new_jwt_token(sub=str(user.id))
    # refreshToken insert schema 생성
    insert_refresh_token = InsertTokenSchema(user_id=user.id,
                                             access_token=token.access_token,
                                             refresh_token=aes.encrypt(token.refresh_token),
                                             refresh_token_key=Hasher.hmac_sha256(token.refresh_token),
                                             issued_at=datetime.fromtimestamp(int(token.iat)),
                                             expires_at=datetime.fromtimestamp(int(token.refresh_token_expires_in)))

    try:
        # RefreshToken을 저장한다
        await r_token_dal.insert(insert_refresh_token)
        # 마지막 로그인 정보를 업데이트한다
        await user_dal.update_last_login(user_id=user.id, login_ip=request.client.host)

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Failed to select/insert data',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()

    logger.info(f'user login success. { {"user_id": user.id} }')

    return token


@router.post('/web/login',
             response_model=DefaultResponse,
             responses={
                 401: {
                     'model': ErrorResponse
                 },
                 500: {
                     'model': ErrorResponse
                 }
             })
async def web_login(*,
                    request: Request,
                    login_info: LoginRequestSchema,
                    session: AsyncSession = Depends(get_session)):
    """
    User Login API(Web Version)

    로그인 정보로 인증 처리 후에 JWT Token을 cookie(httpOnly)에 넣어서 반환한다

    Login Process
        1. 사용자 인증 정보 확인
        2. AccessToken과 RefreshToken을 쌍으로 발급한다(AccessToken은 10분, RefreshToken은 7일의 만료 시간을 갖는다)
        3. RefreshToken은 `token` 테이블에 저장한다: token 값은 암호화해서 저장한다
    """

    # AES Encryption Instance
    aes = AESCipher()

    # Database Instance
    user_dal = UserDAL(session=session)
    r_token_dal = RefreshTokenDAL(session=session)

    # 암호화된 이메일 검색을 위한 blind index 생성
    email_key = Hasher.hmac_sha256(login_info.email)
    # 사용자 이메일이 존재하는지 확인한다
    user = await user_dal.get_user_from_email(email_key)

    # 로그인 인증
    is_login = await authenticate(user, login_info.password)
    if not is_login:
        logger.info(f'incorrect username or password. { {"username": masking(login_info.email, rate=0.5)} }')
        return CustomJSONResponse(message='Incorrect username or password',
                                  status_code=status.HTTP_401_UNAUTHORIZED)

    # JWT Token 발급
    token = await create_new_jwt_token(sub=str(user.id))
    # refreshToken insert schema 생성
    insert_refresh_token = InsertTokenSchema(user_id=user.id,
                                             access_token=token.access_token,
                                             refresh_token=aes.encrypt(token.refresh_token),
                                             refresh_token_key=Hasher.hmac_sha256(token.refresh_token),
                                             issued_at=datetime.fromtimestamp(int(token.iat)),
                                             expires_at=datetime.fromtimestamp(int(token.refresh_token_expires_in)))

    try:
        # RefreshToken을 저장한다
        await r_token_dal.insert(insert_refresh_token)
        # 마지막 로그인 정보를 업데이트한다
        await user_dal.update_last_login(user_id=user.id, login_ip=request.client.host)

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Failed to select/insert data',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()

    response = CustomJSONResponse(message='success')
    response.set_cookie(key='access_token', value=f'{token.access_token}', httponly=True, secure=True)
    response.set_cookie(key='refresh_token', value=f'{token.refresh_token}', httponly=True, secure=True)

    logger.info(f'user login success. { {"user_id": user.id} }')

    return response


@router.post('/api/logout',
             response_model=DefaultResponse,
             responses={
                 401: {
                     'model': ErrorResponse
                 },
                 404: {
                     'model': ErrorResponse
                 }
             })
async def api_logout(*,
                     token: TokenUser = Depends(AuthorizeTokenUser()),
                     session: AsyncSession = Depends(get_session)):
    """
    User Logout API(API Version)

    Logout Process
        1. RefreshToken을 `token` 테이블에서 삭제한다
    """

    token_dal = RefreshTokenDAL(session=session)

    try:
        # refreshToken이 존재하는지 확인한 후 삭제한다
        if await token_dal.exists(user_id=int(token.sub),
                                  access_token=token.access_token):
            await token_dal.delete(user_id=int(token.sub),
                                   access_token=token.access_token)

            await session.commit()
        else:
            raise Exception('user token not found')

    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Invalid Refresh Token',
                                  status_code=status.HTTP_404_NOT_FOUND)
    finally:
        await session.close()

    logger.info(f'user logout. { {"user_id": int(token.sub)} }')

    return CustomJSONResponse(message='success')


@router.post('/web/logout',
             response_model=DefaultResponse,
             responses={
                 401: {
                     'model': ErrorResponse
                 },
                 404: {
                     'model': ErrorResponse
                 }
             })
async def web_logout(*,
                     token: TokenUser = Depends(AuthorizeCookieUser()),
                     session: AsyncSession = Depends(get_session)):
    """
    User Logout API(Web Version)

    Logout Process
        1. accessToken 유효성 확인
        2. RefreshToken을 `token` 테이블에서 삭제한다
        3. cookie에서 토큰을 삭제한다
    """
    token_dal = RefreshTokenDAL(session=session)

    try:
        # refreshToken이 존재하는지 확인한 후 삭제한다
        if await token_dal.exists(user_id=int(token.sub),
                                  access_token=token.access_token):
            await token_dal.delete(user_id=int(token.sub),
                                   access_token=token.access_token)

            await session.commit()
        else:
            raise ValueError('user token not found')

    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Invalid Refresh Token',
                                  status_code=status.HTTP_404_NOT_FOUND)
    else:
        # Cookie에 accessToken과 refreshToken을 삭제한다
        response = CustomJSONResponse(message='success')
        response.set_cookie(key='access_token', value='', httponly=True, max_age=0)
        response.set_cookie(key='refresh_token', value='', httponly=True, max_age=0)

        logger.info(f'user logout. { {"user_id": int(token.sub)} }')

        return response
    finally:
        await session.close()



@router.post('/api/token/refresh',
             response_model=TokenSchema,
             responses={
                 401: {
                     'model': ErrorResponse
                 },
                 500: {
                     'model': ErrorResponse
                 }
             })
async def api_token_refresh(*,
                            token: TokenUser = Depends(AuthorizeTokenRefresh()),
                            session: AsyncSession = Depends(get_session)):
    """
    JWT Token Refresh API(API Version)

    Refresh Process
        1. DB에서 refreshToken을 가져온다
        2. DB에 저장된 refreshToken과 요청한 refreshToken을 비교
        3. accessToken / refreshToken 신규 발급
        4. DB에 refreshToken 정보 업데이트
    """

    # AES Encryption Instance
    aes = AESCipher()

    # Database Instance
    token_dal = RefreshTokenDAL(session=session)

    token_info = await token_dal.get(user_id=int(token.sub), access_token=token.access_token)

    if not token_info or token.refresh_token != aes.decrypt(token_info.refresh_token):
        logger.info(f'mismatch refresh token { {"user_id": int(token.sub)} }')
        raise TokenCredentialsException()

    # 신규 JWT Token 발급
    new_token = await create_new_jwt_token(sub=token.sub)

    # refreshToken 유효 사간이 'jwt_access_token_expire_minutes' 보다 적게 남은 경우에만 새로운 token을 반환한다
    # 그렇지 않은 경우에는 새로 생성한 refreshToken을 저장하지 않는다
    # Think: 리팩토링의 여지가 남았다. refreshToken의 생성 여부를 결정하는게 아니라 일단 생성한 후에 신규 token의 사용 여부를 결정한다
    # remain_expire_at: timedelta = token_info.expires_at - datetime.now()
    # if int(remain_expire_at.total_seconds() // 60) > settings.jwt_access_token_expire_minutes:
    #     new_token.refresh_token = aes.decrypt(token_info.refresh_token)
    #     new_token.refresh_token_expires_in = str(int(token_info.expires_at.timestamp()))

    # refreshToken update schema 생성
    update_token = UpdateTokenSchema(user_id=int(token.sub),
                                     old_access_token=token.access_token,
                                     new_access_token=new_token.access_token,
                                     refresh_token_key=Hasher.hmac_sha256(new_token.refresh_token),
                                     refresh_token=aes.encrypt(new_token.refresh_token),
                                     expires_at=datetime.fromtimestamp(int(new_token.refresh_token_expires_in)))

    try:
        await token_dal.update(update_token)

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Token update failed',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()

    return TokenSchema(access_token=new_token.access_token,
                       refresh_token=new_token.refresh_token)


@router.post('/web/token/refresh',
             response_model=DefaultResponse,
             responses={
                 401: {
                     'model': ErrorResponse
                 },
                 500: {
                     'model': ErrorResponse
                 }
             })
async def web_token_refresh(*,
                            token: TokenUser = Depends(AuthorizeRefreshCookieUser()),
                            session: AsyncSession = Depends(get_session)):
    """
    JWT Token Refresh API(Web Version)

    Refresh Process
        1. DB에서 refreshToken을 가져온다
        2. DB에 저장된 refreshToken과 요청한 refreshToken을 비교
        3. accessToken / refreshToken 신규 발급
        4. DB에 refreshToken 정보 업데이트
    """

    # AES Encryption Instance
    aes = AESCipher()

    # Database Instance
    token_dal = RefreshTokenDAL(session=session)

    token_info = await token_dal.get(user_id=int(token.sub), access_token=token.access_token)
    if not token_info or token.refresh_token != aes.decrypt(token_info.refresh_token):
        logger.info(f'mismatch refresh token { {"user_id": int(token.sub)} }')
        raise TokenCredentialsException()

    # 신규 JWT Token 발급
    new_token = await create_new_jwt_token(sub=token.sub)

    # refreshToken 유효 사간이 'jwt_access_token_expire_minutes' 보다 적게 남은 경우에만 새로운 token을 반환한다
    # 그렇지 않은 경우에는 새로 생성한 refreshToken을 저장하지 않는다
    # Think: 리팩토링의 여지가 남았다. refreshToken의 생성 여부를 결정하는게 아니라 일단 생성한 후에 신규 token의 사용 여부를 결정한다
    # remain_expire_at: timedelta = token_info.expires_at - datetime.now()
    # if int(remain_expire_at.total_seconds() // 60) > settings.jwt_access_token_expire_minutes:
    #     new_token.refresh_token = aes.decrypt(token_info.refresh_token)
    #     new_token.refresh_token_expires_in = str(int(token_info.expires_at.timestamp()))

    # refreshToken update schema 생성
    update_token = UpdateTokenSchema(user_id=int(token.sub),
                                     old_access_token=token.access_token,
                                     new_access_token=new_token.access_token,
                                     refresh_token_key=Hasher.hmac_sha256(new_token.refresh_token),
                                     refresh_token=aes.encrypt(new_token.refresh_token),
                                     expires_at=datetime.fromtimestamp(int(new_token.refresh_token_expires_in)))

    try:
        await token_dal.update(update_token)

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Token update failed',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        # Cookie에 accessToken을 업데이트한다
        response = CustomJSONResponse(message='success')
        response.set_cookie(key='access_token', value=f'{new_token.access_token}', httponly=True)
        response.set_cookie(key='refresh_token', value=f'{new_token.refresh_token}', httponly=True)

        return response
    finally:
        await session.close()