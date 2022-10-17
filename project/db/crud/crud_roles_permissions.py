from typing import List

from slugify import slugify
from sqlalchemy import insert, delete
from sqlalchemy.future import select

from db.crud.abstract import DalABC
from models.permissions import Permissions
from models.roles import RolesPermissions
from schemas.roles import RolePermissionSchema


class RolesPermissionsDAL(DalABC):
    async def bulk_insert(self, role_perms: List[RolePermissionSchema]):
        unpacked_dict = [i.dict() for i in role_perms]
        q = insert(RolesPermissions).values(unpacked_dict)

        await self.session.execute(q)

    async def delete_by_permission_name(self, role_id: int, permission_names: List[str]):
        slugs = [slugify(i) for i in permission_names]
        sub_q = select(Permissions.id).where(Permissions.slug.in_(slugs)).scalar_subquery()

        q = delete(RolesPermissions) \
            .where(RolesPermissions.role_id == role_id) \
            .where(RolesPermissions.permission_id.in_(sub_q)) \
            .execution_options(synchronize_session="fetch")

        await self.session.execute(q)

    async def exists_relation_roles(self, perm_id: int) -> bool:
        q = select(RolesPermissions) \
            .where(RolesPermissions.permission_id == perm_id)

        result = await self.session.execute(q)
        return bool(result.scalars().all())

    async def exists_relation_permissions(self, role_id: int) -> bool:
        q = select(RolesPermissions) \
            .where(RolesPermissions.role_id == role_id)

        result = await self.session.execute(q)
        return bool(result.scalars().all())
