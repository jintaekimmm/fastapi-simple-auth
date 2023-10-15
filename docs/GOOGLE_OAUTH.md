
# OAuth: Google Login

[Google Setting up OAuth 2.0](https://support.google.com/cloud/answer/6158849?hl=en)

[토큰 유형](https://cloud.google.com/docs/authentication/token-types?hl=ko)

[Google JavaScript API로 로그인 참조](https://developers.google.com/identity/gsi/web/reference/js-reference?hl=ko)

## .env

env 파일에 Google ClientID, Client Secret을 추가한다

```shell
... 중략

# OAauth: Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

## Google Settings 

google cloud platform 어플리케이션의 redirect_uri에 다음 uri를 설정한다

```shell
http://HOST:8000/oauth/google/login/callback
```

## Google Login Flow(redirect)

[Google 계정으로 로그인 버튼 표시](https://developers.google.com/identity/gsi/web/guides/display-button?hl=ko)

위 링크의 설명 중 일부를 아래에 작성함

`redirect mode`
redirect UX 모드를 사용하면 사용자 브라우저의 전체 페이지 리디렉션을 사용하여 로그인 UX 흐름을 실행하고 `Google에서 POST 요청을 사용하여 JWT를 로그인 엔드포인트에 직접 반환합니다.` 

-> 구글 로그인 페이지에서 로그인을 성공하면, 구글이 서버(callback)에게 POST로 JWT를 전달해준다. 콜백에서는 이 JWT를 받아서 처리하여 사용자 로그인 처리를 하면된다
