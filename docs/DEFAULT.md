
# Auth Implements

 * 회원가입
 * 로그인
 * 로그아웃
 * 토큰 갱신(JWT Token Refresh)


## 회원가입 API


### Request
```bash
curl --location --request POST 'http://localhost:8000/v1/auth/register' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "홍길동",
    "email": "email_test@domain.com",
    "mobile": "010-1234-5678",
    "password1": "12341234!@#",
    "password2": "12341234!@#"
}'
```

## 로그인 API

Token을 반환하는 두 가지 방식에 따라 두가지 API가 존재한다

> accessToken은 JWT로 생성한다

> refreshToken은 아무런 정보도 가지고 있을 필요가 없으므로 random string으로 생성한다

### Endpoint
POST /v1/auth/api/login : JWT Token을 JSON 으로 반환 

POST /v1/auth/web/login : JWT Token을 accesToken은 JSON,refreshToken은 Cookie(httpOnly)로 반환

### Request
/v1/auth/api/login
```bash
curl --location --request POST 'http://localhost:8000/v1/auth/api/login' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "email_test@domain.com",
    "password": "12341234!@#"
}'
```

/v1/auth/web/login
```bash
curl --location --request POST 'http://localhost:8000/v1/auth/web/login' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "test@test.com",
    "password": "123123"
}'
```


## 로그아웃 API

로그아웃은 API, WEB 동일하게 Authroization 헤더를 통해 토큰을 전달한다

로그아웃 이후에도 accessToken에 유효 시간이 남아 있다면 계속 사용할 수 있다. 이 부분은 token 블랙 리스트를 만들어 로그아웃 후에 accessToken을 관리하는 방식으로 처리할 수 있을 것이다

Redis에 유효시간이 남은 시간 만큼 TTL을 설정하여 저장한다면 자연스럽게 유효 token을 관리할 수 있을 것이다

### Endpoint
POST /v1/auth/api/logout

POST /v1/auth/web/logout

### Request
/v1/auth/api/logout
```bash
curl --location --request POST 'http://localhost:8000/v1/auth/api/logout' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU4NTQwIiwiZXhwIjoiMTY2NTU1OTQ0MCIsInN1YiI6IjMiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.oSni6zPdjA-nA5ZDiFScGw-0dS1-dUXbnxFH4S49bJc'
```

/v1/auth/web/logout
```bash
curl --location --request POST 'http://localhost:8000/v1/auth/web/logout' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU4NTQwIiwiZXhwIjoiMTY2NTU1OTQ0MCIsInN1YiI6IjMiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.oSni6zPdjA-nA5ZDiFScGw-0dS1-dUXbnxFH4S49bJc'
```


## 토큰 갱신(Token Refresh)

accessToken 유효 시간 갱신을 위해 refreshToken을 사용하여 재발급 받는다

두 가지(Header, Cookie) 요청 타입에 따라 API를 나누어서 구현

### Endpoint
POST /v1/token/refresh/api : accessToken을 Authroization Header로 전달

POST /v1/token/refresh/web : accessToken을 Cookie(httpOnly)로 전달

### Request
/v1/auth/api/token/refresh
```bash
curl --location --request POST 'http://localhost:8000/v1/token/refresh/api' \
--header 'Content-Type: application/json' \
--data-raw '{
    "refresh_token": "eee778eb9950b578d6b57f4b2ef04c067f814debf7bda2c2c35828da0ff553ca"
}'
```

/v1/auth/web/token/refresh
```bash
curl --location --request POST 'http://localhost:8000/v1/token/refresh/web' \
--header 'Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNjY1NTU5NTYxIiwiZXhwIjoiMTY2NTU2MDQ2MSIsInN1YiI6IjEiLCJ0eXBlIjoiYWNjZXNzX3Rva2VuIn0.XfMXeH28lz-JYFblpUuc_yW309YETSZkMKUq8hxxIC4; refresh_token=2c7b6770d689f6597b9600ea9755b1e85d5db2c0ffd6aa9fa8c8b7b5dbe0ecd6'
```
