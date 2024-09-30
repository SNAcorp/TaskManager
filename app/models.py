import datetime
from sqlalchemy import (Column, Integer, String, Boolean, ForeignKey, DateTime, Table)
from sqlalchemy.orm import (relationship, backref)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Связующая таблица между пользователями и группами (многие ко многим)
# group_user_association = Table(
#     'group_user_association',
#     Base.metadata,
#     Column('user_id', Integer, ForeignKey('users.id')),
#     Column('group_id', Integer, ForeignKey('groups.id')),
#     Column('role', String, default='member')  # роль участника: 'member', 'admin', 'creator'
# )


class User(Base):
    """
    Модель пользователя
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    role = Column(String, default="user")
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=False)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    block_date = Column(DateTime, nullable=True)

    # groups = relationship("Group", secondary=group_user_association, back_populates="members")


class Task(Base):
    """
    Модель задания для пользователя
    """
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    assigner_id = Column(Integer, nullable=False)  # Человек, выдавший задачу
    description = Column(String, nullable=True)
    deadline = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", backref="tasks")
    subtasks = relationship("Subtask", backref="task", cascade="all, delete-orphan")


class Subtask(Base):
    """
    Модель подпункта задания
    """
    __tablename__ = "subtasks"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    name = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False)


class Notification(Base):
    """
    Модель уведомлений для пользователя
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кому отправлено уведомление
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Если уведомление связано с задачей
    content = Column(String, nullable=False)  # Текст уведомления
    type = Column(String, nullable=False)  # Тип уведомления, например, "task_created", "task_completed"
    is_read = Column(Boolean, default=False)  # Прочитано или нет
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)  # Время создания уведомления

    user = relationship("User", backref="notifications")
    task = relationship("Task", backref="notifications", foreign_keys=[task_id])

# class Group(Base):
#     """
#     Модель группы
#     """
#     __tablename__ = "groups"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
#     creator = relationship("User", backref=backref("created_groups", lazy='dynamic'))
#
#     members = relationship("User", secondary=group_user_association, back_populates="groups")
#
#     def add_member(self, user, role='member'):
#         """Добавить пользователя в группу с указанной ролью."""
#         association = group_user_association.insert().values(user_id=user.id, group_id=self.id, role=role)
#         self.members.append(user)
#
#     def add_admin(self, user):
#         """Назначить пользователя администратором группы."""
#         self.add_member(user, role='admin')
#
#     def is_admin(self, user):
#         """Проверить, является ли пользователь администратором."""
#         return any(role == 'admin' for role in [assoc.role for assoc in user.groups if assoc.id == self.id])