from flask import render_template, url_for, flash, redirect, request, abort
from nimblebox import app, db, bcrypt
from nimblebox.forms import RegistrationForm, LoginForm, MessageForm
from nimblebox.models import User, Message
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Home')


@app.route("/create_account", methods=['GET', 'POST'])
def create_account():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, username=form.username.data, name=form.name.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created successfully! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('createaccount.html', title='Create Account', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(or_(User.username == form.email.data, User.email == form.email.data)).first()
        # user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('get_message'))
            else:
                flash('Login Unsuccessful. Please check email and password', 'danger')
        else:
            flash('You are not registered. Please register now!', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/get_custom_message")
@login_required
def get_message():
    posts = Message.query.filter_by(user_id=current_user.id).first()
    if posts:
        return render_template('message.html', title='Message', post=posts)
    else:
        return render_template('message.html', title='Message', post=current_user.name)


@app.route("/set_custom_message", methods=['GET', 'POST'])
@login_required
def set_message():
    message = Message.query.filter_by(user_id=current_user.id).first()
    if message:
        if message.author != current_user:
            abort(403)
        form = MessageForm()
        if form.validate_on_submit():
            message.content = form.content.data
            db.session.commit()
            flash('Your message has been updated!', 'success')
            return redirect(url_for('get_message'))
        elif request.method == 'GET':
            form.content.data = message.content
        return render_template('updatemessage.html', title='Update Message', form=form)
    else:
        form = MessageForm()
        if form.validate_on_submit():
            post = Message(content=form.content.data, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Your message has been created!', 'success')
            return redirect(url_for('get_message'))
        return render_template('updatemessage.html', title='Update Message', form=form)
