# 多模态数据采集与学习者状态实时感知平台 - 中心服务

## 项目定位

本仓库当前是平台的中心后端服务，已落地的核心能力集中在：

- 用户管理
- 身份认证
- JWT 令牌签发与刷新
- Token 黑名单撤销机制
- 基于角色的 RBAC 基础模型

仓库同时为后续能力做了基础设施预留，但这些能力目前还没有形成完整业务实现：

- WebSocket 实时数据流接入
- RabbitMQ 消息总线集成
- 深度学习推理服务接入或编排
- 流媒体服务协同

## 当前技术栈

- Python 3.10+
- FastAPI
- SQLAlchemy 2.x Async ORM
- asyncpg
- Alembic
- PostgreSQL / TimescaleDB
- RabbitMQ
- APScheduler
- `python-jose`
- `pwdlib[argon2]`

说明：
- 代码和迁移当前基于 PostgreSQL 生态实现，不是 MySQL。
- `docker-compose.yml` 中已声明 TimescaleDB、RabbitMQ、MediaMTX。
- `aio-pika`、`msgpack` 等依赖已经存在，但还没有完整接入到应用主流程。

## 目录结构

```text
.
├── app/
│   ├── api/         # HTTP 路由层
│   ├── common/      # 枚举与共享常量
│   ├── core/        # 配置、数据库、鉴权基础设施
│   ├── dao/         # 数据访问层
│   ├── models/      # SQLAlchemy ORM 模型
│   ├── schemas/     # Pydantic 请求/响应模型
│   ├── services/    # 业务服务层
│   └── utils/       # 通用工具
├── alembic/         # 数据库迁移
├── test/            # 手工 HTTP 测试文件
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
└── AGENTS.md
```

## 当前已实现能力

### 1. 认证与授权

- `POST /auth/token`：用户名密码登录，签发 access token 和 refresh token
- `POST /auth/refresh`：刷新令牌，并撤销旧 refresh token
- `POST /auth/logout`：注销并撤销 access/refresh token

### 2. 用户管理

- `POST /api/users/`：创建用户
- `GET /api/users/me`：获取当前登录用户信息

当前支持的用户类型：

- `student`
- `teacher`
- `admin`

其中：

- `student`、`teacher` 具有独立 profile 表
- `admin` 账号由 Alembic 初始化迁移自动创建

### 3. RBAC 与安全机制

- 用户、角色、权限采用标准关联表建模
- JWT 使用 `jti` 标识唯一令牌
- 已撤销令牌存入 `token_blocklist`
- 应用启动后会通过 APScheduler 定时清理过期黑名单记录

## 数据模型概览

当前核心模型包括：

- `User`
- `StudentProfile`
- `TeacherProfile`
- `Role`
- `Permission`
- `UserRole`
- `RolePermission`
- `TokenBlocklist`

设计特点：

- 用户基础信息和角色扩展信息分表存储
- 通过 `user_type` 区分用户类型
- 通过关联表支持 RBAC 扩展
- 通过黑名单机制支持 JWT 主动失效

## 基础设施

### 数据库

当前使用：

- PostgreSQL / TimescaleDB

`docker-compose.yml` 中使用的镜像为：

- `timescale/timescaledb:latest-pg17`

### 消息队列

当前已声明：

- RabbitMQ
- 管理插件
- MQTT 插件

说明：
- 已实现 RabbitMQ HTTP Auth Backend 四个认证接口，并已接入 `app/main.py`
- RabbitMQ 容器配置文件位于 `config/rabbitmq/rabbitmq.conf` 和 `config/rabbitmq/enabled_plugins`
- 当前容器内通过 `host.docker.internal:8000` 访问 FastAPI 认证接口，本地开发时需先启动 Web 服务

### 流媒体

当前已声明：

- MediaMTX

用于后续接入 RTSP / RTMP / HLS / WebRTC 等流媒体能力。

## 快速开始

### 1. 安装依赖

推荐使用 `uv`：

```bash
uv sync
```

### 2. 准备环境变量

仓库根目录使用 `.env` 作为默认配置来源。至少需要确认以下变量：

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=your-password
POSTGRES_DB=platform

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=your-password

SYS_ADMIN_USER=admin
SYS_ADMIN_INIT_PWD=your-password
```

### 3. 启动基础设施

```bash
docker compose up -d
```

当前会启动：

- TimescaleDB
- RabbitMQ
- MediaMTX

RabbitMQ 已启用以下插件：

- `rabbitmq_management`
- `rabbitmq_event_exchange`
- `rabbitmq_mqtt`
- `rabbitmq_auth_backend_http`

### 4. 执行数据库迁移

```bash
uv run alembic upgrade head
```

### 5. 启动服务

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

文档地址：

- Swagger UI: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- OpenAPI: [http://127.0.0.1:8000/api/openapi.json](http://127.0.0.1:8000/api/openapi.json)

## 开发约定

建议遵守当前项目分层：

- `api/` 只负责 HTTP 输入输出和依赖注入
- `services/` 负责业务编排
- `dao/` 负责数据库访问与事务边界
- `models/` 负责 ORM 建模
- `schemas/` 负责请求/响应契约
- `core/` 负责配置、数据库和安全基础能力

新增能力时建议：

- WebSocket 放到 `app/ws/` 或 `app/realtime/`
- RabbitMQ 集成放到 `app/messaging/`
- 推理服务放到 `app/inference/`
- 后台任务放到 `app/jobs/`

## RabbitMQ 权限映射

当前仓库已经实现 RabbitMQ HTTP Auth Backend 四个接口：

- `POST /mq/auth/user`
- `POST /mq/auth/vhost`
- `POST /mq/auth/resource`
- `POST /mq/auth/topic`

业务权限命名和 RabbitMQ 映射规范见：

- `docs/messaging-permissions.md`
- `docs/messaging-permissions.zh-CN.md`

当前采用两层模型：

- `Role -> Permission` 表达业务能力
- `Permission -> rabbitmq_permission_binding` 表达 RabbitMQ 技术授权规则

默认已种子化一条管理员权限：

- `cap.messaging.broker.manage`

RabbitMQ HTTP 后端配置入口：

- `config/rabbitmq/rabbitmq.conf`
- `config/rabbitmq/enabled_plugins`

当前对 RabbitMQ 暴露的实际访问前缀为：

- `/mq/auth`

## 当前边界与注意事项

目前不要误判为“已完整实现”的能力：

- WebSocket 实时服务
- 推理服务
- 面向具体业务域的大规模 RabbitMQ 权限种子数据
- 细粒度权限校验中间件
- 自动化测试体系

另外：

- `README` 以代码现状为准，当前数据库是 PostgreSQL/TimescaleDB
- 若后续引入 NGINX，请在仓库中补充对应配置后再写入文档

## 测试与调试

当前仓库中已有手工测试文件：

- `test/user.http`
- `test/http-client.env.json`

更适合用于接口联调和本地验证；自动化测试体系仍待补充。

## 后续演进建议

推荐将本仓库继续演进为平台统一接入与控制面服务：

- 保持用户、认证、RBAC 作为平台统一身份中心
- 为 WebSocket 连接复用现有 JWT 认证体系
- 将 RabbitMQ 作为异步事件总线而不是直接耦合到路由层
- 将深度学习推理任务封装为独立服务适配层，避免阻塞主请求线程
- 将实时流处理与媒体接入能力模块化，不污染现有用户管理主链路
