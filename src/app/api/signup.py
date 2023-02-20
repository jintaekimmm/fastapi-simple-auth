from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import CustomJSONResponse
from app.core.utils.masking import masking
from db.crud.crud_user import UserDAL
from dependencies.database import get_session
from schemas.response import ErrorResponse
from schemas.signup import SignupRequestSchema, SignUpBaseSchema
from app.core.security.encryption import AESCipher, Hasher

router = APIRouter(prefix='/v1/signup', tags=['signup'])


@router.post('',
             status_code=status.HTTP_201_CREATED,
             responses={
                 409: {
                     'model': ErrorResponse
                 },
                 500: {
                     'model': ErrorResponse
                 }
             })
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
        logger.info(f'email address is already registered. { {"email": masking(user_info.email, rate=0.5)} }')
        return JSONResponse({'message': 'Email Address is Already Registered'}, status_code=status.HTTP_409_CONFLICT)

    # 암호화된 핸드폰 번호 검색을 위한 blind index 생성
    mobile_key = Hasher.hmac_sha256(user_info.mobile)
    # 동일한 핸드폰 번호가 존재하는지 확인한다
    if await user_dal.exists_mobile(mobile_key):
        logger.info(f'mobile number is already registered. { {"mobile": masking(user_info.mobile, rate=0.5)} }')
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
        logger.exception(e)
        await session.rollback()
        return JSONResponse({'message': 'Failed to insert data'},
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    finally:
        await session.close()

    logger.info(f'signup success. { {"email": masking(user_info.email, rate=0.5), "first_name": masking(user_info.first_name), "last_name": masking(user_info.last_name)} }')
