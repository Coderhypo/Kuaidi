from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_user, logout_user, login_required, current_user

from app.form import SearchForm, LoginForm, RegisterForm, WatchForm, UnWatchForm, DelPackageForm
from app.model import Express, Package, User

from config import INTERNAL_CODE

route = Blueprint("view", __name__)


@route.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()
    form.express_code.choices = [(e.code, e.name) for e in Express.query.all()]

    if form.validate_on_submit():
        if current_user and current_user.is_authenticated:
            pkg = Package.get_package(current_user.user_id, form.express_code.data, form.package_number.data)
        else:
            pkg = None
            form.errors['package_number'] = ['查询前请先登录!']

        if pkg:
            return redirect(url_for("view.package_info", package_id=pkg.package_id))
        else:
            if not form.errors:
                form.errors['package_number'] = ['未找到相关信息, 请核实单号和物流公司']

    return render_template("index.html", form=form)


@route.route("/package/<package_id>", methods=['GET', 'POST'])
@login_required
def package_info(package_id):
    pkg = Package.get_package_by_id(package_id)
    if not pkg:
        return redirect(url_for("view.index"))
    if pkg.user_id != current_user.user_id:
        return redirect(url_for("view.user_package"))
    express = Express.query.filter_by(express_id=pkg.express_id).first()

    watch_form = WatchForm()
    unwatch_form = UnWatchForm()

    if watch_form.validate_on_submit() and pkg.package_id == watch_form.watch_package_id.data:
        pkg.watching(watch_form.watch_nicename.data)
        return redirect(url_for("view.package_info", package_id=pkg.package_id))

    if unwatch_form.validate_on_submit() and pkg.package_id == unwatch_form.unwatch_package_id.data:
        pkg.unwatching()
        return redirect(url_for("view.package_info", package_id=pkg.package_id))

    return render_template("package.html", package=pkg, express=express, watch_form=watch_form,
                           unwatch_form=unwatch_form)


@route.route("/user/package", methods=['GET', 'POST'])
@login_required
def user_package():
    packages = Package.query.filter_by(user_id=current_user.user_id).all()
    delete_form = DelPackageForm()
    if delete_form.validate_on_submit():
        pkg = Package.query.filter_by(package_id=delete_form.delete_package_id.data).first()
        if pkg and pkg.user_id == current_user.user_id:
            pkg.delete()
        return redirect(url_for("view.user_package"))

    return render_template("user/packages.html", packages=packages, delete_form=delete_form)


@route.route("/user/watching", methods=['GET', 'POST'])
@login_required
def user_watching():
    packages = Package.get_watching_package_by_user_id(current_user.user_id)
    unwatch_form = UnWatchForm()
    if unwatch_form.validate_on_submit():
        pkg = Package.query.filter_by(package_id=unwatch_form.unwatch_package_id.data).first()
        if pkg and pkg.user_id == current_user.user_id:
            pkg.unwatching()
        return redirect(url_for("view.user_watching"))
    return render_template("user/watching.html", packages=packages, unwatch_form=unwatch_form)


@route.route("/user/open-api")
@login_required
def user_token():
    token = current_user.get_token()
    return render_template("user/token.html", token=token)


@route.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for("view.user_package"))
        form.errors['username'] = ['用户名或密码错误']
    return render_template("login.html", form=form)


@route.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("view.index"))


@route.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.internal_code.data != INTERNAL_CODE:
            form.errors['internal_code'] = ["内测码错误, 请联系作者。"]
        if not form.errors:
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                form.errors['username'] = ['用户名 {} 已被占用'.format(form.username.data)]
            else:
                user = User.query.filter_by(email=form.email.data).first()
                if user:
                    form.errors['email'] = ['邮箱 {} 已被占用'.format(form.email.data)]
        if not form.errors:
            user = User(form.username.data, form.email.data, form.password.data)
            if user:
                return redirect(url_for("view.login"))
    return render_template("register.html", form=form)


@route.route("/about")
def about():
    return render_template("about.html")

