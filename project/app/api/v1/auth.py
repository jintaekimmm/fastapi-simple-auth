from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud.crud_user import UserDAL
from dependencies.database import get_session
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

    # 개인 정보 암호화 및 패스워드 해싱
    sign_up = SignUpBaseSchema(
        first_name=user_info.first_name,
        last_name=user_info.last_name,
        email=aes.encrypt(user_info.email),
        email_key=Hasher.hmac_sha256(user_info.email),
        mobile=aes.encrypt(user_info.mobile),
        mobile_key=Hasher.hmac_sha256(user_info.mobile),
        password=Hasher.get_password_hash(user_info.password1)
    )

    try:
        await user_dal.insert(sign_up)
        await session.commit()
    except Exception as e:
        print(e)
        await session.rollback()

    finally:
        await session.close()

    return JSONResponse({}, status_code=201)


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

