from models import User, Admin
from models import BlogPost, Comment, Tag
from sqlalchemy import and_

from database import db_session
from datetime import datetime


class BlogService:
    __instance = None

    def __new__(cls):
        if cls.__instance == None:
            cls.__instance = super(BlogService, cls).__new__(cls)
        return cls.__instance

    def add_post(self, title, content, author, tags=[], make_visible=True):
        blog_post = BlogPost()
        blog_post.author = author
        blog_post.title = title
        blog_post.content = content
        blog_post.is_visible = make_visible
        blog_post.tags = tags
        blog_post.post_date = datetime.now()

        db_session.add(blog_post)
        db_session.commit()

        return blog_post

    def edit_post(self, id, title, content, tags=[], make_visible=True):
        blog_post = self.fetch_post_by_id(id)
        if blog_post is None:
            return None

        blog_post.title = title
        blog_post.content = content
        blog_post.is_visible = make_visible
        blog_post.tags = tags

        db_session.add(blog_post)
        db_session.commit()

        return blog_post

    def delete_post(self, id):
        blog_post = self.fetch_post_by_id(id)
        if blog_post is None:
            return

        db_session.delete(blog_post)
        db_session.commit()

    def fetch_all_posts(self, include_hidden=True):
        if include_hidden:
            return db_session.query(BlogPost).all()
        return db_session.query(BlogPost).filter(BlogPost.is_visible == True).all()

    def fetch_post_by_id(self, id):
        return db_session.query(BlogPost).filter(BlogPost.id == id).first()

    def add_comment(self, post_id, content, user):
        blog_post = self.fetch_post_by_id(post_id)
        if blog_post is None:
            return None

        if blog_post.comments is None:
            blog_post.comments = []

        comment = Comment()
        comment.blog_post = blog_post
        comment.content = content
        comment.user = user
        comment.comment_date = datetime.now()

        db_session.add(comment)
        db_session.commit()

        return blog_post


class UserService:
    __instance = None

    def __new__(cls):
        if cls.__instance == None:
            cls.__instance = super(UserService, cls).__new__(cls)
        return cls.__instance

    def sign_up(self, username, password, display_name, phone, email, is_admin=False):
        user = Admin() if is_admin else User()
        user.id = self._get_next_user_id()
        user.username = username
        user.password = password
        user.display_name = display_name
        user.phone = phone
        user.email = email

        db_session.add(user)
        db_session.commit()

        return user

    def is_default_admin_exists(self):
        count = db_session().query(Admin).filter(Admin.username == 'admin').count()

        return count != 0

    def fetch_all_users(self):
        return db_session.query(User).all()

    def fetch_user_by_id(self, id):
        return db_session().query(User).filter(User.id == id).first()

    def login(self, username, password):
        return db_session.query(User).filter(and_(User.username == username, User.password == password)).first()

    def _get_next_user_id(self):
        count = db_session.query(User).filter(User.id != None).count()
        return count+1


blog_service = BlogService()
user_service = UserService()
