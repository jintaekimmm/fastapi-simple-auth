from sqlalchemy import Column, Integer, String, TEXT, UniqueConstraint

from db.base import Base
from models.mixin import TimestampMixin


class Roles(Base, TimestampMixin):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(150), nullable=False, index=True)
    content = Column(TEXT, default=None)
    UniqueConstraint('name', name='name')


class RolesPermissions(Base):
    __tablename__ = 'roles_permissions'

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, nullable=False, index=True)
    permission_id = Column(Integer, nullable=False, index=True)

    UniqueConstraint('role_id', 'permission_id', name='role_permission')
