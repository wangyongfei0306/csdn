from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_mail import Mail
from flask_moment import Moment
from flask_login import LoginManager, AnonymousUserMixin
from flask_whooshee import Whooshee
from flask_wtf import CSRFProtect


bootstrap = Bootstrap()
moment = Moment()
login_manager = LoginManager()
csrf = CSRFProtect()
ckeditor = CKEditor()
mail = Mail()
whooshee = Whooshee()


@login_manager.user_loader
def get(uid):
    from CSDN.models import User
    return User.query.get(int(uid))


login_manager.login_view = 'auth.login'
login_manager.login_message = u'请先登录或注册'
login_manager.login_message_category = 'warning'


class Guest(AnonymousUserMixin):
    @property
    def is_admin(self):
        return False

    def can(self, permission_name):
        return False

login_manager.anonymous_user = Guest