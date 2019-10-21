import random
from faker import Faker
from sqlalchemy.exc import IntegrityError, DataError
from CSDN.models import Category, db, Post, User, Role, Comment, Collect

fake = Faker()


def fake_user(count=20):
    for i in range(count):
        user = User(
            email = fake.email(),
            username = fake.name().replace(' ',''),
            name = fake.word().upper(),
            timestamp = fake.date_time_this_year(),
            bio = fake.sentence(),
            location = fake.city(),
            website = fake.url()
        )
        user.role = Role.query.filter_by(name='User').first()
        user.set_password('123456789')
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_category(count=10):
    category = Category(name='Default')
    db.session.add(category)
    for i in range(count):
        category = Category(name=fake.word())
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_post(count=100):
    for i in range(count):
        post = Post(
            title = fake.sentence(),
            body = fake.text(2000),
            category = Category.query.get(random.randint(1, Category.query.count())),
            timestamp = fake.date_time_this_year(),
            user = User.query.get(random.randint(1, User.query.count()))
        )
        db.session.add(post)
        try:
            db.session.commit()
        except DataError:
            db.session.rollback()


def fake_collect(count=100):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.collect(Post.query.get(random.randint(1, Post.query.count())))
    db.session.commit()


def fake_comment(count=500):
    for i in range(count):
        comment = Comment(
            body = fake.sentence(),
            timestamp = fake.date_time_this_year(),
            user = User.query.get(random.randint(1, User.query.count())),
            post = Post.query.get(random.randint(1, Post.query.count()))
        )
        db.session.add(comment)
        try:
            db.session.commit()
        except DataError:
            db.session.rollback()
