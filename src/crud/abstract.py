from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABCMeta


class DalABC(metaclass=ABCMeta):
    def __init__(self, session: AsyncSession):
        self.session = session
