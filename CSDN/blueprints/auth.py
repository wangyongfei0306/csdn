from flask import Blueprint, render_template, flash, url_for, redirect
from flask_login import login_user, logout_user, current_user, login_required
from CSDN.forms.auth import LoginForm, RegisterForm, ForgetPasswordForm, ResetPasswordForm
from CSDN.helper import generate_token, send_reset_password_email, validate_token
from CSDN.models import User, db
from CSDN.secret import Operations

auth_bp = Blueprint('auth',__name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        with db.auto_commit():
            user = User()
            user.set_attrs(form.data)
            db.session.add(user)
        flash('你已经成功注册，请登录吧！', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/login.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.validate_password(form.password.data):
            if not user.active:
                flash('你的账号已经被封.', 'warning')
                return redirect(url_for('main.index'))
            if login_user(user):
                flash('你已经成功登录', 'success')
                return redirect(url_for('main.index'))
            else:
                pass
        flash('你的账号或密码错误', 'warning')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已经成功登出', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forget/password', methods=['GET', 'POST'])
def forget_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first_or_404()
        if user:
            token = generate_token(user=user, operation=Operations.RESET_PASSWORD)
            send_reset_password_email(user=user, token=token)
            flash('重置密码邮件已发送，请检查.', 'success')
            return redirect(url_for('auth.login'))
        flash('邮件错误！', 'warning')
        return redirect(url_for('auth.forget_password'))
    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/reset/password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first_or_404()
        if user is None:
            return redirect(url_for('main.index'))
        if validate_token(user=user, token=token, operation=Operations.RESET_PASSWORD,
                          new_password=form.password.data):
            flash('密码修改成功，请登录.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('无效或过期的链接.', 'danger')
            return redirect(url_for('auth.forget_password'))
    return render_template('auth/reset_password.html', form=form)