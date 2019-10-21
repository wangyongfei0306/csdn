from flask_ckeditor import CKEditorField
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, Optional, EqualTo, ValidationError

from CSDN.models import User, Category


class CommentForm(FlaskForm):
    body = TextAreaField('Body', validators=[DataRequired(), Length(1, 254)])
    submit = SubmitField()


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    username = StringField('Username', validators=[DataRequired(), Length(1, 20),
                                                   Regexp('^[a-zA-Z0-9]*$',
                                                          message='The username should contain only a-z, A-Z and 0-9.')])
    website = StringField('Website', validators=[Optional(), Length(0, 255)])
    location = StringField('City', validators=[Optional(), Length(0, 50)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(0, 120)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('名字已经被使用.', 'warning')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(8, 128),
                                                    EqualTo('confirm_password', message='两次新密码有错误')])
    confirm_password = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField()


class ChangeEmailForm(FlaskForm):
    email = StringField('新邮箱', validators=[DataRequired(), Email(), Length(1, 254)])
    submit = SubmitField()

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经被注册过.')


class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(message='必填项.'), Length(1, 30)])
    category = SelectField('分类', coerce=int, default=1)
    body = CKEditorField('内容', validators=[DataRequired(message='必填项.')])
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.order_by(Category.name).all()]


class NotificationSettingForm(FlaskForm):
    receive_comment_notification = BooleanField('新的评论')
    receive_collect_notification = BooleanField('新的收藏')
    receive_follow_notification = BooleanField('新的关注')
    submit = SubmitField()


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField('我的收藏公开.')
    submit = SubmitField()


class DeleteAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField()

    def validate_email(self, field):
        if current_user.username != field.data:
            raise ValidationError('用户名错误.')