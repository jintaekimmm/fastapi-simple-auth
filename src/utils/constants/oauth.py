from enum import Enum


class ProviderID(str, Enum):
    LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"
    NAVER = "NAVER"
