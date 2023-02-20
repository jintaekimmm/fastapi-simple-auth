from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from slugify import slugify
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import CustomJSONResponse
from db.crud.crud_permissions import PermissionsDAL
from db.crud.crud_roles import RolesDAL
from db.crud.crud_roles_permissions import RolesPermissionsDAL
from dependencies.auth import AuthorizeTokenUser
from dependencies.database import get_session
from schemas.permissions import PermissionBaseSchema
from schemas.response import ErrorResponse, DefaultResponse
from schemas.roles import RoleBaseSchema, RoleListResponseSchema, RoleCreateUpdateRequestSchema, RolePermissionSchema, \
    RolesAndPermissionResponseSchema
from schemas.token import TokenUser

router = APIRouter(prefix='/roles', tags=['roles'])


@router.get('',
            response_model=RoleListResponseSchema,
            responses={
                401: {
                    'model': ErrorResponse
                },
                500: {
                    'model': ErrorResponse
                }
            })
async def list_roles(*,
                     _: TokenUser =Depends(AuthorizeTokenUser()),
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
        logger.exception(e)
        return CustomJSONResponse(message='Internal Server Error',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return responses


@router.post('',
             response_model=DefaultResponse,
             responses={
                 400: {
                     'model': ErrorResponse
                 },
                 401: {
                     'model': ErrorResponse
                 },
                 409: {
                     'model': ErrorResponse
                 },
                 500: {
                     'model': ErrorResponse
                 }
             })
async def create_roles(*,
                       role_info: RoleCreateUpdateRequestSchema,
                       _: TokenUser = Depends(AuthorizeTokenUser()),
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
            logger.info(f"can't create roles. because '{msg}' not found permissions { {'role_name': role_info.name} }")
            return CustomJSONResponse(message=f"can't create roles. "
                                              f"because '{msg}' not found permissions",
                                      status_code=status.HTTP_400_BAD_REQUEST)

        # Insert role
        try:
            role_result = await role_dal.insert(role=role_info)
        except IntegrityError as e:
            logger.exception(e)
            await session.rollback()
            return JSONResponse({'message': 'role already exists'}, status_code=status.HTTP_409_CONFLICT)

        # 생성한 Role Id를 가져온다
        try:
            role_id = role_result.inserted_primary_key[0]
        except IndexError as e:
            logger.exception(e)
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
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Internal Server Error',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()

    # Add Location Header
    new_resource_uri = router.url_path_for('get_roles', role_id=role_id)
    headers = {'Location': new_resource_uri}

    return CustomJSONResponse(message=None,
                              status_code=status.HTTP_201_CREATED,
                              headers=headers)


@router.get('/{role_id}',
            response_model=RolesAndPermissionResponseSchema,
            responses={
                401: {
                    'model': ErrorResponse
                },
                404: {
                    'model': ErrorResponse
                },
                500: {
                    'model': ErrorResponse
                }
            })
async def get_roles(*,
                    role_id: int,
                    _: TokenUser = Depends(AuthorizeTokenUser()),
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
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Internal Server Error',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        if not role:
            logger.info(f'role not found. { {"role_id": role_id} }')
            return CustomJSONResponse(message='Role not found',
                                      status_code=status.HTTP_404_NOT_FOUND)
    finally:
        await session.close()

    response = RolesAndPermissionResponseSchema(id=role.id,
                                                name=role.name,
                                                content=role.content,
                                                created_at=role.created_at,
                                                updated_at=role.updated_at,
                                                permissions=[PermissionBaseSchema(name=perm.name,
                                                                                  content=perm.content,
                                                                                  created_at=perm.created_at,
                                                                                  updated_at=perm.updated_at)
                                                             for perm in perms])

    return response

@router.put('/{role_id}',
            response_model=RolesAndPermissionResponseSchema,
            responses={
                400: {
                    'model': ErrorResponse
                },
                401: {
                    'model': ErrorResponse
                },
                404: {
                    'model': ErrorResponse
                },
                409: {
                    'model': ErrorResponse
                },
                500: {
                    'model': ErrorResponse
                }
            })
async def update_roles(*,
                       role_id: int,
                       role_info: RoleCreateUpdateRequestSchema,
                       _: TokenUser = Depends(AuthorizeTokenUser()),
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
            logger.info(f"can't create roles. because '{msg}' not found permissions. { {'role_id': role_id, 'role_name': role_info.name} }")
            return CustomJSONResponse(message=f"can't create roles. "
                                              f"because '{msg}' not found permissions",
                                      status_code=status.HTTP_400_BAD_REQUEST)

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
        logger.exception(e)
        await session.rollback()
        return JSONResponse({"message": f"role '{role_info.name}' is already exists"},
                            status_code=status.HTTP_409_CONFLICT)

    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Internal Server Error',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        role = await role_dal.get(role_id=role_id)
        if not role:
            return CustomJSONResponse('Role not found',
                                      status_code=status.HTTP_404_NOT_FOUND)
        perms = await perm_dal.get_permissions_relation_roles(role_id=role_id)
    finally:
        await session.close()

    response = RolesAndPermissionResponseSchema(id=role.id,
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

    return response


@router.delete('/{role_id}',
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   401: {
                       'model': ErrorResponse
                   },
                   403: {
                       'model': ErrorResponse
                   },
                   404: {
                       'model': ErrorResponse
                   },
                   500: {
                       'model': ErrorResponse
                   }
               })
async def delete_roles(*,
                       role_id: int,
                       _: TokenUser = Depends(AuthorizeTokenUser()),
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
            return CustomJSONResponse(message='Role not found',
                                      status_code=status.HTTP_404_NOT_FOUND)
        # Role과 연결된 Permission이 존재하는지 확인한다
        if await role_perm_dal.exists_relation_permissions(role_id=role_id):
            # Role과 연결된 Permission의 이름을 가져온다
            result = await perm_dal.get_permissions_relation_roles(role_id=role_id)
            msg = ', '.join([i.name for i in result])
            if msg:
                logger.info(f"can't delete role. because '{msg}' currently assigned to this role. { {'role_id': role_id} }")
                return CustomJSONResponse(message=f"can't delete role. "
                                                  f"because '{msg}' currently assigned to this role",
                                          status_code=status.HTTP_403_FORBIDDEN)

        await role_dal.delete(role_id=role_id)

        await session.commit()

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        return CustomJSONResponse(message='Internal Server Error',
                                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()
