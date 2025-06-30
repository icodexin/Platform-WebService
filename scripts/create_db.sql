-- 用户表
CREATE TABLE users
(
    user_id         VARCHAR(20) PRIMARY KEY COMMENT '用户ID',
    hashed_password VARCHAR(128)                 NOT NULL COMMENT 'Hash密码',
    name            VARCHAR(50)                  NOT NULL COMMENT '姓名',
    status          ENUM ('ENABLED', 'DISABLED') NOT NULL DEFAULT 'ENABLED' COMMENT '账号状态',
    gender          ENUM ('M', 'F', 'U')                  DEFAULT 'U' COMMENT '性别',
    birthdate       DATE COMMENT '出生日期',
    college         VARCHAR(50) COMMENT '学院',
    stu_type        ENUM ('UNDERGRADUATE', 'POSTGRADUATE', 'DOCTORAL') COMMENT '学生类型',
    grade           INT COMMENT '年级',
    major           VARCHAR(50) COMMENT '专业',
    last_login_at   TIMESTAMP                    NULL COMMENT '最后登录时间',
    last_login_ip   VARCHAR(45) COMMENT '最后登录IP',

    created_at      TIMESTAMP                             DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by      VARCHAR(20)                  NOT NULL COMMENT '创建者',
    updated_at      TIMESTAMP                             DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    updated_by      VARCHAR(20)                  NOT NULL COMMENT '更新者'
);

-- 角色表
CREATE TABLE roles
(
    role_id     INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色ID',
    role_name   VARCHAR(20) NOT NULL UNIQUE COMMENT '角色名称',
    description VARCHAR(255) COMMENT '角色描述',

    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by  VARCHAR(20) NOT NULL COMMENT '创建者',
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    updated_by  VARCHAR(20) NOT NULL COMMENT '更新者'
);

-- 权限表
CREATE TABLE permissions
(
    perm_id     INT AUTO_INCREMENT PRIMARY KEY COMMENT '权限ID',
    perm_name   VARCHAR(50) NOT NULL UNIQUE COMMENT '权限名称',
    description VARCHAR(255) COMMENT '权限描述',

    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by  VARCHAR(20) NOT NULL COMMENT '创建者',
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    updated_by  VARCHAR(20) NOT NULL COMMENT '更新者'
);

-- 用户与角色关联
CREATE TABLE user_role
(
    user_id    VARCHAR(20) NOT NULL,
    role_id    INT         NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (role_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by VARCHAR(20) NOT NULL COMMENT '创建者',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    updated_by VARCHAR(20) NOT NULL COMMENT '更新者'
);

-- 角色与权限关联
CREATE TABLE role_permission
(
    role_id    INT         NOT NULL,
    perm_id    INT         NOT NULL,
    PRIMARY KEY (role_id, perm_id),
    FOREIGN KEY (role_id) REFERENCES roles (role_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (perm_id) REFERENCES permissions (perm_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by VARCHAR(20) NOT NULL COMMENT '创建者',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    updated_by VARCHAR(20) NOT NULL COMMENT '更新者'
);

-- 创建超级管理员
INSERT INTO users (user_id, hashed_password, name, created_by, updated_by)
VALUES ('superadmin',
        '$argon2id$v=19$m=65536,t=3,p=4$SWszl7PpYz8y9HDMDw8jCQ$7YJBmiq4hWB96oT8W5Gl5/iUak9HqBc3YWHf+S+SkwU', # real password: ccnu@123321
        '超级管理员', 'SYSTEM_INIT', 'SYSTEM_INIT');

-- 关联超级管理员角色
INSERT INTO roles (role_name, description, created_by, updated_by)
VALUES ('SUPERADMIN', '系统超级管理员角色', 'SYSTEM_INIT', 'SYSTEM_INIT');

INSERT INTO user_role(user_id, role_id, created_by, updated_by)
VALUES ('superadmin', (SELECT role_id FROM roles WHERE role_name = 'SUPERADMIN'),
        'SYSTEM_INIT', 'SYSTEM_INIT');

-- 创建系统服务账户
INSERT INTO users (user_id, hashed_password, name, created_by, updated_by)
VALUES ('sys_service',
        '$argon2id$v=19$m=65536,t=3,p=4$ucpHYhhgJjr5GE/M7rPZqg$+DT6XzBMCPc1hoc4E/7LTU9wzMZoxKNGit66a7GQ6Hc', # real password: ccnu@009988
        '系统服务账户', 'SYSTEM_INIT', 'SYSTEM_INIT');

-- 关联系统服务账户角色
INSERT INTO roles (role_name, description, created_by, updated_by)
VALUES ('SYSTEM_SERVICE', '系统服务账户角色', 'SYSTEM_INIT', 'SYSTEM_INIT');

INSERT INTO user_role(user_id, role_id, created_by, updated_by)
VALUES ('sys_service', (SELECT role_id FROM roles WHERE role_name = 'SYSTEM_SERVICE'),
        'SYSTEM_INIT', 'SYSTEM_INIT');

-- 创建学生角色
INSERT INTO roles (role_name, description, created_by, updated_by)
VALUES ('STUDENT', '学生角色', 'SYSTEM_INIT', 'SYSTEM_INIT');

-- 创建教师角色
INSERT INTO roles (role_name, description, created_by, updated_by)
VALUES ('TEACHER', '教师角色', 'SYSTEM_INIT', 'SYSTEM_INIT');

-- Token黑名单表
CREATE TABLE token_blocklist
(
    jti            BINARY(16) PRIMARY KEY COMMENT 'Token ID',
    user_id        VARCHAR(20)                NOT NULL COMMENT '用户ID',
    token_type     ENUM ('access', 'refresh') NOT NULL COMMENT 'Token类型',
    expires_at     TIMESTAMP                  NOT NULL COMMENT '过期时间',
    revoked_reason VARCHAR(255) COMMENT '撤销原因',
    FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);