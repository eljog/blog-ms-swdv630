from models import User, Admin
from models import BlogPost, Comment, Tag
from sqlalchemy import and_

from database import db_session
from datetime import datetime


class BlogService:
    '''
    A service provider class that provides APIs for blog operations, such as create, edit, and delete post, add/remove comments etc. 
    This is a singleton class.
    '''

    __instance = None

    def __new__(cls):
        if cls.__instance == None:
            cls.__instance = super(BlogService, cls).__new__(cls)
        return cls.__instance

    def add_post(self, title, content, author, tags=[], make_visible=True):
        '''
        Create a new blog post

        Parameters
        ----------
        title: str,
            Blog post title.
        content: str,
            Blog post content.
        author : Admin,
            Admin user who is authring the post.
        tags : list,
            A list of Tag objects, defaults to empty list.
        make_visible: Boolean,
            Whether to make the post visible to public (publish), defaults to True.

        Returns
        -------
        BlogPost
            The blog post object that is added.
        '''

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

    def edit_post(self, id, title, content, tags, make_visible):
        '''
        Edit a blog post

        Parameters
        ----------
        id: int,
            ID of the log post.
        title: str,
            Blog post title.
        content: str,
            Blog post content.
        tags : list,
            A list of Tag objects.
        make_visible: Boolean,
            Whether to make the post visible to public (publish) or not.

        Returns
        -------
        BlogPost
            The blog post object that is edited.
        '''

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
        '''
        Delete a blog post

        Parameters
        ----------
        id: int,
            ID of the blog post.
        '''

        blog_post = self.fetch_post_by_id(id)
        if blog_post is None:
            return

        db_session.delete(blog_post)
        db_session.commit()

    def fetch_all_posts(self, include_hidden=True):
        '''
        Fetch all a blog posts

        Parameters
        ----------
        include_hidden: Boolean,
            If True, unpublished posts will be included

        Returns
        -------
        list
            A list of BlogPost objects.
        '''

        if include_hidden:
            return db_session.query(BlogPost).all()
        return db_session.query(BlogPost).filter(BlogPost.is_visible == True).all()

    def fetch_post_by_id(self, id):
        '''
        Fetch a blog post by id.

        Parameters
        ----------
        id: int,
            ID of the blog post.

        Returns
        -------
        BlogPost
            The matching blog post. None if no match found.
        '''

        return db_session.query(BlogPost).filter(BlogPost.id == id).first()

    def add_comment(self, post_id, content, user):
        '''
        Add a comment to a blog post

        Parameters
        ----------
        post_id: int,
            ID of the blog post.
        content: str,
            The body of the comment.
        user: User,
            The user who is making the comment.

        Returns
        -------
        BlogPost
            The blog post object to which the comment is added.
        '''

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
    '''
    A service provider class that provides APIs for user operations, such as signup, login etc. 
    This is a singleton class.
    '''

    __instance = None

    def __new__(cls):
        if cls.__instance == None:
            cls.__instance = super(UserService, cls).__new__(cls)
        return cls.__instance

    def sign_up(self, username, password, display_name, phone, email, is_admin=False):
        '''
        Register/sign up as a new user.

        Parameters
        ----------
        username: str, 
            Unique username which will be used for loging in.
        password: str,
            User's password.
        display_name: str,
            User's display name.
        phone: str,
            User's phone, must be unique.
        email: : str,
            User's email id, must be unique.
        is_admin: Boolean,
            If True user will be registered as admin. Defaults to False.

        Returns
        -------
        User/Admin
            The user record that is created
        '''

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
        '''
        Check whether the default admin user exists in the system.
        Used during the first startup, to pre-create the admin user.

        Returns
        -------
        Boolean,
            True if the default admin exists, False otherwise.
        '''

        count = db_session().query(Admin).filter(Admin.username == 'admin').count()

        return count != 0

    def fetch_all_users(self):
        '''
        Fetch a list of users in the system.

        Returns
        -------
        list
            List of User/Admin objects.
        '''

        return db_session.query(User).all()

    def fetch_user_by_id(self, id):
        '''
        Fetch a user by id.

        Parameters
        ----------
        id: int,
            ID of the user.

        Returns
        -------
        Admin/User
            Matching Admin/User object, None if no match found.
        '''
        return db_session().query(User).filter(User.id == id).first()

    def login(self, username, password):
        '''
        Authenticates a user.

        Parameters
        ----------
        username: str,
            Username of the user.
        password: str,
            Password of the user.

        Returns
        -------
        Admin/User
            Authenticated Admin/User object, None if no match found.
        '''
        return db_session.query(User).filter(and_(User.username == username, User.password == password)).first()

    def _get_next_user_id(self):
        '''
        Private method used for calculating the next primary key/ID for the user record.
        This is done manually since SQL alchemy does not allow autoincrement of primary keys for polymorphic types.
        '''
        count = db_session.query(User).filter(User.id != None).count()
        return count+1


blog_service = BlogService()
user_service = UserService()
