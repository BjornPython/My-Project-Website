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