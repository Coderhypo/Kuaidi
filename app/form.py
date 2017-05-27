from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo


class SearchForm(FlaskForm):
    express_code = SelectField("express", choices=[], coerce=str)
    package_number = StringField("number", validators=[DataRequired("单号不能为空")])


class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired("用户名不能为空")])
    password = PasswordField("密码", validators=[DataRequired("登录密码不能为空")])
    remember = BooleanField("记住登录状态", default=False)


class RegisterForm(FlaskForm):
    username = StringField("登录用户名", validators=[DataRequired("用户名作为登录用, 不能为空")])
    email = StringField("邮箱", validators=[DataRequired("邮箱不能为空")])
    password = PasswordField("密码", validators=[DataRequired("密码不能为空"), Length(min=6, message="密码不能少于 6 位")])
    re_password = PasswordField("再次输入密码", validators=[EqualTo("password", message="两次密码输入不一致")])
    internal_code = StringField("内测码", validators=[DataRequired("内测码不能为空")])


class WatchForm(FlaskForm):
    watch_package_id = HiddenField()
    watch_nicename = StringField("昵称", validators=[DataRequired("昵称不能为空")])


class UnWatchForm(FlaskForm):
    unwatch_package_id = HiddenField()


class DelPackageForm(FlaskForm):
    delete_package_id = HiddenField()

