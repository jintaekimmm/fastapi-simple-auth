from typing import List

from slugify import slugify
from sqlalchemy import insert, delete
from sqlalchemy.future import select

from db.crud.abstract import DalABC
from models.roles import Roles
from models.user import UsersRoles
from schemas.user import UserRolesSchema


class UsersRolesDAL(DalABC):
    async def insert(self, user_role: UserRolesSchema) -> None:
        q = insert(UsersRoles).values(**user_role.dict())

        await self.session.execute(q)

    async def bulk_insert(self, user_roles: List[UserRolesSchema]):
        unpacked_dict = [i.dict() for i in user_roles]
        q = insert(UsersRoles).values(unpacked_dict)

        await self.session.execute(q)

    async def delete(self, user_id: int, role_id: int) -> None:
        q = delete(UsersRoles) \
            .where(UsersRoles.user_id == user_id) \
            .where(UsersRoles.role_id == role_id)

        await self.session.execute(q)

    async def delete_by_role_name(self, user_id: int, role_names: List[str]):
        slugs = [slugify(i) for i in role_names]
        sub_q = select(Roles.id).where(Roles.slug.in_(slugs)).scalar_subquery()

        q = delete(UsersRoles) \
            .where(UsersRoles.user_id == user_id) \
            .where(UsersRoles.role_id.in_(sub_q)) \
            .execution_options(synchronize_session="fetch")

        await self.session.execute(q)

    async def exists_user_relation_role(self, user_id: int, role_id: int) -> bool:
        q = select(UsersRoles) \
            .where(UsersRoles.user_id == user_id) \
            .where(UsersRoles.role_id == role_id)

        result = await self.session.execute(q)
        return bool(result.scalars().all())
