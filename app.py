import os

from flask import Flask, abort, redirect, render_template, request, session
from flask.helpers import url_for
from flask.json import jsonify
from flask_bootstrap import Bootstrap
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import db_session, init_db
from models import Admin, User
from services import blog_service, user_service
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
Bootstrap(app)

logging.basicConfig(level=logging.DEBUG)

host_url = "http://localhost:5000"
if os.environ.get("CODESPACES") == "true":
    host_url = "https://{}-5000.apps.codespaces.githubusercontent.com".format(
        os.environ.get("CLOUDENV_ENVIRONMENT_ID"))


class UserMeta:
    '''
    Class that holds minimal user identifiable info in the session context
    '''

    def __init__(self, id, display_name, type):
        self.id = id
        self.display_name = display_name
        self.type = type


def setup_admin(user_service):
    '''
    Create admin user when the app is launched for the first time
    '''

    if not user_service.is_default_admin_exists():
        user_service.sign_up('admin', 'password', 'Admin',
                             None, 'admin@blog.com', True)
        app.logger.info("Admin Added: ",
                        user_service.is_default_admin_exists())


@app.route('/')
@app.route('/index/')
def index():
    '''
    Route for home page that also renders list of blog posts
    Administrators can also see unpublished posts
    '''

    is_admin = False

    if is_loggedin():
        user = get_current_user()
        is_admin = user is not None and user.type == 'admin'

    include_hidden = is_admin
    posts = blog_service.fetch_all_posts(include_hidden)
    return render_template('index.html', posts=posts)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    '''
    Route for login page and for submitting login form
    '''

    if not is_loggedin():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = user_service.login(username, password)
            if user is not None:
                user_meta = UserMeta(user.id, user.display_name, user.type)
                session['user'] = user_meta.__dict__
            else:
                return render_template('login.html', error_message='Invalid credentials.')
        elif request.method == 'GET':
            return render_template('login.html')
    return redirect(host_url + "/index/", code=303)


@app.route('/logout/')
def logout():
    '''
    Logout end point
    '''

    if is_loggedin():
        session.pop('user')
    return redirect(host_url + "/index/", code=303)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    '''
    Route for registration page and for submitting registration form
    '''

    if not is_loggedin():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            display_name = request.form['display_name']
            email = request.form['email']
            try:
                user = user_service.sign_up(
                    username, password, display_name, None, email)
                user_meta = UserMeta(user.id, user.display_name, user.type)
                session['user'] = user_meta.__dict__
            except:
                return render_template('register.html', error_message='Registration failed. Please check your input and try again. It is also possible that there is an account with the given username or emailid.')
        elif request.method == 'GET':
            return render_template('register.html')
    return redirect(host_url + "/index/", code=303)


@app.route('/posts/', methods=['GET', 'POST'])
@app.route('/posts/<int:id>', methods=['GET', 'POST'])
def add_view_post(id=None):
    '''
    Route for "add post" page and for submitting "add post" form for admins
    Also for viewing a blog post by id - for all users
    Administrators can view unpublished posts
    '''

    is_admin = False

    if is_loggedin():
        user = get_current_user()
        is_admin = user is not None and user.type == 'admin'

    if request.method == 'POST':
        if not is_loggedin():
            return redirect(host_url + '/login/', code=303)
        if not is_admin:
            return redirect(host_url + '/index/', code=303)

        title = request.form['title']
        content = request.form['content']
        visibility = False
        if 'is_visible' in request.form:
            is_visible = request.form['is_visible']
            visibility = True if is_visible == 'on' else False
        post = blog_service.add_post(
            title, content, user, make_visible=visibility)
        message = "Posted Successfully. <a href=\"/posts/{}\" class=\"alert-link\">View Post.</a>".format(
            post.id)
        return render_template('editpost.html', post=post, success_message=message)
    elif request.method == 'GET':
        if id is not None:
            post = blog_service.fetch_post_by_id(id)
            if post is None or (not post.is_visible and not is_admin):
                abort(404, description="Post not found")
            message = None if post.is_visible else "This post is only visible to admins."
            return render_template('viewpost.html', post=post, warning_message=message)
        if is_admin:
            return render_template('addpost.html')
        elif not is_loggedin():
            return redirect(host_url + '/login/', code=303)
        else:
            abort(403, description="Post not found")


@app.route('/editpost/<int:id>/', methods=['GET', 'POST'])
def edit_post(id):
    '''
    Route for "edit post" page and for submitting "edit post" form, for admins
    '''

    is_admin = False

    if is_loggedin():
        user = get_current_user()
        is_admin = user is not None and user.type == 'admin'
    else:
        return redirect(host_url + '/login/', code=303)

    if not is_admin:
        abort(403, "Only admin can edit posts")

    if request.method == 'GET':
        if id is not None:
            post = blog_service.fetch_post_by_id(id)
            if post is None:
                abort(404, description="Post not found")
            return render_template('editpost.html', post=post)
        else:
            abort(404, description="Post not found")

    if request.method == 'POST':
        if id is not None:
            title = request.form['title']
            content = request.form['content']
            visibility = False
            if 'is_visible' in request.form:
                is_visible = request.form['is_visible']
                visibility = True if is_visible == 'on' else False
            post = blog_service.edit_post(
                id, title, content, make_visible=visibility)
            if post is None:
                abort(404, description="Post not found")

            message = "Post Updated Successfully.<a href=\"/posts/{}\" class=\"alert-link\">View Post.</a>".format(
                post.id)
            return render_template('editpost.html', post=post, success_message=message)
        else:
            abort(404, description="Post not found")


@app.route('/posts/<int:post_id>/comments/', methods=['POST'])
def add_post_comment(post_id):
    '''
    Route for adding comments to the blog posts - for registered users
    '''

    if request.method == 'POST':
        if is_loggedin():
            user = get_current_user()

            content = request.form['comment']
            post = blog_service.add_comment(post_id, content, user)
            if post is None:
                abort(404, description="Post not found")
            return redirect(host_url + '/posts/'+str(post.id), code=303)
        else:
            return redirect(host_url + '/login/', code=303)


@app.route('/deletepost/<int:id>/', methods=['GET'])
def delete_post_comment(id):
    '''
    Route for deleting a blog post - for admins
    '''

    if request.method == 'GET':
        is_admin = False

        if is_loggedin():
            user = get_current_user()
            is_admin = user is not None and user.type == 'admin'
            if is_admin:
                blog_service.delete_post(id)
                return redirect(host_url + '/', code=303)
            else:
                abort(403, 'Only admin can delete posts')
        else:
            return redirect(host_url + '/login/', code=303)


@app.teardown_appcontext
def shutdown_session(exception=None):
    '''
    Handler for disposing database sessions after each request lifecycle
    '''

    db_session.remove()


def get_current_user():
    '''
    Get the currently logged in user
    '''

    if is_loggedin():
        try:
            return user_service.fetch_user_by_id(session['user']['id'])
        except:
            session.pop('user')
            return None
    return None


def is_loggedin():
    '''
    Check if the request is made by a logged in user
    '''

    return 'user' in session


if __name__ == '__main__':
    init_db()

    setup_admin(user_service)

    app.run()
