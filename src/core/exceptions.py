

class TokenCredentialsException(Exception):
    def __init__(self, message: str = '인증 정보가 일치하지 않습니다'):
        self.message = message


class TokenExpiredException(Exception):
    def __init__(self, message: str = '인증이 만료되었습니다'):
        self.message = message
