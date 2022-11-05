from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CreateComment, ContactForm
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import abort
from sqlalchemy.orm import declarative_base, relationship
import smtplib
from email.message import EmailMessage
import ssl
import os

# Variables
MY_EMAIL = os.getenv("MY_EMAIL")
MY_PASS = os.getenv("MY_PASS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

Base = declarative_base()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
app.config['CKEDITOR_PKG_TYPE'] = 'basic'
ckeditor = CKEditor(app)

Bootstrap(app)

#DATABASE_URL = os.getenv("DATABASE_URL")
#if DATABASE_URL is None:
#    DATABASE_URL = 'sqlite:///posts.db'

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", 'sqlite:///posts.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# LOG IN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


# DATABASE TABLES

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # ***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


with app.app_context():
    db.create_all()


# ----- HELPER FUNCTIONS ----- #


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def send_email(name, email, phone_num, message):
    em = EmailMessage()
    em["From"] = MY_EMAIL
    em["Subject"] = "Someone Sent you a message from your Website!"
    em.set_content(f"Name: {name}\nEmail: {email}\nPhone Number: {phone_num}\n\nMessage:\n{message}")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as connection:
        connection.login(MY_EMAIL, MY_PASS)
        connection.sendmail(MY_EMAIL,
                            EMAIL_RECEIVER,
                            em.as_string()
                            )


def get_all_data():
    data = db.session.query(BlogPost).all()
    return data


def add_blog(title, subtitle, img_url, body):
    new_blog = BlogPost(
        title=title,
        subtitle=subtitle,
        date=date.today(),
        author=current_user,
        img_url=img_url,
        body=body
    )

    try:
        db.session.add(new_blog)
        db.session.commit()
        print(current_user.posts)
    except:
        return False
    return True


def edit_blog(post_id, title, subtitle, img_url, body):
    blog = db.session.query(BlogPost).filter_by(id=post_id).first()
    blog.title = title
    blog.subtitle = subtitle
    blog.img_url = img_url
    blog.body = body
    try:
        db.session.commit()
    except:
        return False
    else:
        return True


def delete_by_id(id):
    blog = db.session.query(BlogPost).filter_by(id=id).first()

    try:
        db.session.delete(blog)
        db.session.commit()
    except:
        return False
    else:
        return True


def used_email(email):
    if db.session.query(User).filter_by(email=email).first():
        return True
    return False


def add_account(email, password, name):
    new_user = User(
        email=email,  # type: ignore
        password=password,  # type: ignore
        name=name  # type: ignore
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except:
        return False
    return True


def add_comment(body, blog):
    print("CURRENT USER: ", current_user)
    print("BLOG: ", blog)
    comment = Comment(
        text=body,
        comment_author=current_user,
        parent_post=blog
    )
    db.session.add(comment)
    db.session.commit()


def del_comment(comment_id):
    comment = db.session.query(Comment).filter_by(id=comment_id).first()
    db.session.delete(comment)
    db.session.commit()


# ----- WRAPPER FUNCTIONS -----#

def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return function(*args, **kwargs)

    return wrapper_function


# ----- ROUTES ----- #

@app.route('/')
def home():
    posts = get_all_data()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    added = None
    blog = db.session.query(BlogPost).filter_by(id=post_id).first()
    if blog.id != current_user.id:
        if current_user.id != 1:
            flash("You do not have permission to edit this post.")
            return redirect("/login")
    edit_form = CreatePostForm(
        title=blog.title,
        subtitle=blog.subtitle,
        author=blog.author,
        img_url=blog.img_url,
        body=blog.body
    )
    if request.method == "POST":
        title = edit_form.title.data
        subtitle = edit_form.subtitle.data
        img_url = edit_form.img_url.data
        body = edit_form.body.data

        if edit_blog(post_id, title, subtitle, img_url, body):
            flash("Successfully Edited")
            return redirect(f"/post/{post_id}")
        flash("Blog Edit Failed")
        return render_template("make-post.html", form=edit_form, current_user_id=current_user.id)

    return render_template("make-post.html", form=edit_form, current_user_id=current_user.id)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    blog = db.session.query(BlogPost).filter_by(id=post_id).first()
    comment = CreateComment()
    comments = []
    for cmt in blog.comments:
        comments.append(cmt.text)

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("You have to be signed in to post a comment.")
            return redirect("/login")
        body = comment.comment.data
        add_comment(body, blog)
        return redirect(url_for("show_post", post_id=post_id))

    return render_template("post.html", current_user=current_user, post=blog, form=comment, comments=blog.comments,
                           del_comment=del_comment)


@app.route("/new-post", methods=['GET', 'POST'])
def new_post():
    if not current_user.is_authenticated:
        flash("You need to be logged in to create a new post.")
        return redirect("/login")

    form = CreatePostForm()
    added = None
    if request.method == "POST":
        title = form.title.data
        subtitle = form.subtitle.data
        img_url = form.img_url.data
        body = form.body.data

        if add_blog(title, subtitle, img_url, body):
            added = "Successfully Added"
            return render_template("make-post.html", form=form, added=added)
        added = "Blog upload Failed"
        return render_template("make-post.html", form=form, added=added)

    return render_template("make-post.html", form=form, added=added)


@app.route("/delete/<int:post_id>/<int:post_author_id>")
@login_required
def delete(post_id, post_author_id):
    if current_user.id != 1 and current_user.id != post_author_id:
        return "You do not have permission to delete this post."
    delete_by_id(post_id)
    return redirect("/")


@app.route("/delete_comment/<int:comment_id>/<int:post_id>")
@login_required
def delete_comment(comment_id, post_id):
    del_comment(comment_id)
    return redirect(url_for("show_post", post_id=post_id))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    contact_form = ContactForm()

    if contact_form.validate_on_submit():
        name = contact_form.name.data
        email = contact_form.email.data
        phone_num = contact_form.phone_num.data
        message = contact_form.message.data
        send_email(name, email, phone_num, message)

    return render_template("contact.html", form=contact_form)


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterForm()

    if register_form.validate_on_submit():
        print("SUBMITTING")
        email = register_form.email.data
        if used_email(email):
            flash("Sorry, That Email is Already Used. Try Logging In.")
            return redirect(url_for("login"))
        name = register_form.name.data
        password = register_form.password.data
        hashed_pass = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)
        if add_account(email, hashed_pass, name):
            user = db.session.query(User).filter_by(email=email).first()
            login_user(user)
            return redirect("/", code=302)

        flash("Registration Failed")
        return redirect(url_for("register"))

    return render_template("register.html", form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        user = db.session.query(User).filter_by(email=email).first()

        password = login_form.password.data
        if user is not None:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect("/", code=301)
        flash("Wrong Email or Password!")
        return render_template("login.html", form=login_form)
    return render_template("login.html", form=login_form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/", code=301)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
