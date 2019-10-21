DEBUG = True

SQLALCHEMY_DATABASE_URI = 'mysql+cymysql://root:root@localhost:3308/csdn'

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = '\x88D\xf09\x91\x07\x98\x89\x87\x96\xa0A\xc68\xf9\xecJ:U\x17\xc5V\xbe\x8b\xef\xd7\xd8\xd3\xe6\x98*4'

ALBUMY_ADMIN_EMAIL = '1111111111@qq.com'


MAIL_SERVER = 'smtp.qq.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USE_TSL = False
MAIL_USERNAME = '1111111111@qq.com'
MAIL_PASSWORD = 'oqpuucngujvwijac'


class Operations:
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'