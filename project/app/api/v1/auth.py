from datetime import datetime

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud.crud_token import RefreshTokenDAL, RefreshTokenDAL
from db.crud.crud_user import UserDAL
from app.core.auth import authenticate, create_new_jwt_token
from dependencies.database import get_session
from internal.logging import app_logger
from schemas.auth import LoginRequestSchema
from schemas.signup import SignupRequestSchema, SignUpBaseSchema
from app.core.security.encryption import AESCipher, Hasher
from schemas.token import CreateTokenSchema, InsertTokenSchema

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


@router.post('/login', response_model=CreateTokenSchema)
async def login(*,
                login_info: LoginRequestSchema,
                session: AsyncSession = Depends(get_session)):
    """
    User Login API

    Login Process
        1. 사용자 인증 정보 확인
        2. AccessToken과 RefreshToken을 쌍으로 발급한다(AccessToken은 10분, RefreshToken은 7일의 만료 시간을 갖는다)
        3. RefreshToken은 `token` 테이블에 저장한다: token 값은 암호화 해서 저장한다
         - 이전에 발급한 RefreshToken이 있다면 삭제하고 다시 저장한다
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
                                             refresh_token=aes.encrypt(token.refresh_token),
                                             refresh_token_key=Hasher.hmac_sha256(token.refresh_token),
                                             issued_at=datetime.fromtimestamp(int(token.iat)),
                                             expires_at=datetime.fromtimestamp(int(token.refresh_token_expires_in)))

    # RefreshToken을 저장한다
    try:
        # 저장되어 있는 RefreshToken이 존재한다면 삭제하고, 새로 발급한 token을 저장한다
        if await r_token_dal.exists_by_user_id(user.id):
            await r_token_dal.delete_by_user_id(user.id)

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


@router.post('/logout')
async def logout():
    """
    User Logout PAI

    Logout Process
        1. RefreshToken을 `token` 테이블에서 삭제한다
    """

    pass


@router.post('/token/refresh')
async def token_refresh():
    """
    JWT Token Refresh API

    Refresh Process
        1. token 유효성 및 만료 여부 확인
        2. DB에 저장된 refreshToken과 요청한 refreshToken을 비교(refreshToken은 1개만 유지하는 전략을 가진다)
         - 다르다면 refresh process 종료
        3. accessToken 발급
         - refreshToken은 재발급하지 않는다
    """

    pass
