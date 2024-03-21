USE `fastapi-simple-auth`;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS user
(
    id          bigint auto_increment
        primary key,
    uuid        binary(16)           not null,
    email       varchar(255)         null comment '이메일 주소(AES 256)',
    email_key   varchar(255)         null comment '이메일 블라인드 인덱스(SHA 256)',
    mobile      varchar(255)         null comment '핸드폰 번호(AES 256)',
    mobile_key  varchar(255)         null comment '핸드폰 번호 블라인드 인덱스(SHA 256)',
    name        varchar(64)          not null comment '이름',
    password    varchar(255)         null comment '비밀번호',
    salt        binary(32)           null comment '비밀번호 Salt',
    provider_id varchar(64)          null comment 'OAuth 제공 업체',
    is_active   tinyint(1) default 0 not null comment '계정 활성화 여부',
    created_at  datetime(6)          not null comment '생성일자',
    updated_at  datetime(6)          not null comment '변경일자',

    constraint uq_email_key_provider_id
        unique (email_key, provider_id),
    constraint uq_uuid
        unique (uuid)
);

-- OAuth 사용자 정보 테이블
CREATE TABLE IF NOT EXISTS social_user
(
    id          bigint auto_increment
        primary key,
    user_id     bigint       null comment '사용자 ID(FK)',
    provider_id varchar(64)  not null comment 'OAuth 제공 업체',
    sub         varchar(255) not null comment 'OAuth 사용자 식별 정보',
    name        varchar(128) null comment 'OAuth 사용자 이름(전체 이름)',
    nickname    varchar(128) null comment 'OAuth 사용자 닉네임',
    profile_picture text null comment 'OAuth 사용자 프로필 이미지',
    given_name  varchar(128) null comment 'OAuth 사용자 이름(성씨를 제외한 이름)',
    family_name varchar(128) null comment 'OAuth 사용자 이름(성씨)',
    created_at  datetime(6)  not null comment '생성일자',
    updated_at  datetime(6)  not null comment '변경일자',

    constraint uq_provider_id_sub
        unique (provider_id, sub)
);


CREATE INDEX idx_user_id ON social_user (user_id);
CREATE INDEX idx_provider_id ON social_user (provider_id);
CREATE INDEX idx_sub ON social_user (sub);


-- 사용자 로그인 이력 테이블
CREATE TABLE IF NOT EXISTS user_login_history
(
    id            bigint auto_increment primary key,
    user_id       bigint        null comment '사용자 ID(PK)',
    user_uuid     binary(16)    not null comment '사용자 UUID',
    login_time    datetime      null comment '마지막 로그인 사간',
    login_success tinyint(1) comment '로그인 성공 여부',
    ip_address    varbinary(16) null comment '마지막 로그인 IP',
    created_at    datetime(6)   not null comment '생성일자',
    updated_at    datetime(6)   not null comment '변경일자'
);

CREATE INDEX idx_user_id ON user_login_history (user_id);
create index idx_user_uuid on user_login_history (user_uuid);

-- JWT Token 테이블
CREATE TABLE IF NOT EXISTS jwt_token
(
    id                bigint auto_increment primary key,
    user_id           bigint       not null comment '사용자 ID',
    user_uuid         binary(16)   not null comment '사용자 UUID',
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
create index idx_user_uuid on jwt_token (user_uuid);