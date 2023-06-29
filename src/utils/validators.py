import re
import string


def check_name(u: str) -> bool:
    """
    name의 유효성을 검사한다
     - 2자리 ~ 50자 이내의 길이
     - 한글, 영어만 사용 가능

    :param u: 사용자 이름
    :return: 유효성 검증을 통과한 경우 'True'를 반환하고, 통과하지 못한경우 'False'를 반환한다
    """

    # 2자리 ~ 50자리 이내인지 확인
    if 1 < len(u) <= 50:
        k = 0
        e = 0
        # 띄어쓰기 수 카운트
        s = 0
        # 문자열 없이 띄어쓰기만으로 입력된 경우를 체크하기 위한 유효성 통과 조건 수를 카운트
        complex_counts = 0

        for i in u:
            if i == " ":
                s += 1
            if ord("가") <= ord(i) <= ord("힣"):
                k += 1
            if ord("a") <= ord(i) <= ord("z"):
                e += 1
            if ord("A") <= ord(i) <= ord("Z"):
                e += 1

        # 띄어쓰기가 있는 경우에 다른 문자열이 입력된 것이 있는지 검사한다
        if s != 0:
            complex_counts = 2
        else:
            for j in [k, e]:
                if j != 0:
                    complex_counts += 1

        if k + e + s == len(u) and complex_counts >= 1:
            return True
        else:
            return False
    else:
        return False


def check_password(p: str) -> bool:
    """
    Password의 유효성을 검사한다
    - 8자리 이상의 길이
    - 소문자, 대문자, 숫자, 기호가 포함되어 있는지 확인
    - 유효성은 소문자, 대문자, 숫자, 기호에서 최소 2종류가 포함되어야 한다

    :param p: 비밀번호 문자열
    :return: 유효성 검증을 통과한 경우 'True'를 반환하고, 통과하지 못한경우 'False'를 반환한다
    """
    l = 0
    u = 0
    d = 0
    c = 0
    # 유효성을 만족하는 조건의 수를 카운트
    # 소문자, 대문자, 숫자, 기호에서 최소 2종류가 포함되야한다
    complex_counts = 0

    # 8자리 이상인지 확인
    if len(p) > 7:
        for i in p:
            # 소문자 개수를 카운팅
            if i.islower():
                l += 1

            # 대문자 개수를 카운팅
            if i.isupper():
                u += 1

            # 숫자 개수를 카운팅
            if i.isdigit():
                d += 1

            # 기호 개수를 카운팅
            # string.punctuation: !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~
            if i in string.punctuation:
                c += 1

        # 유효성을 통과한 조건의 수를 카운트한다
        for j in [l, u, d, c]:
            if j != 0:
                complex_counts += 1

        if l + u + d + c == len(p) and complex_counts >= 2:
            return True
        else:
            return False
    else:
        return False


def check_mobile(m: str) -> bool:
    """
    핸드폰 번호의 유효성을 검사한다

    :param m: 핸드폰 번호 문자열
    :return: 유효성 검증을 통과한 경우 'True'를 반환하고, 통과하지 못한경우 'False'를 반환한다
    """

    # 유효성 검증을 위한 정규표현식
    pattern = re.compile(r"^(01[0|1|6|7|8|9])[.-]?(\d{3}|\d{4})[.-]?(\d{4})")
    # hyphen_add_number = '-'.join(pattern.search(m).groups())

    return bool(pattern.match(m))


def name_validator(value):
    if not check_name(value):
        raise ValueError("2~50자 이내의 한글/영문만 사용 가능합니다")

    return value


def password_validator(value):
    if not check_password(value):
        raise ValueError("8자리 이상의 소문자/대문자/숫자/기호 중 두 가지 이상의 종류를 포함해야합니다")

    return value


def mobile_validator(value):
    if not check_mobile(value):
        raise ValueError("잘못된 핸드폰 번호입니다")

    return value
