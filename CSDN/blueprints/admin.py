from flask import Blueprint, flash, render_template, request, current_app, url_for, redirect
from flask_login import login_required, current_user

from CSDN.decorators import permission_required
from CSDN.forms.admin import EditProfileAdminForm, NewCategoryForm
from CSDN.helper import redirect_back
from CSDN.models import User, Post, Comment, Category, db, Role

admin_bp = Blueprint('admin',__name__)


@admin_bp.route('/index')
def index():
    post_count = Post.query.count()
    reported_post_count = Post.query.filter(Post.flag > 0).count()
    user_count = User.query.count()
    locked_user_count = User.query.filter_by(locked=True).count()
    blocked_user_count = User.query.filter_by(active=False).count()

    comment_count = Comment.query.count()
    reported_comments_count = Comment.query.filter(Comment.flag>0).count()
    category_count = Category.query.count()
    return render_template('admin/index.html', post_count=post_count, reported_post_count=reported_post_count,
                           user_count=user_count, locked_user_count=locked_user_count,
                           blocked_user_count=blocked_user_count, comment_count=comment_count,
                           reported_comments_count=reported_comments_count, category_count=category_count)


@admin_bp.route('/manager/post', defaults={'order':'by_flag'})
@admin_bp.route('/manager/post/<order>')
@login_required
@permission_required('ADMIN')
def manage_post(order):
    page = request.args.get('page', 1, type)
    per_page = current_app.config['CSDN_ADMIN_POST_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page)
        order_rule = 'time'
    else:
        pagination = Post.query.order_by(Post.flag.desc()).paginate(page, per_page)
    posts = pagination.items
    return render_template('admin/manage_post.html', pagination=pagination, posts=posts, order_rule=order_rule)


@admin_bp.route('/manager/user')
@login_required
@permission_required('ADMIN')
def manage_user():
    filter_rule = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_MANAGE_USER_PER_PAGE']

    if filter_rule == 'locked':
        pagination = User.query.filter_by(locked=True).paginate(page, per_page)
    elif filter_rule == 'blocked':
        pagination = User.query.filter_by(active=False).paginate(page, per_page)
    else:
        pagination = User.query.paginate(page, per_page)

    users = pagination.items
    return render_template('admin/manage_user.html', pagination=pagination, users=users)


@admin_bp.route('/manager/comment', defaults={'order':'by_flag'})
@admin_bp.route('/manager/comment/<order>')
@login_required
@permission_required('ADMIN')
def manage_comment(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_MANAGE_COMMENT_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page)
        order_rule = 'time'
    else:
        pagination = Comment.query.order_by(Comment.flag.desc()).paginate(page, per_page)
    comments = pagination.items
    return render_template('admin/manage_comment.html', pagination=pagination, order_rule=order_rule, comments=comments)


@admin_bp.route('/manager/category', methods=['GET', 'POST'])
@login_required
@permission_required('ADMIN')
def manage_category():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CSDN_MANAGE_CATEGORY_PER_PAGE']
    pagination = Category.query.order_by(Category.id.asc()).paginate(page, per_page)
    categories = pagination.items
    return render_template('admin/manage_category.html', categories=categories, pagination=pagination)


@admin_bp.route('/delete/category/<int:category_id>', methods=['POST'])
@permission_required('ADMIN')
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    category.delete()
    flash('分类已删除.', 'success')
    return redirect(url_for('admin.manage_category'))


@admin_bp.route('/lock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('ADMIN')
def lock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.lock()
    flash('账号已经锁定.', 'info')
    return redirect_back()


@admin_bp.route('/unlock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('ADMIN')
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unlock()
    flash('取消锁定.', 'info')
    return redirect_back()


@admin_bp.route('/block/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('ADMIN')
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role.name in ['Admin']:
        flash('不能封禁管理员.', 'warning')
    else:
        user.block()
        flash('账号已封禁.', 'info')
    return redirect_back()


@admin_bp.route('/unblock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('ADMIN')
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unblock()
    flash('已经取消用户封禁.', 'info')
    return redirect_back()


@admin_bp.route('/edit/profile/admin/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        with db.auto_commit():
            role = Role.query.get(form.role.data)
            if role.name == 'Locked':
                user.lock()
            user.role = role
            user.username = form.username.data
            user.name = form.name.data
            user.bio = form.bio.data
            user.website = form.website.data
            user.location = form.location.data
        flash('Profile updated.', 'success')
        return redirect_back()
    form.username.data = user.username
    form.role.data = user.role_id
    form.name.data = user.name
    form.bio.data = user.bio
    form.website.data = user.website
    form.location.data = user.location
    return render_template('admin/edit_profile.html', user=user, form=form)


@admin_bp.route('/new_category', methods= ['GET', 'POST'])
@login_required
def new_category():
    form = NewCategoryForm()
    if form.validate_on_submit():
        with db.auto_commit():
            category = Category(name=form.name.data)
            db.session.add(category)
        flash('新的分类创建成功.', 'success')
        return redirect(url_for('main.index'))
    return render_template('admin/new_category.html', form=form)