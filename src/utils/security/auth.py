from utils.security.encryption import Hasher


async def authenticate(plain_password: str, user_password: str) -> bool:
    """
    사용자 비밀번호를 인증 후 결과를 반환한다

    :param plain_password: 로그인 요청 시에 사용자가 전달한 비밀번호
    :param user_password: Database에 저장된 사용자의 비밀번호
    :return: 비밀번호가 일치하여 인증에 통과하였다면 'True'를, 아니라면 'False'를 반환한다
    """

    # 비밀번호가 없는 경우라면 인증을 시도하지 않는다
    if not plain_password or not user_password:
        return False

    if not Hasher.verify_password(plain_password=plain_password,
                                  hashed_password=user_password):
        return False

    return True
