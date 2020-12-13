from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, event
# from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import relationship
import sqlalchemy
from database import Base
from collections import defaultdict
from sqlalchemy.sql.schema import Table


def receive_mapper_configured(mapper, class_):
    mapper.polymorphic_map = defaultdict(
        lambda: mapper, mapper.polymorphic_map)
    # to prevent 'incompatible polymorphic identity' warning, not necessary
    mapper._validate_polymorphic_identity = None


def polymorphic_fallback(mapper_klass):
    event.listens_for(mapper_klass, 'mapper_configured')(
        receive_mapper_configured)
    return mapper_klass


@polymorphic_fallback
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    username = Column(String, unique=True)
    password = Column(String, nullable=False)
    display_name = Column(String)
    phone = Column(String(10), unique=True)
    email = Column(String(50), unique=True, nullable=False)
    reputation_score = Column(Integer)
    comments = relationship("Comment", back_populates="user")
    social_media = relationship("UserSocialMedia", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def __init__(self):
        self.type = "User"

    def add_reputation_score(self, score):
        self.reputation_score = self.reputation_score + score

    def __repr__(self):
        return "Username: {} Displayname:{}, Type:{}, Email:{}".format(self.username, self.display_name, self.type, self.email)


class Admin(User):
    blog_posts = relationship("BlogPost", back_populates="author")

    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }

    def __init__(self):
        self.blog_posts = []


class BlogPost(Base):
    __tablename__ = 'blog_posts'

    def __init__(self):
        self.tags = []
        self.comments = []

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_date = Column(DateTime)
    title = Column(String, nullable=False)
    content = Column(Text)
    is_visible = Column(Boolean)
    author_id = Column(Integer, ForeignKey('users.id'))

    author = relationship("Admin", back_populates="blog_posts")
    tags = relationship("Tag", back_populates="blog_post")
    comments = relationship("Comment", back_populates="blog_post")
    likes = relationship("PostLike", back_populates="blog_post")
    external_references = relationship(
        "ExternalReference", back_populates="blog_post")


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String)
    comment_date = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    blog_post_id = Column(Integer, ForeignKey('blog_posts.id'))

    user = relationship("User", back_populates="comments")
    blog_post = relationship("BlogPost", back_populates="comments")


class PostLike(Base):
    __tablename__ = 'post_likes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    blog_post_id = Column(Integer, ForeignKey('blog_posts.id'))

    blog_post = relationship("BlogPost", back_populates="likes")
    user = relationship("User")


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag = Column(String)
    blog_post_id = Column(Integer, ForeignKey('blog_posts.id'))

    blog_post = relationship("BlogPost", back_populates="tags")


class ExternalReference(Base):
    __tablename__ = 'external_references'

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String)
    url = Column(String)
    blog_post_id = Column(Integer, ForeignKey('blog_posts.id'))

    blog_post = relationship("BlogPost", back_populates="external_references")


class BadgeMaster(Base):
    __tablename__ = 'badge_master'

    id = Column(Integer, primary_key=True, autoincrement=True)
    badge = Column(String)


class UserBadge(Base):
    __tablename__ = 'user_badges'

    id = Column(Integer, primary_key=True, autoincrement=True)
    badge_id = Column(Integer, ForeignKey('badge_master.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

    badge = relationship("BadgeMaster")
    user = relationship("User", back_populates="badges")


class UserSocialMedia(Base):
    __tablename__ = 'user_social_media'

    id = Column(Integer, primary_key=True, autoincrement=True)
    handle = Column(String)
    social_media_id = Column(Integer, ForeignKey('social_media_master.id'))
    user_id = Column(Integer, ForeignKey('users.id'))

    social_media = relationship("SocialMediaMaster")
    user = relationship("User", back_populates="social_media")


class SocialMediaMaster(Base):
    __tablename__ = 'social_media_master'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


def create_tables(engine):
    Base.metadata.create_all(engine)
