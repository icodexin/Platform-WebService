# 消息业务权限命名与 RabbitMQ 映射规范

## 1. 目标

本文档用于定义：

- 队列 / 消息相关业务权限的命名方式
- 业务权限如何映射到 RabbitMQ HTTP Auth Backend 的四类检查
- 角色设计如何与 RabbitMQ 底层资源解耦

核心设计原则：

- `Role -> Permission` 表达业务能力
- RabbitMQ 的技术授权通过独立映射层处理

这样可以避免把角色直接绑定到具体的 exchange、queue 或 routing key 名称上。

## 2. 业务权限命名规范

### 2.1 固定格式

统一使用以下点分格式：

```text
cap.<domain>.<resource>.<action>[.<scope>]
```

### 2.2 各段含义

| 段位 | 含义 |
|---|---|
| `cap` | 固定前缀，表示业务能力（capability） |
| `<domain>` | 业务域，例如 `messaging` |
| `<resource>` | 业务对象，而不是 RabbitMQ 的底层对象 |
| `<action>` | 允许执行的业务动作 |
| `[.<scope>]` | 可选的额外范围，例如 `personal`、`admin`、`classroom` |

### 2.3 命名规则

- 全部使用小写字母
- 使用 `.` 进行分段
- 各段尽量表达业务语义，而不是技术实现
- 不要把 queue、exchange、routing key 直接写进 `permission.code`
- 当单段必须表达多词语义时，可在段内使用 `snake_case`

### 2.4 推荐示例

```text
cap.messaging.telemetry.publish
cap.messaging.telemetry.consume
cap.messaging.inference_task.publish
cap.messaging.inference_result.consume
cap.messaging.user_event.publish
cap.messaging.user_event.consume.personal
cap.messaging.broker.manage
```

## 3. 为什么不要直接用 RabbitMQ 资源名命名

不建议定义下面这类权限：

```text
mq.queue.q_teacher_dashboard.read
mq.exchange.x_infer_result.write
```

这类命名会把角色权限体系直接绑死在 broker 拓扑上。

一旦 exchange、queue 或 routing key 改名：

- 角色定义会被迫一起调整
- 权限语义会变得难以理解
- 业务能力和技术资源会混在一起

更合理的做法是：

- 业务权限只表达“这个角色能做什么”
- 由 RabbitMQ 映射表把业务能力翻译成 broker 可识别的授权规则

## 4. RabbitMQ 映射模型

当前使用 `rabbitmq_permission_binding` 表承载 RabbitMQ 授权映射。

每一行表示一条 RabbitMQ 检查规则。

### 4.1 核心字段

| 字段 | 含义 |
|---|---|
| `permission_id` | 关联的业务权限 |
| `check_type` | 检查类型：`user` / `vhost` / `resource` / `topic` |
| `vhost_pattern` | vhost 匹配模式，使用 shell-style wildcard |
| `resource_type` | 资源类型，需要时取 `exchange` / `queue` / `topic` |
| `resource_name_pattern` | queue / exchange 名称匹配模式 |
| `permission_level` | 授权级别：`configure` / `write` / `read` |
| `routing_key_pattern` | `/mq/auth/topic` 使用的 AMQP topic wildcard 模式 |
| `rabbitmq_tag` | `/mq/auth/user` 使用的 RabbitMQ 管理标签 |

### 4.2 匹配规则

- `vhost_pattern` 使用 shell-style wildcard，例如 `*`、`platform-*`
- `resource_name_pattern` 使用 shell-style wildcard
- `routing_key_pattern` 使用 AMQP topic wildcard 语法：
  - `*` 表示恰好匹配一个单词
  - `#` 表示匹配零个或多个单词

## 5. 与 RabbitMQ HTTP Auth Backend 的映射关系

RabbitMQ HTTP Auth Backend 会调用四个接口。

| 接口 | 含义 | 对应映射来源 |
|---|---|---|
| `/mq/auth/user` | 用户认证，以及返回可选管理标签 | `check_type = user` |
| `/mq/auth/vhost` | vhost 访问权限校验 | `check_type = vhost` |
| `/mq/auth/resource` | queue / exchange 的 configure、write、read 校验 | `check_type = resource` |
| `/mq/auth/topic` | topic exchange 上 routing key 级权限校验 | `check_type = topic` |

需要注意：

- RabbitMQ 管理标签不能替代真实的消息读写权限
- 管理标签只影响 management plugin / 管理界面相关能力
- 真正的消息访问控制仍由 `vhost`、`resource`、`topic` 共同决定

## 6. 推荐的 RabbitMQ 拓扑命名规范

为了让权限映射长期稳定，建议 broker 命名保持可预测。

### 6.1 Vhost

```text
/platform
/realtime
/inference
```

### 6.2 Exchange

```text
x.collect.telemetry
x.infer.task
x.infer.result
x.user.event
```

### 6.3 Queue

```text
q.collect.ingest.default
q.infer.worker.default
q.teacher.dashboard.class_123
q.user.event.personal.10001
```

### 6.4 Routing key

```text
collect.telemetry.upload.student
infer.task.image.submit
infer.result.image.student.10001
user.event.profile.updated
```

## 7. 映射示例

业务权限：

```text
cap.messaging.inference_result.consume
```

可能对应的 RabbitMQ 绑定：

```text
check_type=user      rabbitmq_tag=NULL
check_type=vhost     vhost_pattern=/platform
check_type=resource  permission_level=read  resource_name_pattern=q.infer.result.*
check_type=topic     permission_level=read  resource_name_pattern=x.infer.result routing_key_pattern=infer.result.#
```

业务权限：

```text
cap.messaging.broker.manage
```

可能对应的 RabbitMQ 绑定：

```text
check_type=user      rabbitmq_tag=administrator
check_type=vhost     vhost_pattern=*
check_type=resource  permission_level=configure resource_name_pattern=*
check_type=resource  permission_level=write     resource_name_pattern=*
check_type=resource  permission_level=read      resource_name_pattern=*
check_type=topic     permission_level=write     resource_name_pattern=* routing_key_pattern=#
check_type=topic     permission_level=read      resource_name_pattern=* routing_key_pattern=#
```

## 8. 角色分配建议

角色应当被授予业务权限，而不是直接授予 RabbitMQ 资源名。

推荐示例：

- `admin`
  - `cap.messaging.broker.manage`
- `teacher`
  - `cap.messaging.telemetry.consume`
  - `cap.messaging.inference_result.consume`
- `student`
  - `cap.messaging.telemetry.publish`
  - `cap.messaging.user_event.consume.personal`

## 9. 当前仓库中的落地情况

当前仓库已经实现：

- RabbitMQ HTTP Auth Backend 四个接口
  - `/mq/auth/user`
  - `/mq/auth/vhost`
  - `/mq/auth/resource`
  - `/mq/auth/topic`
- `rabbitmq_permission_binding` 模型与 Alembic 迁移
- 以下匹配逻辑
  - 管理标签匹配
  - vhost 通配匹配
  - resource 通配匹配
  - AMQP topic wildcard 匹配

当前仓库还预置了一条初始业务权限：

```text
cap.messaging.broker.manage
```

这条权限已授予 `admin` 角色，并映射为 RabbitMQ 全量管理能力。
