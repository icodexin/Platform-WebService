from sqlalchemy import Column, String, Enum, Date, TIMESTAMP, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(Base):
    """用户-角色关系表"""
    __tablename__ = 'user_role'
    user_id = Column(String(20), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.role_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    created_by = Column(String(20), nullable=False, comment="创建者")
    updated_by = Column(String(20), nullable=False, comment="更新者")


class RolePermission(Base):
    """角色-权限关系表"""
    __tablename__ = 'role_permission'
    role_id = Column(Integer, ForeignKey('roles.role_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    perm_id = Column(Integer, ForeignKey('permissions.perm_id', ondelete='CASCADE', onupdate='CASCADE'),
                     primary_key=True)

    created_by = Column(String(20), nullable=False, comment="创建者")
    updated_by = Column(String(20), nullable=False, comment="更新者")


class UserModel(Base):
    """用户表"""
    __tablename__ = 'users'

    user_id = Column(String(20), primary_key=True, comment="用户ID")
    hashed_password = Column(String(128), nullable=False, comment="Hash密码")
    name = Column(String(50), nullable=False, comment="姓名")
    status = Column(Enum('ENABLED', 'DISABLED', name='user_status'), default='ENABLED', nullable=False,
                    comment="账号状态")

    gender = Column(Enum('M', 'F', 'U', name='gender'), default='U', comment="性别")
    birthdate = Column(Date, comment="出生日期")
    college = Column(String(50), comment="学院")
    stu_type = Column(Enum('UNDERGRADUATE', 'POSTGRADUATE', 'DOCTORAL', name='student_type'), comment="学生类型")
    grade = Column(Integer, comment="年级")
    major = Column(String(50), comment="专业")

    last_login_at = Column(TIMESTAMP, comment="最后登录时间")
    last_login_ip = Column(String(45), comment="最后登录IP")

    created_by = Column(String(20), nullable=False, comment="创建者")
    updated_by = Column(String(20), nullable=False, comment="更新者")

    roles = relationship('RoleModel', secondary='user_role', back_populates='users')


class RoleModel(Base):
    """角色表"""
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True, autoincrement=True, comment="角色ID")
    role_name = Column(String(20), unique=True, nullable=False, comment="角色名称")
    description = Column(String(255), comment="角色描述")

    created_by = Column(String(20), nullable=False, comment="创建者")
    updated_by = Column(String(20), nullable=False, comment="更新者")

    users = relationship('UserModel', secondary='user_role', back_populates='roles')
    permissions = relationship('Permission', secondary='role_permission', back_populates='roles')


class Permission(Base):
    """权限表"""
    __tablename__ = 'permissions'

    perm_id = Column(Integer, primary_key=True, autoincrement=True, comment="权限ID")
    perm_name = Column(String(50), unique=True, nullable=False, comment="权限名称")
    description = Column(String(255), comment="权限描述")

    created_by = Column(String(20), nullable=False, comment="创建者")
    updated_by = Column(String(20), nullable=False, comment="更新者")

    roles = relationship('RoleModel', secondary='role_permission', back_populates='permissions')
