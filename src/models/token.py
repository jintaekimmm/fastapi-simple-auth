from sqlalchemy import Column, BigInteger, String, Text, DateTime

from db.base import Base
from models.mixin import TimestampMixin


class JWTToken(Base, TimestampMixin):
    __tablename__ = 'jwt_token'

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    access_token = Column(String(255), index=True)
    refresh_token = Column(Text)
    refresh_token_key = Column(String(128), index=True)
    issued_at = Column(DateTime)
    expires_at = Column(DateTime, index=True)
