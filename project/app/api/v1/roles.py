from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from slugify import slugify
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import internal_server_exception, bad_request_param_exception, not_found_exception, \
    delete_denied_exception
from db.crud.crud_permissions import PermissionsDAL
from db.crud.crud_roles import RolesDAL
from db.crud.crud_roles_permissions import RolesPermissionsDAL
from dependencies.auth import AuthorizeTokenUser
from dependencies.database import get_session
from internal.logging import app_logger
from schemas.permissions import PermissionBaseSchema
from schemas.roles import RoleBaseSchema, RoleListResponseSchema, RoleCreateUpdateRequestSchema, RolePermissionSchema, \
    RolesAndPermissionResponseSchema

router = APIRouter(prefix='/v1/roles', tags=['roles'])


@router.get('')
async def list_roles(*,
                     _=Depends(AuthorizeTokenUser()),
                     session: AsyncSession = Depends(get_session)):
    """
    All List Roles API
    """

    # Database Instance
    role_dal = RolesDAL(session=session)

    try:
        # TODO: Pagination
        role_list = await role_dal.list()

        responses = RoleListResponseSchema(data=[
            RoleBaseSchema(id=role.id,
                           name=role.name,
                           slug=role.slug,
                           content=role.content,
                           created_at=role.created_at,
                           updated_at=role.updated_at)
            for role in role_list
        ])
    except Exception as e:
        app_logger.error(e)
        raise internal_server_exception

    return responses


@router.post('')
async def create_roles(*,
                       role_info: RoleCreateUpdateRequestSchema,
                       _=Depends(AuthorizeTokenUser()),
                       session: AsyncSession = Depends(get_session)):
    """
    Create Roles API
    """

    # Database Instance
    role_dal = RolesDAL(session=session)
    perm_dal = PermissionsDAL(session=session)
    role_perm_dal = RolesPermissionsDAL(session=session)

    # Slug 생성
    role_info.slug = slugify(role_info.name)
    # permissions 요청 목록 생성
    permissions = [perm.name for perm in role_info.permissions]

    try:
        # 요청 목록과 저장된 목록을 비교한다
        perm_result = await perm_dal.get_by_names(permissions)
        not_found_perm = set(permissions).difference(set(i.name for i in perm_result))
        if not_found_perm:
            msg = ', '.join(not_found_perm)
            raise bad_request_param_exception(f"can't create roles. "
                                              f"because '{msg}' not found permissions")

        # Insert role
        try:
            role_result = await role_dal.insert(role=role_info)
        except IntegrityError:
            await session.rollback()
            return JSONResponse({'message': 'role already exists'}, status_code=status.HTTP_409_CONFLICT)

        # 생성한 Role Id를 가져온다
        try:
            role_id = role_result.inserted_primary_key[0]
        except IndexError:
            await session.rollback()
            return JSONResponse({'message': 'role create failed'}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Insert Role - Permission Relation
        insert_role_perm = [RolePermissionSchema(role_id=role_id, permission_id=i.id) for i in perm_result]
        if insert_role_perm:
            await role_perm_dal.bulk_insert(insert_role_perm)

        await session.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()

    # Add Location Header
    new_resource_uri = router.url_path_for('get_roles', role_id=role_id)
    headers = {'Location': new_resource_uri}
    return JSONResponse(None, status_code=status.HTTP_201_CREATED, headers=headers)


@router.get('/{role_id}', response_model=RolesAndPermissionResponseSchema)
async def get_roles(*,
                    role_id: int,
                    _=Depends(AuthorizeTokenUser()),
                    session: AsyncSession = Depends(get_session)):
    """
    Get Roles API
    """

    # Database Instance
    role_dal = RolesDAL(session=session)
    perm_dal = PermissionsDAL(session=session)

    try:
        role = await role_dal.get(role_id=role_id)
        perms = await perm_dal.get_permissions_relation_roles(role_id=role_id)
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        raise internal_server_exception
    else:
        if not role:
            raise not_found_exception
    finally:
        await session.close()

    return RolesAndPermissionResponseSchema(
        id=role.id,
        name=role.name,
        content=role.content,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=[PermissionBaseSchema(name=perm.name,
                                          content=perm.content,
                                          created_at=perm.created_at,
                                          updated_at=perm.updated_at)
                     for perm in perms]
    )


@router.put('/{role_id}')
async def update_roles(*,
                       role_id: int,
                       role_info: RoleCreateUpdateRequestSchema,
                       _=Depends(AuthorizeTokenUser()),
                       session: AsyncSession = Depends(get_session)):
    """
    Update Roles API
    """

    # Database Instance
    role_dal = RolesDAL(session=session)
    perm_dal = PermissionsDAL(session=session)
    role_perm_dal = RolesPermissionsDAL(session=session)

    # Slug 생성
    role_info.slug = slugify(role_info.name)
    # permissions 요청 목록 생성
    permissions = [perm.name for perm in role_info.permissions]

    try:
        # 요청한 permission이 존재하는지 확인한다
        perm_result = await perm_dal.get_by_names(permissions)
        not_found_perm = set(permissions).difference(set(i.name for i in perm_result))
        if not_found_perm:
            msg = ', '.join(not_found_perm)
            raise bad_request_param_exception(f"can't create roles. "
                                              f"because '{msg}' not found permissions")

        role_perm_list = await perm_dal.get_permissions_relation_roles(role_id=role_id)

        # Update(request) payload에 존재하지 않는 것은 삭제한다
        delete_perm = set(i.name for i in role_perm_list).difference(set(permissions))
        # Database에 존재하지 않는 것은 추가한다
        insert_perm = set(permissions).difference(set(i.name for i in role_perm_list))

        await role_dal.update(role_id=role_id, role=role_info)
        if delete_perm:
            await role_perm_dal.delete_by_permission_name(role_id=role_id, permission_names=list(delete_perm))

        if insert_perm:
            found_perm = await perm_dal.get_by_names(list(insert_perm))
            await role_perm_dal.bulk_insert(role_perms=[RolePermissionSchema(role_id=role_id, permission_id=i.id)
                                                        for i in found_perm])

        await session.commit()
    except IntegrityError as e:
        app_logger.error(e)
        await session.rollback()
        return JSONResponse({"message": f"role '{role_info.name}' is already exists"},
                            status_code=status.HTTP_409_CONFLICT)

    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        raise internal_server_exception
    else:
        role = await role_dal.get(role_id=role_id)
        if not role:
            raise not_found_exception
        perms = await perm_dal.get_permissions_relation_roles(role_id=role_id)
    finally:
        await session.close()

    return RolesAndPermissionResponseSchema(
        id=role.id,
        name=role.name,
        content=role.content,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=[PermissionBaseSchema(name=perm.name,
                                          content=perm.content,
                                          created_at=perm.created_at,
                                          updated_at=perm.updated_at)
                     for perm in perms]
    )


@router.delete('/{role_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_roles(*,
                       role_id: int,
                       _=Depends(AuthorizeTokenUser()),
                       session: AsyncSession = Depends(get_session)):
    """
    Delete Roles API
    """

    # Database Instnace
    role_dal = RolesDAL(session=session)
    perm_dal = PermissionsDAL(session=session)
    role_perm_dal = RolesPermissionsDAL(session=session)

    try:
        role = await role_dal.get(role_id=role_id)
        if not role:
            raise not_found_exception
        # Role과 연결된 Permission이 존재하는지 확인한다
        if await role_perm_dal.exists_relation_permissions(role_id=role_id):
            # Role과 연결된 Permission의 이름을 가져온다
            result = await perm_dal.get_permissions_relation_roles(role_id=role_id)
            msg = ', '.join([i.name for i in result])
            if msg:
                delete_denied_exception(f"can't delete role. "
                                        f"because '{msg}' currently assigned to this role")

        await role_dal.delete(role_id=role_id)

        await session.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        app_logger.error(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()
