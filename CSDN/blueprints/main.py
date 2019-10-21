from flask import Blueprint, request, current_app, render_template, url_for, redirect, flash
from flask_login import login_required, current_user
from CSDN.decorators import permission_required
from CSDN.fakes import fake_category, fake_post, fake_user, fake_comment, fake_collect
from CSDN.forms.user import CommentForm, PostForm
from CSDN.helper import redirect_back
from CSDN.models import Role, Post, Category, Comment, db, User

main_bp = Blueprint('main',__name__)


@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_PER_PAGE']
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page)
    posts = pagination.items
    categories = Category.query.order_by(Category.id.asc()).all()
    return render_template('main/index.html', pagination=pagination, posts=posts, categories=categories)
    # Role.init_role()
    # fake_user()
    # fake_category()
    # fake_post()
    # fake_collect()
    # fake_comment()
    # return ';sff'


@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        flash('请输入搜索关键字.', 'warning')
        return redirect_back()

    sort = request.args.get('sort', 'post')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_SEARCH_PER_PAGE']
    if sort == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    else:
        pagination = Post.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items
    return render_template('main/search.html', q=q, pagination=pagination, results=results, sort=sort)


@main_bp.route('/new_post', methods=['GET', 'POST'])
@login_required
@permission_required('UPLOAD')
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        with db.auto_commit():
            title = form.title.data
            body = form.body.data
            category = Category.query.get(form.category.data)
            post = Post(title=title, body=body, category=category, user=current_user)
            db.session.add(post)
        flash('文章成功创建', 'success')
        return redirect(url_for('main.show_post', post_id=post.id))
    return render_template('main/new_post.html', form=form)


@main_bp.route('/show_post/<int:post_id>')
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    user = post.user
    categories = Category.query.order_by(Category.name).all()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(post
                                           ).order_by(Comment.timestamp.desc()).paginate(page, per_page)
    comments = pagination.items
    comment_form = CommentForm()
    return render_template('main/post.html', post=post, categories=categories,
                           user=user, pagination=pagination, comments=comments, comment_form=comment_form)


@main_bp.route('/post_previous/<int:post_id>')
def post_previous(post_id):
    post_p = Post.previous(post_id)
    if post_p is None:
        flash('已经是第一篇文章', 'info')
        return redirect(url_for('main.show_post', post_id=post_id))
    return redirect(url_for('main.show_post', post_id=post_p.id))


@main_bp.route('/post_next/<int:post_id>')
def post_next(post_id):
    post_n = Post.next(post_id)
    if post_n is None:
        flash('已经是最后一篇文章', 'info')
        return redirect(url_for('main.show_post', post_id=post_id))
    return redirect(url_for('main.show_post', post_id=post_n.id))


@main_bp.route('/show_category/<int:category_id>', defaults={'order': 'by_time'})
@main_bp.route('/show_category/<int:category_id>/<order>')
def show_category(category_id, order):
    category = Category.query.get_or_404(category_id)
    order_rule = 'time'
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_PER_PAGE']
    pagination = Post.query.with_parent(category).order_by().paginate(page, per_page)
    posts = pagination.items

    if order == 'by_collects':
        posts.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/category.html', category=category,
                           pagination=pagination, order_rule=order_rule, posts=posts)