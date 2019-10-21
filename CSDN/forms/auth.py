from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo
from CSDN.models import User


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 30)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 254)])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField()

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('注册的名字已经被使用')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('注册的Email已经被使用')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 254)])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 128)])
    submit = SubmitField()


class ForgetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField()

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('邮箱账号错误')


class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField('新密码', validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('确认', validators=[DataRequired()])
    submit = SubmitField()