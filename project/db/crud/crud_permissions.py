from typing import List

from sqlalchemy import insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.permissions import Permissions
from models.roles import RolesPermissions, Roles
from schemas.permissions import PermissionCreateUpdateRequestSchema


class PermissionsDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[Permissions]:
        q = select(Permissions)

        result = await self.session.execute(q)
        return result.scalars().all()

    async def insert(self, permission: PermissionCreateUpdateRequestSchema) -> None:
        q = insert(Permissions).values(**permission.dict())
        await self.session.execute(q)

    async def get(self, perm_id: int) -> Permissions:
        q = select(Permissions).where(Permissions.id == perm_id)

        result = await self.session.execute(q)
        return result.scalars().first()

    async def update(self, perm_id: int, permission: PermissionCreateUpdateRequestSchema) -> None:
        q = update(Permissions) \
            .where(Permissions.id == perm_id) \
            .values(**permission.dict()) \
            .execution_options(synchronize_session="fetch")

        await self.session.execute(q)

    async def delete(self, perm_id: int):
        q = delete(Permissions) \
            .where(Permissions.id == perm_id) \
            .execution_options(synchronize_session="fetch")

        await self.session.execute(q)

    async def exists_relation_roles(self, perm_id: int) -> bool:
        q = select(RolesPermissions) \
            .where(RolesPermissions.permission_id == perm_id)

        result = await self.session.execute(q)
        return bool(result.scalars().all())

    async def get_roles_relation_permissions(self, perm_id: int):
        q = select(Roles.name) \
            .join(RolesPermissions, RolesPermissions.role_id == Roles.id) \
            .join(Permissions.id, Permissions.id == RolesPermissions.permission_id) \
            .where(Permissions.id == perm_id)

        result = await self.session.execute(q)
        return result.scalars().all()