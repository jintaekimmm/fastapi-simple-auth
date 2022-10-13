from fastapi import APIRouter

router = APIRouter(prefix='/v1/roles', tags=['roles'])


@router.get('')
async def list_roles():
    """
    All List Roles API
    """

    pass


@router.post('')
async def create_roles():
    """
    Create Roles API
    """
    pass


@router.get('/{role_id}')
async def get_roles(role_id: int):
    """
    Get Roles API
    """
    pass


@router.put('/{role_id}')
async def update_roles(role_id: int):
    """
    Update Roles API
    """
    pass


@router.delete('/{role_id}')
async def delete_roles(role_id: int):
    """
    Delete Roles API
    """
    pass
