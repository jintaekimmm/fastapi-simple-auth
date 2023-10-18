from abc import ABC
from dataclasses import dataclass


@dataclass
class UserProfile(ABC):
    """사용자 프로필 정보를 담는 클래스"""

    id: str = ""
    email: str = ""
    nickname: str = ""
    gender: str = ""
    age: str = ""
    birthday: str = ""
    profile_image: str = ""
    name: str = ""
    mobile: str = ""

    async def mapping_data(self, body: dict):
        """
        프로필 데이터를 바인딩한다
        """

        raise NotImplementedError
