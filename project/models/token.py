from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Text

from db.base import Base


class Token(Base):
    __tablename__ = 'token'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    access_token = Column(String(255), index=True)
    refresh_token = Column(Text)
    refresh_token_key = Column(String(128), index=True)
    issued_at = Column(DateTime)
    expires_at = Column(DateTime, index=True)
