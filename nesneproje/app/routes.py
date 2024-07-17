from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm
from app.models import User, Post
from datetime import datetime, timezone

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(query).all()

    return render_template("index.html", title='Home Page', form=form, posts=posts)
    
@app.route('/explore')
@login_required
def explore():
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(query).all()
    return render_template('explore.html', title='Explore', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Bu siteye erişmek için lütfen giriş yapınız', 'warning')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Giriş Yap', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Tebrikler, artık kayıtlı bir kullanıcısınız!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Kayıt Ol', form=form)


@app.route('/about')
def about():
    return render_template('about.html', title='Hakkımızda')


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)



@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(query).all()
    return render_template('admin_dashboard.html', posts=posts)

@app.route('/admin/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.post.data
        db.session.commit()
        flash('Post güncellendi.')
        return redirect(url_for('admin_dashboard'))
    elif request.method == 'GET':
        form.post.data = post.body
    return render_template('edit_post.html', form=form)

@app.route('/admin/delete_post/<int:post_id>')
@login_required
def delete_post(post_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post silindi.')
    return redirect(url_for('admin_dashboard'))
