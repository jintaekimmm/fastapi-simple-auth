from typing import List

from slugify import slugify
from sqlalchemy import insert, delete
from sqlalchemy.future import select
from sqlalchemy.orm import aliased

from db.crud.abstract import DalABC
from models.permissions import Permissions
from models.roles import RolesPermissions
from schemas.roles import RolePermissionSchema


class RolesPermissionsDAL(DalABC):
    async def bulk_insert(self, role_perms: List[RolePermissionSchema]):
        unpacked_dict = [i.dict() for i in role_perms]
        q = insert(RolesPermissions).values(unpacked_dict)

        await self.session.execute(q)

    async def insert_by_role_names(self, role_names: List[str]):
        pass

    async def delete_by_role_names(self, role_names: List[str]):
        pass

    async def get_by_role(self, role_id: int) -> List[RolesPermissions]:
        q = select(RolesPermissions) \
            .where(RolesPermissions.role_id == role_id) \
            .execution_options(synchronize_session="fetch")

        result = await self.session.execute(q)
        return result.scalras().all()

    async def delete_by_role(self, role_id: int):
        pass

    async def delete_by_permission_name(self, role_id: int, permission_names: List[str]):
        slugs = [slugify(i) for i in permission_names]
        sub_q = select(Permissions.id).where(Permissions.slug.in_(slugs)).scalar_subquery()

        q = delete(RolesPermissions) \
            .where(RolesPermissions.role_id == role_id) \
            .where(RolesPermissions.permission_id.in_(sub_q)) \
            .execution_options(synchronize_session="fetch")

        await self.session.execute(q)
