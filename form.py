from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length


class RegisterForm(FlaskForm):
    username = StringField('username', validators=[
        (DataRequired(message='用户名不可以为空')),
        Length(3, 15, message='用户名长度在3-15个单位')
    ], render_kw={'placeholder': '请输入用户名'})
    password = PasswordField('password', validators=[
        (DataRequired(message='密码不可以为空')),
        Length(6, 15, message='密码长度在3-15个单位')
    ], render_kw={'placeholder': '请输入密码'})


class LoginForm(FlaskForm):
    username = StringField('username', validators=[
        (DataRequired(message='用户名不可以为空')),
        Length(3, 15, message='用户名长度在3-15个单位')
    ], render_kw={'placeholder': '请输入用户名'})
    password = PasswordField('password', validators=[
        (DataRequired(message='密码不可以为空')),
        Length(6, 15, message='密码长度在3-15个单位')
    ], render_kw={'placeholder': '请输入密码'})
