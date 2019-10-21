from threading import Thread

from flask import request, url_for, redirect, render_template, current_app
from flask_mail import Message
from CSDN.extensions import mail
from CSDN.models import Notification, db, User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature

from CSDN.secret import Operations


def redirect_back(default='main.index', **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        return redirect(target)
    return redirect(url_for(default, **kwargs))


def push_follow_notification(follower, receiver):
    body = '用户 <a href="%s">%s</a> 关注了你.' % \
              (url_for('user.index', username=follower.username), follower.username)
    notification = Notification(body=body, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_collect_notification(collector, post_id, receiver):
    body = '用户 <a href="%s">%s</a> 收藏了你的 <a href="%s">文章</a>' % \
              (url_for('user.index', username=collector.username),
               collector.username,
               url_for('main.show_post', post_id=post_id))
    notification = Notification(body=body, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_comment_notification(post_id, receiver, page=1):
    body = '<a href="%s#comments">这篇文章</a> 有了新的回复/评论.' % \
              (url_for('main.show_post', post_id=post_id, page=page))
    notification = Notification(body=body, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def _send_mail(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, to, template, **kwargs):
    msg = Message(subject + 'update.', recipients=[to], sender=current_app.config['MAIL_USERNAME'])
    msg.body = render_template(template+'.txt', **kwargs)
    msg.html = render_template(template+'.html', **kwargs)

    app = current_app._get_current_object()
    thr = Thread(target=_send_mail, args=[app, msg])
    thr.start()
    return thr


def send_reset_password_email(user, token):
    send_email(subject='密码', to=user.email, template='emails/reset_password', token=token, user=user)


def send_reset_email_email(user, token, to=None):
    send_email(subject='邮箱', to=to or user.email, template='emails/change_email', token=token, user=user)


def generate_token(user, operation , expire_in=None, **kwargs):
    s = Serializer(current_app.config['SECRET_KEY'], expire_in)
    data = {'id': user.id, 'operation': operation}
    data.update(**kwargs)
    return s.dumps(data)


def validate_token(user, token, operation, new_password=None):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except (SignatureExpired, BadSignature):
        return False

    if operation != data.get('operation') or data.get(id) != user.id:
        return False
    if operation == Operations.RESET_PASSWORD:
        user.set_password(new_password)
    elif operation == Operations.CHANGE_EMAIL:
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if User.query.filter_by(email=new_email).first() is not None:
            return False
        user.email = new_email
    else:
        return False

    db.session.commit()
    return True