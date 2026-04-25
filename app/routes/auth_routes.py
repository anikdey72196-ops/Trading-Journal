from flask import Blueprint, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, User
from form import Register, Login

# Create the blueprint
auth_bp = Blueprint('auth', __name__)

# =================================  Register  ============================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if 'user_id' in session:
        return redirect(url_for('main.home'))

    form = Register()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.Password.data, method='pbkdf2:sha256')
        user = User(
            Name=form.Name.data,
            Email=form.Email.data,
            Password=hashed_password, 
            Daily_max_trade=form.Avg_Daily_max_trade.data
        )
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Email or Username might already exist.', 'danger')
            print("Database error during registration.")

    return render_template('register.html', form=form)

# =================================  Login  ============================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.home'))

    form = Login()
    if form.validate_on_submit():
        user = User.query.filter_by(Email=form.Email.data).first()
        
        if user:
            # Check hashed password
            if check_password_hash(user.Password, form.Password.data):
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                return redirect(url_for('main.home'))
            # Fallback for plain text passwords in the current database (auto-upgrades them to hashes)
            elif user.Password == form.Password.data:
                user.Password = generate_password_hash(form.Password.data, method='pbkdf2:sha256')
                db.session.commit()
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                return redirect(url_for('main.home'))
            else:
                flash('Invalid email or password.', 'danger')
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)

# =================================  Logout  ============================
@auth_bp.route('/logout')
def logout():
    """User logout route."""
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
