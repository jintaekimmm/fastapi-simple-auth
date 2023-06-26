import math


def masking_str(s: str, percent: float = 0.3) -> str:
    """
    입력 문자열을 마스킹하여 결과를 반환한다

    :param s: 입력 문자열
    :param percent: 문자열에서 마스킹 처리할 퍼센트 비율이다
    :return: 전체 문자열의 퍼센트 비율만큼 '*' 문자로 변환하여 반환한다
    """

    if not s:
        return ''

    str_len = len(s)
    masking_len = math.ceil(str_len * percent)

    return f"{s[:-masking_len]}{len(s[-masking_len:]) * '*'}"
