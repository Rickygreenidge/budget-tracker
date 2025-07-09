from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

CATEGORIES = ["Bills", "Debt", "Savings", "Fun", "Emergency Fund", "Groceries"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100))
    date = db.Column(db.String(10), default=lambda: datetime.now().strftime("%m-%d-%Y"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), default=lambda: datetime.now().strftime("%m-%d-%Y"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Create database tables once at startup
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        error = 'Incorrect username or password.'
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['password']
        confirm = request.form['confirm_password']
        if pw != confirm:
            error = 'Passwords do not match.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already taken.'
        else:
            hashed = generate_password_hash(pw)
            db.session.add(User(username=username, password=hashed))
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    error = success = None
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['password']
        confirm = request.form['confirm_password']
        user = User.query.filter_by(username=username).first()
        if not user:
            error = 'Username not found.'
        elif pw != confirm:
            error = 'Passwords do not match.'
        else:
            user.password = generate_password_hash(pw)
            db.session.commit()
            success = 'Password reset! You can now log in.'
    return render_template('forgot_password.html', error=error, success=success)


@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    error = success = None
    if request.method == 'POST':
        pw = request.form['password']
        confirm = request.form['confirm_password']
        if pw != confirm:
            error = 'Passwords do not match.'
        else:
            current_user.password = generate_password_hash(pw)
            db.session.commit()
            success = 'Password updated successfully!'
    return render_template('reset_password.html', error=error, success=success)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/', methods=['GET'])
@login_required
def home():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.id.desc()).all()
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.id.desc()).all()
    total_income = sum(i.amount for i in incomes)
    total_spent = sum(e.amount for e in expenses)
    remaining = total_income - total_spent

    totals_by_category = {
        cat: sum(e.amount for e in expenses if e.category == cat)
        for cat in CATEGORIES
    }
    chart_labels = list(totals_by_category.keys())
    chart_data = list(totals_by_category.values())

    return render_template(
        'dashboard.html',
        expenses=expenses,
        incomes=incomes,
        total_income=total_income,
        total_spent=total_spent,
        remaining=remaining,
        totals_by_category=totals_by_category,
        chart_labels=chart_labels,
        chart_data=chart_data,
        categories=CATEGORIES
    )


@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    cat = request.form['category']
    amt = float(request.form['amount'])
    desc = request.form.get('description', '')
    dt = datetime.now().strftime("%m-%d-%Y")
    db.session.add(Expense(
        category=cat, amount=amt, description=desc, date=dt, user_id=current_user.id
    ))
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    e = Expense.query.get_or_404(expense_id)
    if e.user_id != current_user.id:
        return 'Unauthorized', 403
    if request.method == 'POST':
        e.category = request.form['category']
        e.amount = float(request.form['amount'])
        e.description = request.form.get('description', '')
        e.date = datetime.now().strftime("%m-%d-%Y")
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit_expense.html', expense=e, categories=CATEGORIES)


@app.route('/delete/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    e = Expense.query.get_or_404(expense_id)
    if e.user_id != current_user.id:
        return 'Unauthorized', 403
    db.session.delete(e)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    amt = float(request.form['amount'])
    dt = datetime.now().strftime("%m-%d-%Y")
    db.session.add(Income(amount=amt, date=dt, user_id=current_user.id))
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/reset_income')
@login_required
def reset_income():
    Income.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
