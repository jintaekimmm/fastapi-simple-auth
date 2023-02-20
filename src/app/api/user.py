from typing import List, Union

from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import internal_server_exception, not_found_exception, not_found_param_exception
from db.crud.crud_permissions import PermissionsDAL
from db.crud.crud_roles import RolesDAL
from db.crud.crud_user import UserDAL
from db.crud.crud_users_roles import UsersRolesDAL
from dependencies.auth import AuthorizeTokenUser
from dependencies.database import get_session
from schemas.permissions import PermissionListResponseSchema, PermissionBaseSchema
from schemas.roles import RoleListResponseSchema, RoleBaseSchema
from schemas.user import UserAssignedRoleRequestSchema, UserAssignedRoleUpdateSchema, UserRolesSchema

router = APIRouter(prefix='/v1', tags=['users'])


@router.get('/users/{user_id}/roles', response_model=RoleListResponseSchema)
async def get_user_roles(*,
                         user_id: int,
                         _=Depends(AuthorizeTokenUser()),
                         session: AsyncSession = Depends(get_session)):
    """
    List roles assigned to a user
    """

    # Database Instance
    user_dal = UserDAL(session=session)
    role_dal = RolesDAL(session=session)

    try:
        # 사용자가 존재하는지 확인한다
        user_info = await user_dal.get(user_id=user_id)
        if not user_info:
            logger.info(f'user not found { {"user_id": user_id} }')
            raise not_found_param_exception(f"user not found")

        role_list = await role_dal.get_roles_relation_users(user_id=user_id)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()

    responses = RoleListResponseSchema(data=[
        RoleBaseSchema(id=role.id,
                       name=role.name,
                       slug=role.slug,
                       content=role.content,
                       created_at=role.created_at,
                       updated_at=role.updated_at)
        for role in role_list
    ])

    return responses


@router.get('/users/{user_id}/permissions', response_model=PermissionListResponseSchema)
async def get_user_permissions(*,
                               user_id: int,
                               _=Depends(AuthorizeTokenUser()),
                               session: AsyncSession = Depends(get_session)):
    """
    List permissions to a user
    """

    # Database Instance
    user_dal = UserDAL(session=session)
    permission_dal = PermissionsDAL(session=session)

    try:
        # 사용자가 존재하는지 확인한다
        user_info = await user_dal.get(user_id=user_id)
        if not user_info:
            logger.info(f'user not found { {"user_id": user_id} }')
            raise not_found_param_exception(f"user not found")

        perm_list = await permission_dal.get_roles_relation_users(user_id=user_id)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()

    responses = PermissionListResponseSchema(data=[
        PermissionBaseSchema(id=perm.id,
                             name=perm.name,
                             slug=perm.slug,
                             content=perm.content,
                             created_at=perm.created_at,
                             updated_at=perm.updated_at)
        for perm in perm_list])

    return responses


@router.post('/users/{user_id}/roles')
async def user_assigned_role(*,
                             user_id: int,
                             role: UserAssignedRoleRequestSchema,
                             _=Depends(AuthorizeTokenUser()),
                             session: AsyncSession = Depends(get_session)):
    """
    Add a user Role assignment
    """

    # Database Instance
    user_dal = UserDAL(session=session)
    role_dal = RolesDAL(session=session)
    user_role_dal = UsersRolesDAL(session=session)

    try:
        # 사용자가 존재하는지 확인한다
        user_info = await user_dal.get(user_id=user_id)
        if not user_info:
            logger.info(f'user not found { {"user_id": user_id} }')
            raise not_found_param_exception(f"user not found")

        # role이 존재하는지 확인한다
        role_info = await role_dal.get_by_name(role_name=role.role)
        if not role_info:
            msg = role.role
            logger.info(f"unable to assign role to user. because '{msg}' not found role. { {'user_id': user_id} }")
            raise not_found_param_exception(f"unable to assign role to user. "
                                            f"because '{msg}' not found role")

        try:
            await user_role_dal.insert(user_role=UserRolesSchema(user_id=user_id, role_id=role_info.id))
        except IntegrityError as e:
            logger.exception(e)
            await session.rollback()
            return JSONResponse({"message": f"user has already been assigned role {role.role}"},
                                status_code=status.HTTP_409_CONFLICT)

        await session.commit()
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()

    logger.info(f'user roles hava been updated. { {"user_id": user_id} }')

    return JSONResponse({"message": "user roles have been updated"})


@router.put('/users/{user_id}/roles', response_model=RoleListResponseSchema)
async def update_user_assigned_roles(*,
                                     user_id: int,
                                     role_info: UserAssignedRoleUpdateSchema,
                                     _=Depends(AuthorizeTokenUser()),
                                     session: AsyncSession = Depends(get_session)):
    """
    Update user roles assigned
    """

    # Database Instance
    user_dal = UserDAL(session=session)
    role_dal = RolesDAL(session=session)
    user_role_dal = UsersRolesDAL(session=session)
    # roles 요청 목록 생성
    roles = role_info.roles.copy()

    try:
        # 사용자가 존재하는지 확인한다
        user_info = await user_dal.get(user_id=user_id)
        if not user_info:
            logger.info(f'user not found { {"user_id": user_id} }')
            raise not_found_param_exception(f"user not found")

        # 요청한 role이 존재하는지 확인한다
        roles_result = await role_dal.get_by_names(names=roles)
        not_found_roles = set(roles).difference(set(i.name for i in roles_result))
        if not_found_roles:
            msg = ', '.join(not_found_roles)
            logger.info(f"can't assigned user. because '{msg}' roles not found. { {'user_id': user_id} }")
            raise not_found_param_exception(f"can't assigned user. "
                                            f"because '{msg} roles not found")

        user_role_list = await role_dal.get_roles_relation_users(user_id=user_id)

        # Update(request) payload에 존재하지 않는 것은 삭제한다
        delete_roles = set(i.name for i in user_role_list).difference(set(roles))
        # Database에 존재하지 않는 것은 추가한다
        insert_roles = set(roles).difference(set(i.name for i in user_role_list))

        if delete_roles:
            await user_role_dal.delete_by_role_name(user_id=user_id, role_names=list(delete_roles))

        if insert_roles:
            found_roles = await role_dal.get_by_names(list(insert_roles))
            await user_role_dal.bulk_insert(user_roles=[UserRolesSchema(user_id=user_id, role_id=i.id)
                                                        for i in found_roles])

        await session.commit()

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        raise internal_server_exception
    else:
        role_list = await role_dal.get_roles_relation_users(user_id=user_id)
    finally:
        await session.close()

    responses = RoleListResponseSchema(data=[
        RoleBaseSchema(id=role.id,
                       name=role.name,
                       slug=role.slug,
                       content=role.content,
                       created_at=role.created_at,
                       updated_at=role.updated_at)
        for role in role_list
    ])

    return responses


@router.delete('/users/{user_id}/roles/{role_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_assigned_role(*,
                                    user_id: int,
                                    role_id: int,
                                    _=Depends(AuthorizeTokenUser()),
                                    session: AsyncSession = Depends(get_session)):
    """
    Remove a user role assigned
    """

    # Database Instance
    user_dal = UserDAL(session=session)
    user_role_dal = UsersRolesDAL(session=session)

    try:
        # 사용자가 존재하는지 확인한다
        user_info = await user_dal.get(user_id=user_id)
        if not user_info:
            logger.info(f'user not found { {"user_id": user_id} }')
            raise not_found_param_exception(f"user not found")

        # user에 role이 할당되어 있는지 확인한다
        if not await user_role_dal.exists_user_relation_role(user_id=user_id, role_id=role_id):
            logger.info(f'user has no role assgined. { {"user_id": user_id, "role_id": role_id} }')
            return JSONResponse({'message': 'user has no role assigned'}, status_code=status.HTTP_404_NOT_FOUND)

        await user_role_dal.delete(user_id=user_id, role_id=role_id)

        await session.commit()
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()


@router.get('/users/{user_id}/has/role')
async def has_role_for_user(*,
                            user_id: int,
                            roles: Union[List[str], None] = Query(default=None),
                            _=Depends(AuthorizeTokenUser()),
                            session: AsyncSession = Depends(get_session)):
    """
    Check user has a roles
    """

    # Database Instance
    user_dal = UserDAL(session=session)
    role_dal = RolesDAL(session=session)

    try:
        # 사용자가 존재하는지 확인한다
        user_info = await user_dal.get(user_id=user_id)
        if not user_info:
            logger.info(f'user not found { {"user_id": user_id} }')
            raise not_found_param_exception(f"user not found")

        # role이 존재하는지 확인한다
        role_result = await role_dal.get_by_names(roles)
        if not role_result:
            logger.info(f'role not found { {"roles": roles} }')
            raise not_found_param_exception(f"role not found")

        # 사용자에게 할당된 role중에 요청 목록과 한개라도 일치하는 것이 있다면 STATUS 200 반환
        user_has_roles = await role_dal.get_roles_relation_users(user_id=user_id)
        if any(user.name in roles for user in user_has_roles):
            return JSONResponse({'result': True})

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()

    return JSONResponse({'result': False}, status_code=status.HTTP_404_NOT_FOUND)


@router.get('/users/{user_id}/has/permission')
async def has_permission_for_user(*,
                                  user_id: int,
                                  permissions: Union[List[str], None] = Query(default=None),
                                  _=Depends(AuthorizeTokenUser()),
                                  session: AsyncSession = Depends(get_session)):
    """
    check user has a permissions
    """

    # Database Instance
    user_dal = UserDAL(session=session)
    perm_dal = PermissionsDAL(session=session)

    try:
        # 사용자가 존재하는지 확인한다
        user_info = await user_dal.get(user_id=user_id)
        if not user_info:
            logger.info(f'user not found { {"user_id": user_id} }')
            raise not_found_param_exception(f"user not found")

        # permission이 존재하는지 확인한다
        perm_result = await perm_dal.get_by_names(permissions)
        if not perm_result:
            logger.info(f'permission not found { {"permissions": permissions} }')
            raise not_found_param_exception(f"permission not found")

        # 사용자에게 할당된 permission중에 요청 목록과 한개라도 일치하는 것이 있다면 STATUS 200 반환
        user_has_perms = await perm_dal.get_roles_relation_users(user_id=user_id)
        if any(user.name in permissions for user in user_has_perms):
            return JSONResponse({'result': True})

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(e)
        await session.rollback()
        raise internal_server_exception
    finally:
        await session.close()

    return JSONResponse({'result': False}, status_code=status.HTTP_404_NOT_FOUND)
