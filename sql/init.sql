USE `fastapi-simple-auth`;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS user
(
    id         bigint auto_increment primary key,
    uuid       binary(16)           not null comment '',
    email      varchar(255)         null comment '이메일 주소(AES 256)',
    email_key  varchar(255)         null comment '이메일 블라인드 인덱스(SHA 256)',
    mobile     varchar(255)         null comment '핸드폰 번호(AES 256)',
    mobile_key varchar(255)         null comment '핸드폰 번호 블라인드 인덱스(SHA 256)',
    name       varchar(64)          not null comment '이름',
    password   varchar(255)         not null comment '비밀번호',
    is_active  tinyint(1) default 0 not null comment '계정 활성화 여부',
    created_at datetime(6)          not null comment '생성일자',
    updated_at datetime(6)          not null comment '변경일자',

    constraint uq_email
        unique (email_key),
    constraint uq_mobile
        unique (mobile_key),
    constraint uq_uuid
        unique (uuid)
);

-- 사용자 로그인 이력 테이블
CREATE TABLE IF NOT EXISTS user_login_history
(
    id            bigint auto_increment primary key,
    user_id       bigint        null comment '사용자 ID(PK)',
    login_time    datetime      null comment '마지막 로그인 사간',
    login_success tinyint(1) comment '로그인 성공 여부',
    ip_address    varbinary(16) null comment '마지막 로그인 IP',
    created_at    datetime(6)   not null comment '생성일자',
    updated_at    datetime(6)   not null comment '변경일자'
);

CREATE INDEX idx_user_id ON user_login_history (user_id);


-- JWT Token 테이블
CREATE TABLE IF NOT EXISTS jwt_token
(
    id                bigint auto_increment primary key,
    user_id           bigint       not null comment '사용자 ID',
    access_token      varchar(255) not null comment 'AccessToken',
    refresh_token     text         not null comment 'RefreshToken(AES 256)',
    refresh_token_key varchar(128) not null comment 'RefreshToken(SHA 256)',
    issued_at         datetime     not null comment 'Token 발행일시',
    expires_at        datetime     not null comment 'RefreshToken 만료일시',
    created_at        datetime(6)  not null comment '생성일자',
    updated_at        datetime(6)  not null comment '변경일자'
);

CREATE INDEX idx_user_id ON jwt_token (user_id);
CREATE INDEX idx_access_token ON jwt_token (access_token);
CREATE INDEX idx_expires_at ON jwt_token (expires_at);
CREATE INDEX idx_refresh_token_key ON jwt_token (refresh_token_key);
