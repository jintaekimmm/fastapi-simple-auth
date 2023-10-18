
# OAuth: Kakao Login

[카카오 로그인](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api)

[카카오 로그인 설정하기](https://developers.kakao.com/docs/latest/ko/kakaologin/prerequisite)


## .env

env 파일에 Kakao RestAPI Key, Client Secret, Redirect Uri를 추가한다

client Secret은 [내 애플리케이션] > [보안] 에서 설정 가능하다

```shell
# OAuth: Kakao
KAKAO_REST_API_KEY=
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=
```

## Kakao Settings

[카카오 로그인 설정하기](https://developers.kakao.com/docs/latest/ko/kakaologin/prerequisite)

카카오 로그인 Redirect URI를 다음 uri로 설정한다

```shell
http://HOST:8000/kakao/login/callback
```

## Kakao Login flow

[카카오 REST API로 로그인하기](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#kakaologin)

REST API를 통해 카카오 로그인을 구현한다

1. [인가 코드 받기](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#request-code)
2. [토큰 받기](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#request-token)
3. [사용자 정보 가져오기](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#req-user-info)


### OpenID

OpenID Connect 활성화 설정을 하지 않아도 카카오 로그인을 진행하는데 문제가 없다

OpenID Token을 처리하지 않고 있으며, 직접 사용자 정보를 호출하여 프로필 정보를 가져오고 있다

이것은 카카오 로그인 '동의항목'에 동의된 정보들이 OpenID와 사용자 정보 조회 시에 동일한 결과를 가져오게 된다

명시적으로 사용하기 위해 API 호출이 늘어나도 사용자 정보를 직접 요청하고 있다

### 동의항목

개발할 때에는 동의항목에 모든 상태를 사용할 수 없다. 다음 링크에는 동의항목별 설정 방법을 볼 수 있다

[동의 항목별 "필수동의" 설정 방법](https://devtalk.kakao.com/t/how-to-set-scopes-to-required-consent/115162)
