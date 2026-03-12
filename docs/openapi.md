# API 文档

本文档基于当前代码实现整理，聚焦认证、用户与权限管理相关接口。

基础信息：

- 服务前缀：`/api` 用于业务接口与文档接口
- Swagger UI：`GET /api/docs`
- OpenAPI JSON：`GET /api/openapi.json`
- 认证方式：Bearer Token

## 认证模型

### Access Token

- 通过 `POST /auth/token` 获取
- 用于访问受保护接口
- 请求头格式：

```http
Authorization: Bearer <access_token>
```

### Refresh Token

- 通过 `POST /auth/token` 获取
- 通过 `POST /auth/refresh` 刷新
- 通过 `POST /auth/logout` 撤销

### 可选登录态

`POST /api/users/` 同时支持匿名与已登录调用：

- 匿名：可注册普通用户
- 已登录：仍可注册普通用户
- 已登录且具有 `sys.user.create.admin`：可创建管理员

## 权限模型

当前内置用户/权限管理权限如下：

| 权限码 | 含义 |
| --- | --- |
| `sys.permission.manage` | 权限管理 |
| `sys.role.manage` | 角色管理 |
| `sys.user.read.self` | 读取当前用户 |
| `sys.user.read.all` | 读取全部用户 |
| `sys.user.update.self` | 修改当前用户 |
| `sys.user.update.all` | 修改全部用户 |
| `sys.user.deactivate.self` | 注销当前用户账号 |
| `sys.user.deactivate.all` | 注销全部用户账号 |
| `sys.user.create.admin` | 创建管理员用户 |
| `sys.user.role.update.all` | 修改用户角色 |

### 范围语义

- `SELF`：只能操作自己
- `ALL`：可以操作全部用户，并且包含对自己的操作权限

例如：

- 拥有 `sys.user.update.all` 的用户，可以修改自己，也可以修改别人
- 拥有 `sys.user.update.self` 的用户，只能修改自己

### 默认角色授权

| 角色 | 默认权限 |
| --- | --- |
| `admin` | `permission.manage` `role.manage` `read.self` `read.all` `update.self` `update.all` `deactivate.self` `deactivate.all` `create.admin` `role.update.all` |
| `teacher` | `read.self` `update.self` `deactivate.self` |
| `student` | `read.self` `update.self` `deactivate.self` |

## 认证接口

### `POST /auth/token`

用户登录，返回访问令牌和刷新令牌。

请求类型：

- `application/x-www-form-urlencoded`

表单字段：

| 字段 | 说明 |
| --- | --- |
| `username` | 统一身份 ID |
| `password` | 密码 |

响应示例：

```json
{
  "access_token": "xxx",
  "refresh_token": "xxx",
  "token_type": "bearer"
}
```

### `POST /auth/refresh`

刷新访问令牌与刷新令牌。

请求类型：

- `application/x-www-form-urlencoded`

表单字段：

| 字段 | 说明 |
| --- | --- |
| `refresh_token` | 刷新令牌 |

### `POST /auth/logout`

注销登录，撤销当前 access token 与传入的 refresh token。

请求要求：

- Bearer access token
- 表单字段 `refresh_token`

## 用户接口

### `POST /api/users/`

创建用户。

支持用户类型：

- `student`
- `teacher`
- `admin`

创建规则：

- 匿名可创建 `student`、`teacher`
- 已登录用户可创建 `student`、`teacher`
- 只有拥有 `sys.user.create.admin` 的已登录用户才能创建 `admin`

请求体使用 discriminated union，按 `user_type` 区分。

学生示例：

```json
{
  "user_type": "student",
  "unified_id": "20269992",
  "password": "123456",
  "name": "普通学生测试",
  "gender": "unknown",
  "student_type": "undergraduate",
  "college": "计算机学院",
  "major": "网络工程",
  "enrollment_year": 2026
}
```

教师示例：

```json
{
  "user_type": "teacher",
  "unified_id": "T20269992",
  "password": "123456",
  "name": "普通教师测试",
  "gender": "unknown",
  "department": "计算机学院",
  "title": "讲师"
}
```

管理员示例：

```json
{
  "user_type": "admin",
  "unified_id": "admin02",
  "password": "123456",
  "name": "管理员二号",
  "gender": "unknown"
}
```

### `GET /api/users/`

分页查询用户列表。

权限要求：

- `sys.user.read.all`

查询参数：

| 参数 | 说明 |
| --- | --- |
| `page` | 页码，默认 `1` |
| `page_size` | 每页条数，默认 `20`，最大 `100` |
| `keyword` | 按 `unified_id` 或 `name` 模糊检索 |
| `user_type` | 按用户类型筛选 |
| `is_active` | 按账号状态筛选 |

### `GET /api/users/me`

获取当前登录用户信息。

权限要求：

- `sys.user.read.self`
- 或 `sys.user.read.all`

### `GET /api/users/{user_id}`

获取指定用户详情。

权限要求：

- 读自己：`sys.user.read.self` 或 `sys.user.read.all`
- 读他人：`sys.user.read.all`

### `PUT /api/users/{user_id}`

更新指定用户信息。

权限要求：

- 改自己：`sys.user.update.self` 或 `sys.user.update.all`
- 改他人：`sys.user.update.all`

请求体说明：

- 可更新基础字段：`unified_id`、`password`、`name`、`gender`、`birthdate`、`is_active`
- 学生可更新学生扩展字段：`student_type`、`college`、`major`、`enrollment_year`
- 教师可更新教师扩展字段：`department`、`title`

业务约束：

- 当前用户不能通过此接口修改自己的 `is_active`
- 注销账号必须使用注销接口
- 学生不能更新教师资料字段
- 教师不能更新学生资料字段
- 管理员没有学生/教师扩展资料字段

### `GET /api/users/{user_id}/roles`

获取指定用户的角色绑定。

权限要求：

- 读自己：`sys.user.read.self` 或 `sys.user.read.all`
- 读他人：`sys.user.read.all`

响应说明：

- `immutable_role` 表示该用户随 `user_type` 固定绑定的系统角色
- `roles` 表示当前全部角色集合，包含 `immutable_role`

响应示例：

```json
{
  "user_id": 12,
  "immutable_role": {
    "id": 3,
    "code": "student",
    "name": "学生",
    "is_system": true
  },
  "roles": [
    {
      "id": 3,
      "code": "student",
      "name": "学生",
      "is_system": true
    },
    {
      "id": 8,
      "code": "biz.research.viewer",
      "name": "科研只读角色",
      "is_system": false
    }
  ]
}
```

### `PUT /api/users/{user_id}/roles`

整体更新指定用户的角色绑定。

权限要求：

- `sys.user.role.update.all`

请求体示例：

```json
{
  "role_ids": [8, 9]
}
```

业务约束：

- 用户初始绑定的系统角色不可移除或替换
- 例如学生始终保留 `student`，教师始终保留 `teacher`，管理员始终保留 `admin`
- 不允许给用户额外分配其他系统角色
- `role_ids` 只需要传“希望附加的角色集合”，系统会自动保留该用户不可变的系统角色
- 传入的角色 ID 必须全部存在

### `POST /api/users/me/deactivate`

注销当前登录用户账号。

权限要求：

- `sys.user.deactivate.self`
- 或 `sys.user.deactivate.all`

行为说明：

- 内部实现不是物理删除
- 实际效果为将 `is_active` 设为 `false`

响应示例：

```json
{
  "detail": "User account deactivated successfully"
}
```

### `POST /api/users/{user_id}/deactivate`

注销指定用户账号。

权限要求：

- 注销自己：`sys.user.deactivate.self` 或 `sys.user.deactivate.all`
- 注销他人：`sys.user.deactivate.all`

行为说明：

- 内部实现不是物理删除
- 实际效果为将 `is_active` 设为 `false`

## 权限管理接口

权限管理接口统一要求：

- `sys.permission.manage`

### `GET /api/permissions/`

分页查询权限列表。

查询参数：

| 参数 | 说明 |
| --- | --- |
| `page` | 页码，默认 `1` |
| `page_size` | 每页条数，默认 `20`，最大 `100` |
| `keyword` | 按权限编码或名称模糊检索 |

### `POST /api/permissions/`

创建权限。

请求体示例：

```json
{
  "code": "biz.example.manage",
  "name": "示例业务管理"
}
```

### `GET /api/permissions/{permission_id}`

查询权限详情。

### `PUT /api/permissions/{permission_id}`

更新权限。

### `DELETE /api/permissions/{permission_id}`

删除权限。

说明：

- 系统内置权限不允许修改或删除
- 已绑定角色的权限不能直接删除

## 角色管理接口

角色管理接口统一要求：

- `sys.role.manage`

### `GET /api/roles/`

分页查询角色列表。

查询参数：

| 参数 | 说明 |
| --- | --- |
| `page` | 页码，默认 `1` |
| `page_size` | 每页条数，默认 `20`，最大 `100` |
| `keyword` | 按角色编码或名称模糊检索 |

响应说明：

- 返回角色基础信息
- 返回角色当前绑定的权限列表
- 返回 `permission_count`、`user_count`
- 返回 `is_system` 标识是否为内置角色

### `POST /api/roles/`

创建角色。

请求体示例：

```json
{
  "code": "biz.ops.viewer",
  "name": "运维只读角色",
  "permission_ids": [3, 12]
}
```

说明：

- `permission_ids` 可为空数组
- 所有传入的权限 ID 都必须存在
- 角色编码必须唯一

### `GET /api/roles/{role_id}`

查询角色详情。

返回内容包含：

- 角色基础信息
- 角色权限列表
- 绑定用户数量
- 是否内置角色

### `PUT /api/roles/{role_id}`

更新角色。

可更新字段：

- `code`
- `name`
- `permission_ids`

说明：

- `permission_ids` 传入后会整体覆盖该角色当前的权限绑定
- 系统内置角色不允许修改
- 角色编码修改后仍要求全局唯一

请求体示例：

```json
{
  "name": "运维只读角色-更新",
  "permission_ids": [12]
}
```

### `DELETE /api/roles/{role_id}`

删除角色。

说明：

- 系统内置角色不允许删除
- 已绑定用户的角色不允许删除
- 未绑定用户的自定义角色可以删除

## 常见响应语义

| 状态码 | 含义 |
| --- | --- |
| `200` | 请求成功 |
| `201` | 创建成功 |
| `400` | 参数错误或业务约束不满足 |
| `401` | 未认证或 token 无效 |
| `403` | 已认证但无权限 |
| `404` | 资源不存在 |

## 已验证的典型行为

- 管理员可以登录、查看自己、查看列表、查看他人、修改自己、创建管理员、停用他人
- 管理员可以查看用户当前角色，并在保留系统角色的前提下为用户增删自定义角色
- 管理员可以查看角色列表、创建角色、修改角色权限、删除未绑定用户的自定义角色
- 学生可以登录、查看自己、修改自己，不能查看他人、不能看列表、不能创建管理员、不能停用他人
- 教师可以登录、查看自己、修改自己，不能查看他人、不能看列表、不能停用他人
- 匿名用户可以注册普通学生/教师，不能访问受保护接口，不能创建管理员
