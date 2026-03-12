# WebService Repository Context

Last verified: 2026-03-12

## 1. Repository Role

This repository is the central backend service for the "Collect Platform" project.

Current implemented role:
- User identity management
- Authentication and token issuance
- RBAC role assignment and token revocation
- Async PostgreSQL/TimescaleDB persistence

Planned role, not yet fully implemented in this repository:
- WebSocket real-time data stream access layer
- RabbitMQ-based message integration
- Deep learning inference service access or orchestration
- Streaming/media coordination with MediaMTX

Important:
- Do not assume WebSocket, inference, or full RabbitMQ business flows are already complete.
- The codebase currently delivers a user/auth service foundation, plus some infrastructure preparation for future expansion.

## 2. Current Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy 2.x async ORM
- asyncpg
- Alembic
- JWT (`python-jose`)
- Argon2 password hashing (`pwdlib`)
- APScheduler
- aio-pika and msgpack are already declared as dependencies, but their usage is not yet a completed end-to-end feature in the current app wiring.

## 3. Runtime and Infrastructure Baseline

Application entry:
- `app/main.py`

Configured infrastructure:
- PostgreSQL-compatible database via TimescaleDB container
- RabbitMQ with management plugin and MQTT plugin enabled
- MediaMTX for RTSP/RTMP/HLS/WebRTC related media transport

Current database baseline:
- PostgreSQL / TimescaleDB

Historical note:
- Earlier repository descriptions had mentioned MySQL, but the repository is now documented and implemented consistently around PostgreSQL/TimescaleDB.
- When modifying or extending this project, treat the code, migrations, settings, and `docker-compose.yml` as the source of truth for database behavior unless an explicit database migration is introduced later.

## 4. Project Structure

### `app/`
Core application code.

### `app/api/`
HTTP route layer.

Current routes:
- `auth.py`: login, refresh token, logout
- `users.py`: user creation and current-user query
- `rabbitmq.py`: RabbitMQ HTTP auth backend endpoints (`/auth/user`, `/auth/vhost`, `/auth/resource`, `/auth/topic`)

Rule:
- Keep route handlers thin.
- Request validation and response shaping belong here.
- Business orchestration should stay in `services/`.

### `app/services/`
Business service layer.

Current responsibilities:
- `auth.py`: credential validation, JWT verification, token revocation
- `user.py`: user creation orchestration, current user resolution, active-user checks
- `rabbitmq_auth.py`: RabbitMQ HTTP auth backend decision logic and binding-based permission matching

Rule:
- Put cross-DAO business logic here.
- Authentication, authorization, user profile composition, and future WebSocket session-level policies should be handled here instead of in API handlers.

### `app/dao/`
Persistence access layer.

Current responsibilities:
- `user.py`: query users/roles and create teacher or student records
- `token.py`: token blocklist persistence and cleanup

Rule:
- Keep SQLAlchemy query details and transaction boundaries here.
- Avoid embedding HTTP semantics in DAO code.

### `app/models/`
SQLAlchemy ORM models.

Current model groups:
- User base model: `User`
- User subtype profiles: `StudentProfile`, `TeacherProfile`
- RBAC models: `Role`, `Permission`, `UserRole`, `RolePermission`
- Messaging authorization model: `RabbitMQPermissionBinding`
- Security model: `TokenBlocklist`

Current domain model:
- A user has one `user_type` (`student`, `teacher`, `admin`)
- Student and teacher extra fields are split into dedicated profile tables
- Roles are assigned through a join table
- Revoked JWTs are stored in a blocklist table instead of using pure stateless token invalidation

### `app/schemas/`
Pydantic request/response schemas.

Current pattern:
- Input models are split by role-specific payloads
- `UserCreate` and `UserResponse` are discriminated unions keyed by `user_type`
- Password hashing is performed during schema validation when plaintext input is received

### `app/core/`
Application core facilities.

Current files:
- `config.py`: environment-backed settings
- `db.py`: async engine, session factory, ORM base, timestamp mixin
- `security.py`: password hashing and JWT creation/validation helpers

### `app/common/`
Shared enums and constants.

### `app/utils/`
Utility helpers. Currently lightweight and not a major architectural center.

### `alembic/`
Database migration management.

Current migration intent:
- Initial schema creation
- Initial RBAC seed data and bootstrap admin account

### `test/`
Manual HTTP test assets (`.http` and environment file), not a full automated test suite.

## 5. Application Behavior Today

### Authentication
- OAuth2 password flow style login endpoint at `/auth/token`
- JWT access token and refresh token issuance
- Refresh flow revokes the previous refresh token before issuing a new pair
- Logout revokes both access token and refresh token

### User Management
- Supports creating student and teacher users
- Admin account is bootstrapped by Alembic seed migration
- Current-user endpoint returns role-specific response shape

### Security Model
- Passwords use Argon2 hashing
- Revoked tokens are persisted in `token_blocklist`
- A scheduler removes expired blocklist records every hour at application runtime

### Data Layer
- Async SQLAlchemy session per request via dependency injection
- PostgreSQL enums and relational schema managed by Alembic

## 6. Boundaries and Current Gaps

These capabilities are not fully established yet:
- No WebSocket endpoint module is wired into the app
- No inference service module exists yet
- RabbitMQ HTTP auth backend exists, but business-specific permission seeds and broker topology conventions are still at an early stage
- No complete permission-check middleware/dependency layer is present yet
- No comprehensive automated test suite is present yet

Be careful:
- Some repository descriptions are broader than the currently delivered code.

## 7. Recommended Extension Direction

When adding new capabilities, preserve the current layering and split responsibilities explicitly.

Recommended module placement:
- WebSocket gateway: `app/ws/` or `app/realtime/`
- Message bus integration: `app/messaging/`
- Inference service adapter or orchestration: `app/inference/`
- Background jobs beyond token cleanup: `app/jobs/`

Recommended rules:
- Reuse `app/core/config.py` for all new runtime settings
- Reuse current JWT and user identity model for WebSocket handshake authentication
- Keep inference execution out of the main request thread when work is heavy or latency-sensitive
- Use service-layer abstractions before introducing direct RabbitMQ, model-serving, or stream-server calls into API handlers
- If future features need authorization, extend the RBAC model instead of duplicating ad hoc permission logic

## 8. Operational Notes for Future Agents

When analyzing or editing this repository, assume the following:
- This is currently a backend foundation service, not yet a full real-time or inference platform
- The most stable, production-like part of the codebase is user/auth/RBAC/data-modeling
- Infrastructure declarations are ahead of application integration in several areas
- Schema and business rules should be inferred from `app/models/`, `app/schemas/`, `app/services/`, and Alembic migrations first, not from the README
- Messaging business permission naming and RabbitMQ mapping rules are documented in `docs/messaging-permissions.md`
- RabbitMQ authorization is implemented as `Role -> Permission -> rabbitmq_permission_binding`, not by binding roles directly to queue or exchange names

Preferred reading order for future work:
1. `app/main.py`
2. `app/core/`
3. `app/api/`
4. `app/services/`
5. `app/dao/`
6. `app/models/`
7. `alembic/versions/`

## 9. Short Summary

This repository currently is:
- An async FastAPI user/auth service
- Backed by PostgreSQL/TimescaleDB
- Using JWT + token blocklist
- Structured with API / Service / DAO / Model / Schema layering
- Prepared for RabbitMQ and streaming infrastructure, but not yet fully expanded into WebSocket and inference service delivery
