from datetime import datetime

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud.crud_token import RefreshTokenDAL
from db.crud.crud_user import UserDAL
from app.core.auth import authenticate, create_new_jwt_token, create_access_token, new_refresh_token_expires
from dependencies.auth import AuthorizeCookieUser, AuthorizeTokenUser, credentials_exception
from dependencies.database import get_session
from internal.logging import app_logger
from schemas.auth import LoginRequestSchema
from schemas.signup import SignupRequestSchema, SignUpBaseSchema
from app.core.security.encryption import AESCipher, Hasher
from schemas.token import CreateTokenSchema, InsertTokenSchema, CookieTokenSchema, TokenUser

router = APIRouter(prefix='/v1', tags=['auth'])


@router.post('/signup')
async def signup(*,
                 user_info: SignupRequestSchema,
                 session: AsyncSession = Depends(get_session)):
    """
    User SignUp API
    """

    # AES Encryption Instance
    aes = AESCipher()
    # Database Instance
    user_dal = UserDAL(session=session)

    # 암호화된 이메일 검색을 위한 blind index 생성
    email_key = Hasher.hmac_sha256(user_info.email)
    # 동일한 이메일이 존재하는지 확인한다
    if await user_dal.exists_email(email_key):
        return JSONResponse({'message': 'Email Address is Already Registered'}, status_code=status.HTTP_409_CONFLICT)

    # 암호화된 핸드폰 번호 검색을 위한 blind index 생성
    mobile_key = Hasher.hmac_sha256(user_info.mobile)
    # 동일한 핸드폰 번호가 존재하는지 확인한다
    if await user_dal.exists_mobile(mobile_key):
        return JSONResponse({'message': 'Mobile Number is Already Registered'}, status_code=status.HTTP_409_CONFLICT)

    # 개인 정보 암호화 및 패스워드 해싱
    sign_up = SignUpBaseSchema(
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        email=aes.encrypt(user_info.email),
        email_key=email_key,
        mobile=aes.encrypt(user_info.mobile),
        mobile_key=mobile_key,
        password=Hasher.get_password_hash(user_info.password1),
        is_active=1
    )

    # 사용자 데이터 저장
    try:
        await user_dal.insert(sign_up)
        await session.commit()
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        return JSONResponse({'message': 'Failed to insert data'},
                            status_code=status.HTTP_500_UNAUTHORIZED)

    finally:
        await session.close()

    return JSONResponse(None,
                        status_code=201)


@router.post('/api/login', response_model=CreateTokenSchema)
async def api_login(*,
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
        return JSONResponse({'message': 'Incorrect username or password.'},
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

    # RefreshToken을 저장한다
    try:
        await r_token_dal.insert(insert_refresh_token)
        await session.commit()
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        return JSONResponse({'message': 'Failed to select/insert data'},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()

    return token


@router.post('/web/login')
async def web_login(*,
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
        return JSONResponse({'message': 'Incorrect username or password.'},
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

    # RefreshToken을 저장한다
    try:
        await r_token_dal.insert(insert_refresh_token)
        await session.commit()
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        return JSONResponse({'message': 'Failed to select/insert data'},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()

    response = JSONResponse({'message': 'login success'})
    response.set_cookie(key='access_token', value=f'{token.access_token}', httponly=True)
    response.set_cookie(key='refresh_token', value=f'{token.refresh_token}', httponly=True)

    return response


@router.post('/api/logout')
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
    except ValueError as e:
        await session.rollback()
        return JSONResponse({'message': str(e)},
                            status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        return JSONResponse({'message': 'Invalid Refresh Token'},
                            status_code=status.HTTP_404_NOT_FOUND)
    finally:
        await session.close()

    return JSONResponse({'message': 'logout success'})


@router.post('/web/logout')
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
    except ValueError as e:
        await session.rollback()
        return JSONResponse({'message': str(e)},
                            status_code=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        return JSONResponse({'message': 'Token Expired fail'},
                            status_code=status.HTTP_404_NOT_FOUND)
    else:
        # Cookie에 accessToken과 refreshToken을 삭제한다
        response = JSONResponse({'message': 'logout success'})
        response.set_cookie(key='access_token', value='', httponly=True, max_age=0)
        response.set_cookie(key='refresh_token', value='', httponly=True, max_age=0)

        return response
    finally:
        await session.close()


@router.post('/api/token/refresh')
async def api_token_refresh(*,
                            token: TokenUser = Depends(AuthorizeTokenUser()),
                            session: AsyncSession = Depends(get_session)):
    """
    JWT Token Refresh API(API Version)

    Refresh Process
        1. DB에서 refreshToken을 가져온다
        2. DB에 저장된 refreshToken과 요청한 refreshToken을 비교
         - 다르다면 refresh process 종료
        3. accessToken 발급
         - refreshToken의 만료시간을 현재 시간 기준으로 업데이트한다
    """

    pass


@router.post('/web/token/refresh')
async def web_token_refresh(*,
                            token: TokenUser = Depends(AuthorizeCookieUser()),
                            session: AsyncSession = Depends(get_session)):
    """
    JWT Token Refresh API(Web Version)

    Refresh Process
        1. DB에서 refreshToken을 가져온다
        2. DB에 저장된 refreshToken과 요청한 refreshToken을 비교
         - 다르다면 refresh process 종료
        3. accessToken 발급
         - refreshToken의 만료시간을 현재 시간 기준으로 업데이트한다
    """

    # AES Encryption Instance
    aes = AESCipher()

    # Database Instance
    token_dal = RefreshTokenDAL(session=session)

    token_info = await token_dal.get(user_id=int(token.sub), access_token=token.access_token)
    if not token_info or token.refresh_token != aes.decrypt(token_info.refresh_token):
        raise credentials_exception

    new_token = await create_access_token(sub=token.sub)
    new_access_token = new_token.token

    try:
        await token_dal.update(user_id=int(token.sub),
                               old_access_token=token.access_token,
                               new_access_token=new_access_token,
                               expires_at=new_refresh_token_expires())

        await session.commit()
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        return JSONResponse({'message': 'Token Update failed'},
                            status_code=status.HTTP_404_NOT_FOUND)
    else:
        # Cookie에 accessToken을 업데이트한다
        response = JSONResponse({'message': 'refresh success'})
        response.set_cookie(key='access_token', value=f'{new_access_token}', httponly=True)

        return response
    finally:
        await session.close()

