
# OAuth: Naver Login

[Naver ID Login](https://developers.naver.com/docs/login/overview/overview.md)

[Naver 로그인 API 명세](https://developers.naver.com/docs/login/api/api.md)

[Naver 회원 프로필 조회 API 명세](https://developers.naver.com/docs/login/profile/profile.md)

## .env

env 파일에 Naver Client ID, Client Secret, Redirect Uri를 추가한다

```shell
... 중략
# OAuth: Naver
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
NAVER_CALLBACK_URL=
```

## Naver Settings

[Naver 개발자 센터에서 애플리케이션을 등록한다](https://developers.naver.com/apps/#/register?api=nvlogin)

네이버 로그인 Callback URL을 다음 uri로 설정한다

```shell
http://HOST:8000/naver/login/callback
```

## Naver Login flow

[Naver ID 로그인 - Web 어플리케이션](https://developers.naver.com/docs/login/web/web.md)

위 링크를 보면 크게 두 가지 로그인 방법이 있다

1. 서버 사이드 적용: [Naver ID 로그인 - Web 어플리케이션: 1. PHP와 Java로 네이버 로그인 적용하기](https://developers.naver.com/docs/login/web/web.md)

2. 클라이언트 사이드 적용: [Naver ID 로그인 - Web 어플리케이션: 2. JavaScript로 네이버 로그인 적용하기](https://developers.naver.com/docs/login/web/web.md)

여기서는 **1. 서버 사이드 적용** 방법을 참고하여 구현되어 있다

-> 네이버 로그인 페이지에서 로그인을 성공하면, 네이버가 서버(callback)에게 AccessToken을 전달해준다. 콜백에서는 AccessToken을 받아서 사용자 로그인 처리(프로필 조회등)를 처리하면 된다