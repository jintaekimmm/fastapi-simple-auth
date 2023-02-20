import math


def masking(s: str, rate: float = 0.3) -> str:
    """
    문자열을 마스킹하여 결과를 반환한다

    :param s: 입력 문자열
    :param rate: 전체 문자열에서 마스킹할 비율이다(기본 값은 전체 문자열의 30%를 마스킹한다)
    :return:
    """
    if not s:
        return ''

    str_len = len(s)
    masking_len = math.ceil(str_len * rate)

    return f"{s[:-masking_len]}{len(s[-masking_len:]) * '*'}"
