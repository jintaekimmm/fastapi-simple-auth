from typing import List

from slugify import slugify
from sqlalchemy import insert, update, delete
from sqlalchemy.engine import CursorResult
from sqlalchemy.future import select

from db.crud.abstract import DalABC
from models.permissions import Permissions
from models.roles import RolesPermissions, Roles
from schemas.permissions import PermissionCreateUpdateRequestSchema


class PermissionsDAL(DalABC):
    async def list(self) -> List[Permissions]:
        q = select(Permissions)

        result = await self.session.execute(q)
        return result.scalars().all()

    async def insert(self, permission: PermissionCreateUpdateRequestSchema) -> CursorResult:
        q = insert(Permissions).values(**permission.dict())

        result = await self.session.execute(q)
        return result

    async def get(self, perm_id: int) -> Permissions:
        q = select(Permissions).where(Permissions.id == perm_id)

        result = await self.session.execute(q)
        return result.scalars().first()

    async def get_by_name(self, name: List[str]) -> List[Permissions]:
        slug = [slugify(i) for i in name]
        q = select(Permissions).where(Permissions.slug.in_(slug))

        result = await self.session.execute(q)
        return result.scalars().all()

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

    async def get_permissions_relation_roles(self, role_id: int) -> List[Permissions]:
        q = select(Permissions) \
            .join(RolesPermissions, RolesPermissions.permission_id == Permissions.id) \
            .where(RolesPermissions.role_id == role_id)

        result = await self.session.execute(q)
        return result.scalars().all()
