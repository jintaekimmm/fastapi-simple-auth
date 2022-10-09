from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud.crud_user import UserDAL
from dependencies.database import get_session
from internal.logging import app_logger
from schemas.auth import SignupRequestSchema, SignUpBaseSchema
from security.encryption import AESCipher, Hasher

router = APIRouter(prefix='/v1', tags=['auth'])


@router.post('/signup')
async def signup(user_info: SignupRequestSchema,
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

    finally:
        await session.close()

    return JSONResponse(None, status_code=201)


@router.post('/login')
async def login():
    """
    User Login API
    """

    pass


@router.post('/logout')
async def logout():
    """
    User Logout PAI
    """

    pass

