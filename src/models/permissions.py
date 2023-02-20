from sqlalchemy import Column, Integer, String, TEXT, UniqueConstraint

from db.base import Base
from models.mixin import TimestampMixin


class Permissions(Base, TimestampMixin):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(150), nullable=False, index=True)
    content = Column(TEXT, default=None)
    UniqueConstraint('name', name='name')

