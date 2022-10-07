from sqlalchemy import Column, Integer, SmallInteger, DateTime, String

from db.base import Base
from models.mixin import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(32), default=None)
    last_name = Column(String(32), default=None)
    email = Column(String(128), nullable=False, index=True)
    email_key = Column(String(128), nullable=False, index=True, unique=True)
    mobile = Column(String(128), nullable=False, index=True, unique=True)
    mobile_key = Column(String(128), nullable=False, index=True)
    password = Column(String(128), nullable=False)
    is_admin = Column(SmallInteger, default=0)
    is_active = Column(SmallInteger, default=0)
    last_login = Column(DateTime, default=None)
