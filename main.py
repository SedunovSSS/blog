from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib, datetime
from config import admins

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
UPLOAD_FOLDER = './static/uploads'
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    path = db.Column(db.String(150), nullable=False)
    dateR = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __repr__(self):
        return '<Users %r>' % self.id


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    intro = db.Column(db.String(150), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    path = db.Column(db.String(150), nullable=False)
    dateR = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __repr__(self):
        return '<Posts %r>' % self.id


class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    author = db.Column(db.String(150), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    dateR = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __repr__(self):
        return '<Comments %r>' % self.id


@app.route('/')
def main():
    name = request.cookies.get('user')
    post = Posts.query.all()
    if len(post) > 2:
        post = list(reversed(post))
    else:
        post = list(post)
    if name is None:
        name = "Guest"
    try:
        path = db.session.query(Users.path).filter_by(login=name).first()[0]
        return render_template("index.html", name=name, path=path, post=post)
    except:
        return render_template("index.html", name=name, post=post)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        login = request.form['login']
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']
        file = request.files['icon[]']
        path = ""

        if passw1 == passw2:
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            exists = db.session.query(Users.id).filter_by(login=login).first() is not None or db.session.query(Users.id).filter_by(email=email).first() is not None
            if not exists:
                if file:
                    path = f"static/uploads/{login}"
                    if not os.path.exists(path):
                        os.makedirs(path)
                    if not os.path.exists(path + "/icon.png"):
                        file.save(f"static/uploads/{login}/icon.png")
                user = Users(login=login, email=email, password=password, path=str(path+"/icon.png"))
            else:
                return redirect("/register")
            try:
                db.session.add(user)
                db.session.commit()
                resp = make_response(redirect("/"))
                resp.set_cookie('user', user.login)
                return resp
            except Exception as ex:
                print(ex)
                return redirect("/register")
    else:
        name = request.cookies.get('user')
        if name is None:
            name = "Guest"
        try:
            path = db.session.query(Users.path).filter_by(login=name).first()[0]
            return render_template("register.html", name=name, path=path)
        except:
            return render_template("register.html", name=name)


@app.route('/login', methods=['POST', "GET"])
def login():
    if request.method == "POST":
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']
        if passw1 == passw2:
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            exists = db.session.query(Users.id).filter_by(email=email, password=password).first() is not None
            user = db.session.query(Users.login).filter_by(email=email, password=password).first()
            if exists:
                resp = make_response(redirect("/"))
                resp.set_cookie('user', user[0])
                return resp
            else:
                return redirect("/login")

        else:
            name = request.cookies.get('user')
            if name is None:
                name = "Guest"
            try:
                path = db.session.query(Users.path).filter_by(login=name).first()[0]
                return render_template("login.html", name=name, path=path)
            except:
                return render_template("login.html", name=name)
    else:
        name = request.cookies.get('user')
        if name is None:
            name = "Guest"
        try:
            path = db.session.query(Users.path).filter_by(login=name).first()[0]
            return render_template("login.html", name=name, path=path)
        except:
            return render_template("login.html", name=name)


@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if request.method == "POST":
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']
        file = request.files['icon[]']
        login = request.args.get('user')
        path = ""
        if file:
            path = f"static/uploads/{login}"
            file.save(f"static/uploads/{login}/icon.png")
        if passw1 == passw2:
            name = request.cookies.get('user')
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            if name is not None:
                user = Users.query.filter_by(login=name).first()
                try:
                    path = f"static/uploads/{login}/icon.png"
                    user.email = email
                    user.password = password
                    user.path = path
                    db.session.commit()
                    return redirect("/")
                except:
                    return redirect("/profile")
            else:
                return redirect("/login")
    else:
        name = request.cookies.get('user')
        user = request.args.get('user')
        if user is not None and name is not None and name == user:
            email = db.session.query(Users.email).filter_by(login=user).first()[0]
            path = db.session.query(Users.path).filter_by(login=name).first()[0]
            return render_template("profile.html", name=name, path=path, login=name, email=email)
        else:
            return 'None'


@app.route('/admin')
def admin():
    name = request.cookies.get('user')
    if name in admins:
        users = Users.query.all()
        try:
            path = db.session.query(Users.path).filter_by(login=name).first()[0]
            return render_template("admin.html", name=name, path=path, users=users, length=len(users))
        except:
            return redirect("/")
    else:
        return redirect("/")


@app.route('/admin/changeuser', methods=['GET', 'POST'])
def admin_change_user():
    if request.method == "POST":
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']
        file = request.files['icon[]']
        login = request.args.get('user')
        path = ""
        if file:
            path = f"static/uploads/{login}"
            file.save(f"static/uploads/{login}/icon.png")
        if passw1 == passw2:
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            if login is not None:
                user = Users.query.filter_by(login=login).first()
                try:
                    path = f"static/uploads/{login}/icon.png"
                    user.email = email
                    user.password = password
                    if file:
                        user.path = path
                    db.session.commit()
                    return redirect("/admin")
                except Exception as ex:
                    print(ex)
                    return redirect("/admin")
            else:
                return redirect("/admin")
    else:
        name = request.cookies.get('user')
        user_login = request.args.get('user')
        if name in admins:
            user = Users.query.filter_by(login=user_login).first()
            path = db.session.query(Users.path).filter_by(login=name).first()[0]
            return render_template("changeuser.html", user=user, name=name, path=path)
        else:
            return redirect("/")


@app.route("/admin/deluser", methods=['GET'])
def admin_del_user():
    name = request.cookies.get('user')
    if name in admins:
        login = request.args.get('user')
        path = db.session.query(Users.path).filter_by(login=login).first()[0]
        os.remove(path)
        Users.query.filter_by(login=login).delete()
        db.session.commit()
        return redirect("/admin")
    else:
        return redirect("/")


@app.route("/addpost", methods=['GET', 'POST'])
def addpost():
    if request.method == "POST":
        author = request.cookies.get('user')
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']
        image = request.files['image[]']
        path = f"static/uploads/{author}/{image.filename}"
        while os.path.exists(path):
            image.filename = "exists123" + image.filename
            path = f"static/uploads/{author}/{image.filename}"
        path = f"static/uploads/{author}/{image.filename}"
        image.save(path)
        post = Posts(title=title, intro=intro, text=text, path=path, author=author)
        try:
            db.session.add(post)
            db.session.commit()
            return redirect("/")
        except Exception as ex:
            print(ex)
            return redirect("/addpost")

    else:
        name = request.cookies.get('user')
        if name is not None:
            try:
                path = db.session.query(Users.path).filter_by(login=name).first()[0]
                return render_template("addpost.html", name=name, path=path)
            except:
                return render_template("addpost.html", name=name)
        else:
            return redirect("/login")


@app.route("/viewall", methods=['GET', "POST"])
def viewall():
    if request.method == "POST":
        post_id = request.args.get("id")
        author = request.cookies.get("user")
        text = request.form['comment']
        if author is not None:
            if post_id is not None and text is not None:
                comment = Comments(post_id=post_id, author=author, text=text)
                try:
                    db.session.add(comment)
                    db.session.commit()
                    return redirect(f"/viewall?id={post_id}")
                except:
                    return redirect(f"/viewall?id={post_id}")
            else:
                return redirect(f"/viewall?id={post_id}")
        else:
            return redirect("/login")

    else:
        id = request.args.get("id")
        name = request.cookies.get("user")
        path = db.session.query(Users.path).filter_by(login=name).first()[0]
        if id is not None and path is not None:
            post = Posts.query.filter_by(id=id).first()
            comments = Comments.query.filter_by(post_id=id).all()
            if len(comments) > 2:
                comments = list(reversed(comments))
            else:
                comments = list(comments)
            print(comments)
            return render_template("viewall.html", post=post, name=name, path=path, comments=comments)
        else:
            return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)
