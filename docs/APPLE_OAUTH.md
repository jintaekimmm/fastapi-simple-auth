
# OAuth: Apple Login

[Sign in with Apple REST API](https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api)

[Authenticating users with Sign in with Apple](https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api/authenticating_users_with_sign_in_with_apple)

[Displaying  Sign in with Apple buttons on the web](https://developer.apple.com/documentation/sign_in_with_apple/displaying_sign_in_with_apple_buttons_on_the_web)

## Apple Settings

[Configure your environment for Sign in with Apple](https://developer.apple.com/documentation/sign_in_with_apple/configuring_your_environment_for_sign_in_with_apple)

Apple Login API를 사용하기 위해서는 [Apple Developer Program](https://developer.apple.com/programs/)에 등록해야 합니다 (Year/$99)

Login Redirect(Callback) URI는 https:// 를 사용해야 합니다(http://localhost:PORT는 사용할 수 없다)

1. APP ID 생성
   - "Certificates, Identifiers & Profiles" - "Identifiers" 에서 App IDs 생성
   - **App IDs의 "Identifier" 값은 .env의 TEAM_ID 값으로 사용**
2. Key 생성
   - "Certificates, Identifiers & Profiles" - "Keys" 에서 Key 생성
   - "Sign in with Apple" 메뉴 체크 -> configure에서 "Primary App ID" 에는  "1. " 에서 생성한 App ID 선택 
   - Key 등록 후 key file 다운로드: **key file은 이후 client secret을 생성할 때 사용**
   - **Key ID는 .env의 "KEY_ID" 값으로 사용**
   - **key file 이름은 .env의 "AUTH_KEY_FILE" 값으로 사용**
3. Services ID 생성
   - "Certificates, Identifiers & Profiles" - "Identifiers" 에서 Services IDs 생성
   - "Sign in with Apple" 메뉴 체크 -> configure에서 "Primary App ID" 에는  "1. " 에서 생성한 App ID 선택
   - "Domains and Subdomains" 에는 http 스킴을 제외한 도메인을 입력
   - "Return URLs" 에는 Login Callback URL을 입력(https://YOUR_DOMAIN/oauth/apple/login/callback)
   - **Services ID의 "Identifier" 값은 .env의 CLIENT_ID 값으로 사용**


## .env

env 파일에 아래와 같이 환경 변수를 설정한다

```shell
... 중략

# OAuth: Apple
APPLE_TEAM_ID=
APPLE_CLIENT_ID=
APPLE_KEY_ID=
APPLE_REDIRECT_URI=https://YOUR_DOMAIN/oauth/apple/login/callback
APPLE_AUTH_KEY_FILE=xxx.p8
```

## Key file

Login 처리 중 callback으로 전달된 token의 유효성을 검증하기 위해 Client Secret을 생성하여 Apple로 전송한다

Client Secret은 JWT Token으로 되어 있는데, key file로 jwt claim set을 signing하여 전송해야 한다

다운로드 받은 key file의 이름은 .env의 "APPLE_AUTH_KEY_FILE"에 설정하고, src 디렉터리 하위로 이동시킨다

```shell
$ cp YOUR_KEY/DIRECTORY_PATH/key.p8 src/key.p8 
```

## Apple Login Flow

[Displaying  Sign in with Apple buttons on the web](https://developer.apple.com/documentation/sign_in_with_apple/displaying_sign_in_with_apple_buttons_on_the_web) 를 통해 로그인 버튼을 설정하여 애플 로그인을 시도할 수 있다

위를 통해 로그인이 성공하였다면, APPLE_REDIRECT_URI로 인증된 사용자 정보와 토큰이 전송된다

전송되는 토큰은 [Retrieve the user's information from Apple ID servers](https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_rest_api/authenticating_users_with_sign_in_with_apple#3383773)를 통해 알 수 있으며, 주의할 점은 최초 로그인을 했을 때만 사용자 정보를 제공해주고

이후 로그인할 때는 사용자 정보를 제외하고 토큰만 전송된다

```shell
예) callback 데이터 중 
  ...
  "user": {
    "email": "exmaple@exmaple.com",
    "name": {
      "firstName": "fisrt",
      "lastName": "last"
    }
  }
```
