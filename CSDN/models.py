from contextlib import contextmanager
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from CSDN.extensions import whooshee


class SQLAlchemy(_SQLAlchemy):
    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


db = SQLAlchemy()


class Follow(db.Model):
    follower_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    followed_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    follower = relationship('User', foreign_keys=[follower_id], back_populates='following', lazy='joined')
    followed = relationship('User', foreign_keys=[followed_id], back_populates='followers', lazy='joined')


@whooshee.register_model('username')
class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True, index=True)
    name = Column(String(30))
    username = Column(String(30), unique=True)
    _password = Column('password', String(128))
    timestamp = Column(DateTime, default=datetime.utcnow)
    website = Column(String(255))
    bio = Column(String(120))
    location = Column(String(50))
    public_collections = Column(Boolean, default=True)
    receive_comment_notification = Column(Boolean, default=True)
    receive_follow_notification = Column(Boolean, default=True)
    receive_collect_notification = Column(Boolean, default=True)
    locked = Column(Boolean, default=False)
    active = Column(Boolean, default=True)

    role_id = Column(Integer, ForeignKey('role.id'))

    role = relationship('Role', back_populates='users')
    posts = relationship('Post', back_populates='user', cascade='all')
    comments = relationship('Comment', back_populates='user')
    collections = relationship('Collect', back_populates='collector', cascade='all')
    following = relationship('Follow', foreign_keys=[Follow.follower_id],
                             back_populates='follower', lazy='dynamic', cascade='all')
    followers = relationship('Follow', foreign_keys=[Follow.followed_id],
                             back_populates='followed', lazy='dynamic', cascade='all')
    notifications = relationship('Notification', back_populates='receiver')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.set_role()
        self.follow(self)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self._password, password)

    def set_attrs(self, attr_dict):
        for key, value in attr_dict.items():
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)

    def set_role(self):
        if self.role is None:
            if self.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
                self.role = Role.query.filter_by(name='Admin').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
            db.session.commit()

    @property
    def is_admin(self):
        return self.role.name == 'Admin'

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions

    def collect(self, post):
        if not self.is_collecting(post):
            collect = Collect(collector=self, collected=post)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, post):
        collect = Collect.query.with_parent(self).filter_by(collected_id=post.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def is_collecting(self, post):
        return Collect.query.with_parent(self).filter_by(collected_id=post.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        if user.id is None:
            return False
        return self.following.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def lock(self):
        self.locked = True
        self.role = Role.query.filter_by(name='Locked').first()
        db.session.commit()

    def unlock(self):
        self.locked = False
        self.role = Role.query.filter_by(name='User').first()
        db.session.commit()

    @property
    def is_active(self):
        return self.active

    def block(self):
        self.active = False
        db.session.commit()

    def unblock(self):
        self.active = True
        db.session.commit()


roles_permissions = db.Table('roles_permissions',
                             Column('role_id', ForeignKey('role.id'), primary_key=True),
                             Column('permission_id', ForeignKey('permission.id'), primary_key=True)
                             )


class Permission(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)

    roles = relationship('Role', secondary=roles_permissions, back_populates='permissions')


class Role(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)

    permissions = relationship('Permission', secondary=roles_permissions, back_populates='roles')
    users = relationship('User', back_populates='role')

    @staticmethod
    def init_role():
        roles_permissions_map = {
            'Locked':['FOLLOW', 'COLLECT'],
            'User':['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
            'Admin':['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'ADMIN']
        }
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()


class Collect(db.Model):
    collector_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    collected_id = Column(Integer, ForeignKey('post.id'), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    collector = relationship('User', back_populates='collections', lazy='joined')
    collected = relationship('Post', back_populates='collectors', lazy='joined')


@whooshee.register_model('title')
class Post(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(60))
    body = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    can_comment = Column(Boolean, default=True)
    flag = Column(Integer, default=0)

    category_id = Column(Integer, ForeignKey('category.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    category = relationship('Category', back_populates='posts')
    user = relationship('User', back_populates='posts')
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    collectors = relationship('Collect', back_populates='collected', cascade='all')

    @staticmethod
    def previous(pid):
        post = Post.query.get_or_404(pid)
        post_previous = Post.query.with_parent(post.user).filter(
            Post.id < pid).order_by(Post.id.desc()).first()
        return post_previous

    @staticmethod
    def next(pid):
        post = Post.query.get_or_404(pid)
        post_next = Post.query.with_parent(post.user).filter(
            Post.id > pid).order_by(Post.id.asc()).first()
        return post_next


class Category(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(30))

    posts = relationship('Post', back_populates='category')

    def delete(self):
        if self.id != 1:
            with db.auto_commit():
                default_category = Category.query.get(1)
                posts = self.posts[:]
                for post in posts:
                    post.category = default_category
                db.session.delete(self)
        else:
            pass


class Comment(db.Model):
    id = Column(Integer, primary_key=True)
    body = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    flag = Column(Integer, default=0)

    post_id = Column(Integer, ForeignKey('post.id'))
    user_id = Column(Integer, ForeignKey('user.id'))

    post = relationship('Post', back_populates='comments')
    user = relationship('User', back_populates='comments')


class Notification(db.Model):
    id = Column(Integer, primary_key=True)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    receiver_id = Column(Integer, ForeignKey('user.id'))

    receiver = relationship('User', back_populates='notifications')

