from sqlalchemy import Column, Integer, String

from db.base import Base


class Groups(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150))
