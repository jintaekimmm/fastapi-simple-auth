# Fastapi-Simple-Auth

FastAPI로 구현한 인증 API

## Introduce
FastAPI로 구현한 인증 API로 로그인, 로그아웃, 토큰 갱신 등을 포함하고 있다

코드 구조를 개선함에 따라 프로젝트를 리빌딩하였다

### .env example
```bash
# ENCRYPTION
PASSWORD_SECRET_KEY=secret
AES_ENCRYPT_KEY=secret
BLIND_INDEX_KEY=secret

# JWT
JWT_ACCESS_SECRET_KEY=secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_SECRET_KEY=secret
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080

# DATABASE
DB_HOST=DATABASE_HOST
DB_PORT=3306
DB_NAME=DATABASE_NAME
DB_USER=DATABASE_USERNAME
DB_PASSWORD=DATABASE_PASSWORD

# OAUTH: Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# OAuth: Naver
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
NAVER_CALLBACK_URL=
```

### Install & Running
```bash
# Local running usage docker-compose
docker-compose -p fastapi-simple-auth -f docker/docker-compose.yaml up -d --build

# Production running only API
docker build -t fastapi-simple-auth:{VERSION} -f docker/Dockerfile .
docker run -itd --name fastapi-simple-auth -p 8000:8000 fastapi-simple-auth:{VERSION}
```

## Database

사용자 정보와 토큰 정보를 저장하기 위한 Database schema

[Database Schema](sql/init.sql)


## Docs

[Default API docs](docs/DEFAULT.md)

[Google OAuth docs](docs/GOOGLE_OAUTH.md)

[Naver OAuth docs](docs/NAVER_OAUTH.md)

