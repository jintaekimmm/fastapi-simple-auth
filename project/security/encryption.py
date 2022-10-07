import base64
import hashlib
import hmac

from Crypto import Random
from Crypto.Cipher import AES
from passlib.context import CryptContext

from internal.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hasher:
    __blind_index_key = settings.blind_index_key

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

    @classmethod
    def hmac_sha256(cls, plain_text):
        h = hmac.new(cls.__blind_index_key.encode('utf-8'), plain_text.encode('utf-8'), hashlib.sha256)
        return h.hexdigest()


class AESCipher:
    def __init__(self):
        self.bs = 32
        self.key = hashlib.sha256(self._str_to_bytes(settings.aes_encrypt_key)).digest()

    @staticmethod
    def _str_to_bytes(data):
        u_type = type(b''.decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * self._str_to_bytes(chr(self.bs - len(s) % self.bs))

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

    def encrypt(self, raw):
        raw = self._pad(self._str_to_bytes(raw))
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')



