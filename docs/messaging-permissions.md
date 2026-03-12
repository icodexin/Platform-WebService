# Messaging Business Permission Naming and RabbitMQ Mapping

## 1. Goal

This document defines:

- how business permissions related to queue/message workflows should be named
- how business permissions are mapped to RabbitMQ HTTP auth backend checks
- how roles should stay decoupled from RabbitMQ resource details

The design principle is:

- `Role -> Permission` represents business capability
- RabbitMQ-specific authorization is handled by a separate mapping layer

This avoids coupling role definitions directly to exchange, queue, or routing key names.

## 2. Business Permission Naming

### 2.1 Fixed format

Use the following dot-separated format:

```text
cap.<domain>.<resource>.<action>[.<scope>]
```

### 2.2 Segment meaning

| Segment | Meaning |
|---|---|
| `cap` | fixed prefix, means business capability |
| `<domain>` | bounded business context, for example `messaging` |
| `<resource>` | business object, not RabbitMQ internal object |
| `<action>` | allowed business operation |
| `[.<scope>]` | optional extra scope such as `personal`, `admin`, `classroom` |

### 2.3 Naming rules

- use lowercase letters
- use dot-separated segments
- keep segment names business-oriented
- avoid embedding queue, exchange, or routing key names into `permission.code`
- use `snake_case` only inside a segment when a multi-word token is necessary

### 2.4 Recommended examples

```text
cap.messaging.telemetry.publish
cap.messaging.telemetry.consume
cap.messaging.inference_task.publish
cap.messaging.inference_result.consume
cap.messaging.user_event.publish
cap.messaging.user_event.consume.personal
cap.messaging.broker.manage
```

## 3. Why Not Use RabbitMQ Names Directly

Do not define permissions like:

```text
mq.queue.q_teacher_dashboard.read
mq.exchange.x_infer_result.write
```

Those names bind role design directly to broker topology.

When exchange or queue names change, every role assignment becomes brittle.

Instead:

- business permissions describe intent
- a RabbitMQ binding table translates that intent into broker-facing rules

## 4. RabbitMQ Mapping Model

Business permissions are mapped by the `rabbitmq_permission_binding` table.

Each row represents one RabbitMQ authorization rule.

### 4.1 Core fields

| Field | Meaning |
|---|---|
| `permission_id` | linked business permission |
| `check_type` | one of `user`, `vhost`, `resource`, `topic` |
| `vhost_pattern` | shell-style wildcard pattern for vhost |
| `resource_type` | `exchange`, `queue`, or `topic` when needed |
| `resource_name_pattern` | shell-style wildcard for queue/exchange name |
| `permission_level` | `configure`, `write`, or `read` |
| `routing_key_pattern` | AMQP topic wildcard pattern for `/auth/topic` |
| `rabbitmq_tag` | management tag for `/auth/user` only |

### 4.2 Matching rules

- `vhost_pattern` uses shell-style wildcard, for example `*`, `platform-*`
- `resource_name_pattern` uses shell-style wildcard
- `routing_key_pattern` uses AMQP topic wildcard syntax:
  - `*` matches exactly one word
  - `#` matches zero or more words

## 5. Mapping to RabbitMQ HTTP Auth Backend

RabbitMQ HTTP auth backend uses four checks.

| HTTP check | Meaning | Mapping source |
|---|---|---|
| `/auth/user` | user authentication and optional management tags | `check_type = user` |
| `/auth/vhost` | vhost access | `check_type = vhost` |
| `/auth/resource` | queue/exchange configure, write, read | `check_type = resource` |
| `/auth/topic` | topic routing-key level control | `check_type = topic` |

Important:

- RabbitMQ management tags do not replace queue/exchange/topic permissions
- management tags only affect management UI and management-plugin level access
- actual messaging permissions are still decided by `vhost`, `resource`, and `topic`

## 6. Recommended Topology Naming

To keep permission mapping stable, prefer a predictable broker naming style.

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

## 7. Example Mapping

Business permission:

```text
cap.messaging.inference_result.consume
```

Possible RabbitMQ bindings:

```text
check_type=user      rabbitmq_tag=NULL
check_type=vhost     vhost_pattern=/platform
check_type=resource  permission_level=read  resource_name_pattern=q.infer.result.*
check_type=topic     permission_level=read  resource_name_pattern=x.infer.result routing_key_pattern=infer.result.#
```

Business permission:

```text
cap.messaging.broker.manage
```

Possible RabbitMQ bindings:

```text
check_type=user      rabbitmq_tag=administrator
check_type=vhost     vhost_pattern=*
check_type=resource  permission_level=configure resource_name_pattern=*
check_type=resource  permission_level=write     resource_name_pattern=*
check_type=resource  permission_level=read      resource_name_pattern=*
check_type=topic     permission_level=write     resource_name_pattern=* routing_key_pattern=#
check_type=topic     permission_level=read      resource_name_pattern=* routing_key_pattern=#
```

## 8. Role Assignment Guidance

Roles should receive business permissions, not broker resource names.

Recommended examples:

- `admin`:
  - `cap.messaging.broker.manage`
- `teacher`:
  - `cap.messaging.telemetry.consume`
  - `cap.messaging.inference_result.consume`
- `student`:
  - `cap.messaging.telemetry.publish`
  - `cap.messaging.user_event.consume.personal`

## 9. Current Repository Implementation

The repository currently implements:

- RabbitMQ HTTP auth backend endpoints:
  - `/auth/user`
  - `/auth/vhost`
  - `/auth/resource`
  - `/auth/topic`
- `rabbitmq_permission_binding` model and migration
- matching logic for:
  - management tags
  - vhost wildcard
  - resource wildcard
  - AMQP topic wildcard

The repository also seeds one initial permission:

```text
cap.messaging.broker.manage
```

This permission is granted to the `admin` role and mapped to full RabbitMQ broker access.
