# 랜덤 바이트 시퀀스 생성
import base64
import os


def generate_random_bytes(length: int = 16):
    """
    Random Bytes를 생성한다
    """

    return os.urandom(length)


# 바이트 시퀀스를 base64 문자열로 인코딩
def bytes_to_base64(bytes_data: bytes):
    """
    Bytes를 base64 문자열로 인코딩 한다
    """

    return base64.urlsafe_b64encode(bytes_data).decode("utf-8")


def generate_random_state() -> str:
    """
    Random state를 생성한다
    """

    random_bytes = generate_random_bytes()

    return bytes_to_base64(random_bytes).replace("=", "")
