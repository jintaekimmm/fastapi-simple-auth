# Simple Auth JWT

JWT를 사용하여 간단한 인증 서버 구현

## Introduce
기존의 작성된 많은 글과 질문/답변을 보고 구현하였습니다. 일부 구현은 여러 선택 사항 중에 주관적인 생각으로 맞다고 하는 것을 기준으로 선택하였습니다

Oauth 2.0을 제대로 본 이후에 잘못된 것 같은 부분은 수정할 예정입니다. 

화면(Front-end)에서 어떻게 사용할 지에 대해서는 완벽히 고려된 것이 아니므로 실제 사용성과 관련해서는 괴리감이 있을 수 있습니다. 

### .env example
```bash
# ENCRYPTION
PASSWORD_SECRET_KEY={secret_key}
AES_ENCRYPT_KEY={secret_key}
BLIND_INDEX_KEY={secret_key}

#JWT
JWT_ACCESS_SECRET_KEY={secret_key}
JWT_REFRESH_SECRET_KEY={secret_key}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080

# DATABASE
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

## Structure 

```bash
project/
├── app
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   └── v1
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── user.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── security
│   │       ├── __init__.py
│   │       └── encryption.py
│   └── main.py
├── db
│   ├── __init__.py
│   ├── base.py
│   └── crud
│       ├── __init__.py
│       ├── crud_token.py
│       └── crud_user.py
├── dependencies
│   ├── __init__.py
│   ├── auth.py
│   └── database.py
├── gunicorn_conf.py
├── internal
│   ├── __init__.py
│   ├── config.py
│   └── logging.py
├── logs
├── models
│   ├── __init__.py
│   ├── groups.py
│   ├── mixin.py
│   ├── token.py
│   ├── user.py
│   └── user_groups.py
└── schemas
    ├── __init__.py
    ├── auth.py
    ├── token.py
    └── user.py
```

## API Endpoints

![API Endpoint](https://user-images.githubusercontent.com/31076511/195282934-2483a625-9d1f-45a6-9c94-f4092179dccb.png)

## Auth Implements

 * 회원가입
 * 로그인
 * 로그아웃
 * 토큰 갱신(JWT Token Refresh)

## Database

사용자 정보와 토큰(refresh) 정보를 저장하기 위한 Database schema

### User Table
이메일과 핸드폰 번호는 암호화(AES 256)하여 저장한다. 암호화된 값을 검색할 수 없으니 Hash값을 사용해서 검색할 수 있도록 xxx_key 컬럼을 사용한다(blind index)

is_admin과 is_active는 당장 사용하는 컬럼은 아니지만 추후 기능 확장을 위해 컬럼을 생성해둔다
```sql
CREATE TABLE `user`
(
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(32)  NULL     DEFAULT NULL,
    last_name  VARCHAR(32)  NULL     DEFAULT NULL,
    email      VARCHAR(128) NULL,
    email_key  VARCHAR(128) NULL,
    mobile     VARCHAR(128) NULL,
    mobile_key VARCHAR(128) NULL,
    password   VARCHAR(128) NOT NULL,
    is_admin   TINYINT(1)   NOT NULL DEFAULT 0,
    is_active  TINYINT(1)   NOT NULL DEFAULT 0,
    created_at datetime(6)  not null,
    updated_at datetime(6)  not null,
    last_login DATETIME     NULL     DEFAULT NULL,
    last_login_ip VARBINARY(16) NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE INDEX uq_mobile (mobile_key ASC),
    UNIQUE INDEX uq_email (email_key ASC),
    INDEX idx_email (email ASC),
    INDEX idx_mobile (mobile ASC)
);
```

### Token Table
발급한 refreshToken을 관리하는 목적으로 사용한다. refreshToken은 암호화하여 저장하고 검색을 위한 blind index용 컬럼 xxx_key 컬럼을 사용한다

또한, refreshToken과 연결되는 access_token도 저장한다. access_token은 짧은 유효 시간을 가지므로 암호화를 하지 않았다 
```sql
CREATE TABLE `token`
(
    id                bigint auto_increment primary key,
    user_id           int          not null,
    access_token      VARCHAR(255) not null,
    refresh_token     text         not null,
    refresh_token_key VARCHAR(128) not null,
    issued_at         datetime     not null,
    expires_at        datetime     not null,

    INDEX idx_user_id (user_id ASC),
    INDEX idx_access_token (access_token ASC),
    INDEX idx_refresh_token_key (refresh_token_key ASC),
    INDEX idx_expires_at (expires_at ASC)
);
```

## 회원가입 API

사용자의 가입 정보를 처리한다

개인 정보(email, mobile)는 AES 256으로 암호화 하였고, 검색을 위한 blind index를 설정했다 

### Endpoint
[/v1/signup](https://github.com/99-66/simple-auth-jwt/blob/main/project/app/api/v1/user.py#L15)

```bash
POST /v1/signup 
```

### Request
```bash
curl --location --request POST 'http://localhost:9000/v1/signup' \
--header 'Content-Type: application/json' \
--data-raw '{
    "first_name": "jintae",
    "last_name": "kim",
    "email": "email_test@domain.com",
    "mobile": "010-1234-5678",
    "password1": "12341234!@#",
    "password2": "12341234!@#"
}'
```

### Response
```bash
HTTP_STATUS 201 Content: null
```

## 로그인 API

Token을 반환하는 두 가지 방식에 따라 API를 나누어서 구현하였다


> 응답 방식에 많은 고민을 하였으나, 실제 서비스 환경에 따라서 사용하는 방식이 달라질 것 이므로 구현해보는 입장에서는 두 가지 모두를 사용해볼 수 있게 하였습니다 
>
>  또한 token을 어디에다가(local Storage, Cookie...) 저장하는 것에 대한 많은 의견을 보았으나 이 또한 서비스 환경에 따라 선택이 달라질 것이므로
> 
> 값을 직접 사용할 수 있도록 **JSON으로 반환**하는 것과 **cookie(httpOnly)에 설정**하는 것 두 가지로 나누어서 구현하였습니다

> accessToken은 JWT로 생성한다

> refreshToken은 아무런 정보도 가지고 있을 필요가 없으므로 random string으로 생성한다

### Login Process
![Login Process](https://user-images.githubusercontent.com/31076511/195269797-1e881aaa-bf1e-447e-b1c9-49cbb9316f2c.png)

### Endpoint
[/v1/auth/api/login](https://github.com/99-66/simple-auth-jwt/blob/main/project/app/api/v1/auth.py#L21)
[/v1/auth/web/login](https://github.com/99-66/simple-auth-jwt/blob/main/project/app/api/v1/auth.py#L83)
```bash
/v1/auth/api/login : JWT Token을 JSON 으로 반환 
/v1/auth/web/login : JWT Token을 Cookie(httpOnly)로 반환
```

### Request
/v1/auth/api/login
```bash
curl --location --request POST 'http://localhost:9000/v1/auth/api/login' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "email_test@domain.com",
    "password": "12341234!@#"
}'
```

/v1/auth/web/login
```bash
curl --location --request POST 'http://localhost:9000/v1/auth/web/login' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "test@test.com",
    "password": "123123"
}'
```

### Response
/v1/auth/api/login
```bash
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU2MTI3IiwiZXhwIjoiMTY2NTU1NzAyNyIsInN1YiI6IjMiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.Csxe9d_KJGt26r_99aiam2Xtcrcxebkhu6TqBPOMGqg",
    "refresh_token": "ed1121cda6b98997caa3ff7a6b1cfeab7eb596223e0d4bca154367ecf3373546",
    "token_type": "Bearer",
    "expires_in": "1665557027",
    "refresh_token_expires_in": "1666160927",
    "scope": "",
    "sub": "3",
    "iat": "1665556127"
}
```

/v1/auth/web/login
```bash
[Body]
{
    "message": "login success"
}

[Cookie]
access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU2Mjk0IiwiZXhwIjoiMTY2NTU1NzE5NCIsInN1YiI6IjEiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.Z5RhmtqbNfn6eCvr4RhGfDfFCDKTdytXPPi2aW2sLEM; Path=/; HttpOnly;
refresh_token=31f84b4c3fa8d1eb71c036e7e4cc6931d45de42a80521c18308f58fadcdcf95e; Path=/; HttpOnly;
```

## 로그아웃 API

두 가지(Header, Cookie) 요청 타입에 따라 API를 나누어서 구현하였다

로그아웃 이후에도 accessToken에 유효 시간이 남아 있다면 계속 사용할 수 있다. 이 부분은 token 블랙 리스트를 만들어 로그아웃 후에 accessToken을 관리하는 방식으로 처리할 수 있을 것이다

Redis에 유효시간이 남은 시간 만큼 TTL을 설정하여 저장한다면 자연스럽게 유효 token을 관리할 수 있을 것이다(resource server에서 JWT을 검증할 때 redis에서 token을 조회해야 하는 부분이 추가되어야 한다)

### Logout Process
![Logout Process](https://user-images.githubusercontent.com/31076511/195273518-6c6a0a3e-1be4-4afe-b120-3c760d669f17.png)

### Endpoint
[/v1/auth/api/logout](https://github.com/99-66/simple-auth-jwt/blob/main/project/app/api/v1/auth.py#L149)
[/v1/auth/web/logout](https://github.com/99-66/simple-auth-jwt/blob/main/project/app/api/v1/auth.py#L187)
```bash
/v1/auth/api/logout : accessToken을 Authroization Header로 전달 
/v1/auth/web/logout : accessToken을 Cookie(httpOnly)로 전달
```

### Request
/v1/auth/api/logout
```bash
curl --location --request POST 'http://localhost:9000/v1/auth/api/logout' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU4NTQwIiwiZXhwIjoiMTY2NTU1OTQ0MCIsInN1YiI6IjMiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.oSni6zPdjA-nA5ZDiFScGw-0dS1-dUXbnxFH4S49bJc'
```

/v1/auth/web/logout
```bash
curl --location --request POST 'http://localhost:9000/v1/auth/web/logout' \
--header 'Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU4NjMxIiwiZXhwIjoiMTY2NTU1OTUzMSIsInN1YiI6IjEiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.o_5oGzp6x1vjbx5G5aF2MFbToX_mPWpXReZR5zJWqsA'
```

### Response
/v1/auth/api/logout
```bash
{
    "message": "logout success"
}
```

/v1/auth/web/logout
```bash
{
    "message": "logout success"
}
```

## 토큰 갱신(refresh Token)

accessToken 유효 시간 갱신을 위해 refreshToken을 사용하여 재발급 받는다

두 가지(Header, Cookie) 요청 타입에 따라 API를 나누어서 구현하였다

accessToken을 갱신할 때에 refreshToken을 어떻게 할 것인가 에 대한 고민이 있었다 
 1. refreshToken에 아무 작업도 하지 않는다
 2. refreshToken의 만료 시간을 token 갱신 시점으로 업데이트 한다
 3. refreshToken을 새로 생성한다

> 처음에는 refreshToken의 만료 시간만 업데이트 하였으나, 동일 token이 날짜만 계속 늘어난다는 것이 마음에 들지 않았다.

이후 서비스 실 사용성과 관련하여 고민해보았으나, 결론적으로 **3. refreshToken을 새로 생성한다** 로 선택하였다

이런 선택을 한 이유에는 1)과 관련된 고민 중에 2) 글을 보고 마음을 정했다
 1) 사용자가 서비스를 사용 중에 refreshToken이 만료된다면? 
   > 로그인 할 때에 7일의 유효 시간을 갖는 refreshToken을 발급받는다. 사용자가 서비스를 이용 할 때마다 로그인하여 token을 발급 받아 사용하거나, 로그아웃을 잘한다면 문제가 없을 것 같으나,
   > 해당 기간동안 계속해서 사용하는 사용자는 사용중에 강제로 로그인을 해야하는 상황이 나올 수도 있겠다는 생각이 들었다
 2) [refresh-tokens-what-are-they-and-when-to-use-them](https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/)
   > auth0 블로그를 보면 보안 기술로 accessToken을 갱신 할 때마다 refreshToken을 함께 변경(rotation) 한다는 내용을 담고 있다

### Refresh Process
![Refresh Process](https://user-images.githubusercontent.com/31076511/195276586-50cf0610-8e35-4268-8303-f64e0fb0f7a6.png)


### Endpoint
[/v1/auth/api/token/refresh](https://github.com/99-66/simple-auth-jwt/blob/main/project/app/api/v1/auth.py#L232)
[/v1/auth/api/token/refresht](https://github.com/99-66/simple-auth-jwt/blob/main/project/app/api/v1/auth.py#L283)
```bash
/v1/auth/api/token/refresh : accessToken을 Authroization Header로 전달 
/v1/auth/api/token/refresh : accessToken을 Cookie(httpOnly)로 전달
```


### Request
/v1/auth/api/token/refresh
```bash
curl --location --request POST 'http://localhost:9000/v1/auth/api/token/refresh' \
--header 'Content-Type: application/json' \
--data-raw '{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU5NDQwIiwiZXhwIjoiMTY2NTU2MDM0MCIsInN1YiI6IjMiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.1FTOH5mizxDuYrqwt1kc_LxAeZGGU7K5BNdGfKKYR0o",
    "refresh_token": "eee778eb9950b578d6b57f4b2ef04c067f814debf7bda2c2c35828da0ff553ca"
}'
```

/v1/auth/web/token/refresh
```bash
curl --location --request POST 'http://localhost:9000/v1/auth/web/token/refresh' \
--header 'Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU5NTYxIiwiZXhwIjoiMTY2NTU2MDQ2MSIsInN1YiI6IjEiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.XfMXeH28lz-JYFblpUuc_yW309YETSZkMKUq8hxxIC4; refresh_token=2c7b6770d689f6597b9600ea9755b1e85d5db2c0ffd6aa9fa8c8b7b5dbe0ecd6'
```


### Response
/v1/auth/api/token/refresh
```bash
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU5NTM1IiwiZXhwIjoiMTY2NTU2MDQzNSIsInN1YiI6IjMiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.z3hOy91tLPhbJhtn98mvTFh9ut3JweSWEG8N7-oXppI",
    "refresh_token": "298d3ede1a89f313326328c303d6915130d22ea02b82c647a4828162b00c08e2"
}
```

/v1/auth/web/token/refresh
```bash
[body]
{
    "message": "refresh success"
}
[cookie]
access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU5NTc4IiwiZXhwIjoiMTY2NTU2MDQ3OCIsInN1YiI6IjEiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0._B9pUAzJkGDkpuylV_yICOeX4q8_xKqPVWdZF9WpSDY; Path=/; HttpOnly;
refresh_token=525e281c5dfb2c378ebb49c82cd5a46a55474e3446b07f742d590f168ebd1b5f; Path=/; HttpOnly;
```


## End
JWT를 간단하게 보고 시작했다가 오히려 많은 부분을 고민하게 되었다. 각 process 별로 정립된 것이 없고 사람마다 구현이 달라 '무엇이 맞는가', '어떻게 구현해야 하는가'에 대한 결정이 어려웠다

여러 질문과 답변, 글을 보면서도 한편으로는 어느 정도 타협을 하고 간단하게 구현을 할까도 했지만 보안과 관련해서는 타협을 하면 안되겠다는 생각을 하고

내가 인증 서버를 구현해서 쓴다면 이정도는 해야 겠다는 생각을 했다. 

당장은 수정하거나 추가되는 것이 많지 않겠지만, Oauth 2.0을 보고난 이후에 다시 한번 정리를 해보려고 한다

## Reference
 * [https://medium.com/@joshuakelly/blind-indexes-in-3-minutes-making-encrypted-personal-data-searchable-b26bce99ce7c](https://medium.com/@joshuakelly/blind-indexes-in-3-minutes-making-encrypted-personal-data-searchable-b26bce99ce7c)
 * [https://stackoverflow.com/questions/4961603/whats-the-best-way-to-store-and-yet-still-index-encrypted-customer-data](https://stackoverflow.com/questions/4961603/whats-the-best-way-to-store-and-yet-still-index-encrypted-customer-data)
 * [https://9to5tutorial.com/think-of-a-way-to-store-both-ipv4-and-ipv6-ip-addresses-in-one-column-in-mysql](https://9to5tutorial.com/think-of-a-way-to-store-both-ipv4-and-ipv6-ip-addresses-in-one-column-in-mysql)
 * [https://stackoverflow.com/questions/27067251/where-to-store-jwt-in-browser-how-to-protect-against-csrf/63593954#63593954](https://stackoverflow.com/questions/27067251/where-to-store-jwt-in-browser-how-to-protect-against-csrf/63593954#63593954)
 * [https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/](https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/)
 * [https://developers.ringcentral.com/guide/authentication/jwt-flow](https://developers.ringcentral.com/guide/authentication/jwt-flow)
 * [https://towardsdev.com/login-and-registration-workflow-with-jwt-32d492bdfce0](https://towardsdev.com/login-and-registration-workflow-with-jwt-32d492bdfce0)
 * [https://christophergs.com/tutorials/ultimate-fastapi-tutorial-pt-10-auth-jwt/#practical](https://christophergs.com/tutorials/ultimate-fastapi-tutorial-pt-10-auth-jwt/#practical)