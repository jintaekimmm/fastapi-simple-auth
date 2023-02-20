class TokenCredentialsException(Exception):
    def __init__(self, message: str = 'Invalid Token'):
        self.message = message


class TokenExpiredException(Exception):
    def __init__(self, message: str = 'Token Expired'):
        self.message = message
