from fastapi import HTTPException, status

# Exception 4xx
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid Token"
)

token_expired_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token Expired"
)

not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail='Not Found'
)


def delete_denied_exception(msg: str):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=msg
    )


# Exception 5xx
internal_server_exception = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail='Internal Server Error'
)