from sqlalchemy import Column, Integer, UniqueConstraint

from db.base import Base


class UserGroups(Base):
    __tablename__ = 'user_groups'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    group_id = Column(Integer)

    UniqueConstraint('user_id', 'group_id', name='user_groups')
