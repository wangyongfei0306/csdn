from flask import Blueprint, flash, url_for, redirect, abort, render_template, request, current_app
from flask_login import login_required, current_user, logout_user
from CSDN.decorators import permission_required
from CSDN.forms.user import CommentForm, EditProfileForm, ChangePasswordForm, ChangeEmailForm, PostForm, \
    NotificationSettingForm, PrivacySettingForm, DeleteAccountForm
from CSDN.helper import redirect_back, push_follow_notification, push_collect_notification, push_comment_notification, \
    generate_token, send_reset_email_email, validate_token
from CSDN.models import Post, Comment, db, User, Collect, Follow, Category, Notification
from CSDN.secret import Operations


user_bp = Blueprint('user', __name__)


@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user and user.locked:
        flash('你的账号已经被锁定.', 'danger')
    if user == current_user and not user.active:
        logout_user()

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_PER_PAGE']
    pagination = Post.query.with_parent(user).order_by(Post.timestamp.desc()).paginate(page, per_page)
    posts = pagination.items
    return render_template('user/index.html', pagination=pagination, posts=posts, user=user)


@user_bp.route('/show/collections/<username>')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_COLLECTOR_PER_PAGE']
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)


@user_bp.route('/show/collectors/<int:post_id>')
def show_collectors(post_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_COLLECTOR_PER_PAGE']
    pagination = Collect.query.with_parent(post).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors.html', post=post, pagination=pagination, collects=collects)


@user_bp.route('/collect/<int:post_id>', methods=['POST'])
@login_required
@permission_required('COLLECT')
def collect(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.is_collecting(post):
        flash('你已经收藏过了', 'info')
        return redirect(url_for('main.show_post', post_id=post_id))

    current_user.collect(post)
    flash('文章已成功收藏.', 'success')
    if current_user != post.user:
        push_collect_notification(collector=current_user, post_id=post.id, receiver=post.user)
    return redirect(url_for('main.show_post', post_id=post_id))


@user_bp.route('/uncollect/<int:post_id>', methods=['POST'])
@login_required
def uncollect(post_id):
    post = Post.query.get_or_404(post_id)
    if not current_user.is_collecting(post):
        flash('文章没有被收藏.', 'info')
        return redirect(url_for('main.show_post', post_id=post_id))

    current_user.uncollect(post)
    flash('文章已被取消收藏', 'info')
    return redirect(url_for('main.show_post', post_id=post_id))


@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        flash('已经关注过.', 'info')
        return redirect(url_for('user.index', username=username))

    current_user.follow(user)
    flash('恭喜，关注成功.', 'success')
    push_follow_notification(current_user, user)
    return redirect_back()


@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        flash('没有关注的人.', 'info')
        return redirect(url_for('user.index', username=username))
    current_user.unfollow(user)
    flash('成功取消关注.', 'info')
    return redirect_back()


@user_bp.route('/show_following/<username>')
def show_following(username):
    user = User.query.filter_by(username=username).first()
    follows = user.following.order_by(Follow.timestamp.desc()).all()
    return render_template('user/following.html', user=user, follows=follows)


@user_bp.route('/show_followers/<username>')
def show_followers(username):
    user = User.query.filter_by(username=username).first()
    follows = user.followers.order_by(Follow.timestamp.desc()).all()
    return render_template('user/followers.html', user=user, follows=follows)


@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        with db.auto_commit():
            current_user.set_attrs(form.data)
        flash('成功修改资料', 'success')
        return redirect(url_for('main.index', username=current_user.username))
    form.name.data = current_user.name
    form.username.data = current_user.username
    form.website.data = current_user.website
    form.location.data = current_user.location
    form.bio.data = current_user.bio
    return render_template('user/settings/edit_profile.html', form=form)


@user_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.validate_password(form.old_password.data):
            with db.auto_commit():
                current_user.password = form.new_password.data
            flash('密码修改成功，请重新登录.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('原始密码错误.', 'warning')
    return render_template('user/settings/change_password.html', form=form)


@user_bp.route('/change_email_request', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = generate_token(user=current_user, operation=Operations.CHANGE_EMAIL,
                               new_email=form.email.data.lower())
        send_reset_email_email(user=current_user, token=token, to=form.email.data.lower())
        flash('更改邮件已发送，请检查.', 'success')
        return redirect(url_for('user.index', username=current_user.username))
    return render_template('user/settings/change_email.html', form=form)


@user_bp.route('/change_email/<token>')
@login_required
def change_email(token):
    if validate_token(user=current_user, token=token, operation=Operations.CHANGE_EMAIL):
        flash('邮箱已经更新.', 'success')
        return redirect(url_for('user.index', username=current_user.username))
    else:
        flash('过期或者无效的token.', 'warning')
        return redirect(url_for('user.change_email_request'))


@user_bp.route('/show_notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)
    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@user_bp.route('/notification/read/<notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)
    notification.is_read = True
    db.session.commit()
    flash('提示信息操作成功.', 'success')
    return redirect(url_for('user.show_notifications'))


@user_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('所有提示信息均已读.', 'success')
    return redirect(url_for('user.show_notifications'))


@user_bp.route('/notification_setting', methods=['GET', 'POST'])
@login_required
def notification_setting():
    form = NotificationSettingForm()
    if form.validate_on_submit():
        with db.auto_commit():
            current_user.set_attrs(form.data)
        flash('提示消息更新成功.', 'success')
        return redirect(url_for('user.index', username=current_user.username))
    form.receive_comment_notification.data = current_user.receive_comment_notification
    form.receive_follow_notification.data = current_user.receive_follow_notification
    form.receive_collect_notification.data = current_user.receive_collect_notification
    return render_template('user/settings/edit_notification.html', form=form)


@user_bp.route('/privacy_setting', methods=['GET', 'POST'])
@login_required
def privacy_setting():
    form = PrivacySettingForm()
    if form.validate_on_submit():
        with db.auto_commit():
            current_user.set_attrs(form.data)
        flash('设置成功.', 'success')
        return redirect(url_for('user.index', username=current_user.username))
    form.public_collections.data = current_user.public_collections
    return render_template('user/settings/edit_privacy.html', form=form)


@user_bp.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        db.session.delete(current_user._get_current_object())
        db.session.commit()
        flash('你自由了，再见！', 'success')
        return redirect(url_for('main.index'))
    return render_template('user/settings/delete_account.html', form=form)


@user_bp.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    if form.validate_on_submit():
        with db.auto_commit():
            post.title = form.title.data
            post.body = form.body.data
            post.category = Category.query.get(form.category.data)
        flash('文章更新完毕', 'success')
        return redirect(url_for('main.show_post', post_id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    form.category.data = post.category_id
    return render_template('main/edit_post.html', form=form)


@user_bp.route('/report/post/<int:post_id>', methods=['POST'])
@login_required
def report_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.flag += 1
    db.session.commit()
    flash('文章举报成功.', 'success')
    return redirect(url_for('main.show_post', post_id=post_id))


@user_bp.route('/delete/post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.user and not current_user.can('ADMIN'):
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除', 'success')
    post_n = Post.query.with_parent(post.user).filter(Post.id > post_id).order_by(Post.id.asc()).first()
    if post_n is None:
        post_p = Post.query.with_parent(post.user).filter(Post.id < post_id).order_by(Post.id.desc()).first()
        if post_p is None:
            return redirect(url_for('user.index', username=current_user.username))
        return redirect(url_for('main.show_post', post_id=post_p.id))
    return redirect(url_for('main.show_post', post_id=post_n.id))


@user_bp.route('/set/comment/<int:post_id>', methods=['POST'])
@login_required
def set_comment(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.user and current_user.can('ADMIN'):
        abort(404)
    if post.can_comment:
        post.can_comment = False
        db.session.commit()
        flash('您设置此文章为不能评论', 'info')
    else:
        post.can_comment = True
        db.session.commit()
        flash('您设置此文章为可以评论', 'info')
    return redirect(url_for('main.show_post', post_id=post_id))


@user_bp.route('/new/comment/<int:post_id>', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(post_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        with db.auto_commit():
            body = form.body.data
            user = current_user._get_current_object()
            comment = Comment(body=body, user=user, post=post)
            db.session.add(comment)
        flash('评论成功', 'success')
        push_comment_notification(post_id=post.id, receiver=post.user, page=page)
    return redirect(url_for('main.show_post', post_id=post_id))


@user_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
    pass


@user_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.user and not current_user.can('ADMIN') and current_user != comment.post.user:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('你已成功删除评论', 'success')
    return redirect(url_for('main.show_post', post_id=comment.post_id))


@user_bp.route('/report/comment<int:comment_id>', methods=['POST'])
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('评论已成功举报', 'success')
    return redirect(url_for('main.show_post', post_id=comment.post_id))

