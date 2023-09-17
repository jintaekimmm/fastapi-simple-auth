from sqlalchemy import Column, BigInteger, String, SmallInteger, BINARY, DateTime

from db.base import Base
from models.mixin import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, index=True)
    uuid = Column(BINARY(16), unique=True)
    email = Column(String(255), nullable=False, index=True)
    email_key = Column(String(255), nullable=False, index=True, unique=True)
    name = Column(String(64), default=None)
    mobile = Column(String(255), nullable=True, index=True, unique=True)
    mobile_key = Column(String(255), nullable=True, index=True)
    password = Column(String(128), nullable=True)
    is_active = Column(SmallInteger, default=0)
    provider_id = Column(String(64), index=True)


class UserLoginHistory(Base, TimestampMixin):
    __tablename__ = "user_login_history"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    login_time = Column(DateTime, default=None)
    login_success = Column(SmallInteger, default=0)
    ip_address = Column(BINARY(16))


class SocialUserAccount(Base, TimestampMixin):
    __tablename__ = "social_user_account"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    provider_id = Column(String(64), index=True)
    sub = Column(String(255), index=True)
    name = Column(String(128))
    given_name = Column(String(128))
    family_name = Column(String(128))
