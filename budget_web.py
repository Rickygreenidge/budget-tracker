from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime("%m-%d-%Y"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime("%m-%d-%Y"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    # LegacyAPIWarning workaround: Use db.session.get for SQLAlchemy 2.0+
    return db.session.get(User, int(user_id))

@app.route("/", methods=["GET"])
@login_required
def home():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.id.desc()).all()
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.id.desc()).all()
    total_income = sum(i.amount for i in incomes)
    total_spent = sum(e.amount for e in expenses)
    remaining = total_income - total_spent

    totals_by_category = {}
    for cat in CATEGORIES:
        totals_by_category[cat] = sum(e.amount for e in expenses if e.category == cat)

    chart_labels = list(totals_by_category.keys())
    chart_data = list(totals_by_category.values())

    html = """<!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                background: #232529;
                color: #e2e4ea;
                font-family: 'Inter', Arial, sans-serif;
                margin: 0;
                min-height: 100vh;
                overflow-x: hidden;
            }
            .navbar {
                width: 100vw;
                background: #22232a;
                display: flex;
                align-items: center;
                padding: 0 1.5rem 0 0;
                height: 64px;
                box-shadow: 0 1px 8px rgba(0,0,0,.08);
                position: fixed;
                top: 0; left: 0; z-index: 100;
                transition: top 0.4s;
            }
            .menu-btn {
                margin-left: 2.2rem;
                margin-top: .3rem;
                background: #26282c;
                border-radius: 18px;
                width: 68px;
                height: 68px;
                border: none;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 102;
                box-shadow: 0 2px 12px rgba(0,0,0,0.10);
                font-size: 2.5rem;
                transition: box-shadow .2s;
            }
            .menu-btn:focus { outline: 2px solid #444ce7; }
            .menu-icon {
                color: #fff;
                font-size: 2.2rem;
                pointer-events: none;
                margin-top: 4px;
            }
            .nav-title {
                font-size: 3.1rem;
                font-weight: 700;
                margin-left: 1.3rem;
                letter-spacing: 0.5px;
                color: #e2e4ea;
                flex: 1;
            }
            .sidebar {
                position: fixed;
                top: 0;
                left: -255px;
                width: 240px;
                height: 100vh;
                background: #22232a;
                box-shadow: 4px 0 32px rgba(0,0,0,.12);
                z-index: 120;
                transition: left .33s;
                padding-top: 80px;
                display: flex;
                flex-direction: column;
            }
            .sidebar.open { left: 0; }
            .sidebar .slogo {
                font-size: 1.3rem;
                font-weight: bold;
                color: #ffe37a;
                margin-bottom: 2.2rem;
                display: flex;
                align-items: center;
                gap: .5rem;
            }
            .sidebar .username {
                font-size: 1.1rem;
                margin-bottom: .9rem;
                color: #fff6b2;
                font-weight: 700;
            }
            .sidebar a, .sidebar .slink {
                display: block;
                color: #e2e4ea;
                padding: 15px 26px 15px 26px;
                text-decoration: none;
                font-size: 1.19rem;
                border-radius: 8px;
                margin: 3px 0;
                transition: background .17s;
            }
            .sidebar a.active, .sidebar a:hover { background: #565af7; color: #fff; }
            .sidebar .logout { color: #ff8282 !important; }
            .sidebar .logout:hover { background: #2d1212; }
            .sidebar .resetpw { color: #ffe37a !important; }
            .sidebar .resetpw:hover { background: #3d3d20; color: #fff; }
            .main-content {
                margin-left: 0;
                margin-top: 72px;
                padding: 16px 32px;
                transition: margin-left .34s;
            }
            @media (min-width: 700px) {
                .main-content { padding-left: 70px; padding-right: 70px; }
            }
            .card {
                background: #28292c;
                border-radius: 16px;
                box-shadow: 0 4px 32px rgba(0,0,0,.16);
                padding: 2.2rem 2.2rem 1.3rem 2.2rem;
                margin-bottom: 24px;
            }
            .card.slim { padding: 1.1rem 1.3rem; }
            .row { display: flex; flex-wrap: wrap; gap: 28px; }
            .col2 { flex: 1 1 350px; }
            .col1 { flex: 1 1 600px; }
            .dashboard-section { margin-bottom: 1.9rem; }
            h2 { font-size: 2.1rem; margin-bottom: 1.4rem; }
            .input-dark {
                background: #18191b;
                color: #fff;
                border: 1.5px solid #444ce7;
                border-radius: 10px;
                padding: 0.65rem 1.1rem;
                font-size: 1.06rem;
                outline: none;
                transition: border .22s;
                margin-right: 1.2rem;
                margin-bottom: .7rem;
                width: 240px;
            }
            .input-dark:focus { border: 1.5px solid #44d964; }
            .input-dark[type="number"]::-webkit-outer-spin-button,
            .input-dark[type="number"]::-webkit-inner-spin-button {
                -webkit-appearance: none;
                margin: 0;
            }
            .input-dark[type="number"] { -moz-appearance: textfield; }
            .btn-main {
                background: #444ce7;
                color: #fff;
                border: none;
                padding: 0.7rem 1.4rem;
                border-radius: 8px;
                font-size: 1.14rem;
                cursor: pointer;
                margin-left: 0.8rem;
                margin-top: 2px;
                transition: background .2s;
            }
            .btn-main:hover { background: #393fb3; }
            .btn-red {
                background: #fb6868;
                color: #fff;
                border: none;
                padding: 0.49rem 1.15rem;
                border-radius: 7px;
                font-size: 1.05rem;
                cursor: pointer;
                margin-left: .75rem;
                transition: background .2s;
            }
            .btn-red:hover { background: #d64242; }
            .category-select { width: 170px; }
            table { width: 100%; border-collapse: collapse; font-size: 1.02rem; }
            th, td { padding: 8px 12px; text-align: left; }
            th { background: #232529; color: #ffe37a; }
            tr:nth-child(even) { background: #26282c; }
            tr:nth-child(odd) { background: #232529; }
            td, th { border-bottom: 1px solid #202126; }
            .chart-box { background: #232529; border-radius: 14px; padding: 1.1rem 1.5rem; margin-top: 15px;}
            .spending { color: #44d964; font-size: 2.35rem; margin: 0.2rem 0; }
            .spending-total { color: #ffd95a; font-size: 2.1rem; font-weight: 700;}
            .pie-box, .bar-box { min-width: 240px; }
            @media (max-width: 1100px) {
                .row { flex-direction: column; }
                .main-content { padding: 16px 5vw; }
                .col2, .col1 { flex: 1 1 100%; }
            }
            @media (max-width: 700px) {
                .navbar { font-size: 1.7rem; }
                .menu-btn { width: 48px; height: 48px; font-size: 1.5rem; }
                .nav-title { font-size: 2.1rem; }
                .sidebar { width: 85vw; min-width: 175px; }
                .main-content { margin-top: 58px; padding: 10px 2vw; }
                .card, .chart-box { padding: 1rem 7vw 1.1rem 7vw; }
            }
        </style>
    </head>
    <body>
        <div class="navbar" id="navbar">
            <button class="menu-btn" id="menuBtn" onclick="toggleSidebar()" aria-label="Menu">
                <span class="menu-icon">&#9776;</span>
            </button>
            <span class="nav-title">Dashboard</span>
        </div>
        <nav class="sidebar" id="sidebar" aria-label="Sidebar">
            <div class="slogo">💰 Tracker</div>
            <div class="username">Logged in as:<br>{{current_user.username}}</div>
            <a href="/" class="active slink">Dashboard</a>
            <a href="/reset_password" class="slink resetpw">Reset Password</a>
            <a href="/logout" class="logout slink">Logout</a>
        </nav>
        <div class="main-content" id="main-content">
            <div class="dashboard-section row">
                <div class="card col2">
                    <h2>Add/Update Income</h2>
                    <form method="POST" action="/add_income" style="display:flex;flex-wrap:wrap;align-items:center;">
                        <input name="amount" class="input-dark" type="number" step="0.01" min="0" placeholder="Income Amount" required autocomplete="off">
                        <button type="submit" class="btn-main">Add/Update</button>
                        <button type="button" class="btn-red" onclick="confirmResetIncome()">Reset Income</button>
                    </form>
                    <div style="margin-top:0.8rem;">Current Total Income: <span style="color:#44d964;font-weight:700;">${{ '{:,.2f}'.format(total_income) }}</span></div>
                </div>
                <div class="card col2 slim">
                    <h2 style="margin-bottom:.8rem;">Remaining Balance</h2>
                    <div class="spending">${{ '{:,.2f}'.format(remaining) }}</div>
                    <div style="font-size:1rem;color:#aaa;">Income minus all expenses</div>
                </div>
            </div>
            <div class="dashboard-section card">
                <h2>Add Expense</h2>
                <form method="POST" action="/add" style="display:flex;flex-wrap:wrap;align-items:center;">
                    <select name="category" class="input-dark category-select" required>
                        <option value="">Select Category</option>
                        {% for cat in categories %}
                        <option value="{{cat}}">{{cat}}</option>
                        {% endfor %}
                    </select>
                    <input name="amount" class="input-dark" type="number" step="0.01" min="0" placeholder="Amount" required autocomplete="off">
                    <input name="description" class="input-dark" type="text" maxlength="100" placeholder="Description (memo)">
                    <button type="submit" class="btn-main">Add</button>
                </form>
            </div>
            <div class="dashboard-section row">
                <div class="card col1">
                    <h2>All Expenses</h2>
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>Category</th>
                            <th>Amount ($)</th>
                            <th>Description</th>
                            <th>Actions</th>
                        </tr>
                        {% for e in expenses %}
                        <tr>
                            <td>{{e.date}}</td>
                            <td>{{e.category}}</td>
                            <td>${{ '{:,.2f}'.format(e.amount) }}</td>
                            <td>{{e.description or ""}}</td>
                            <td>
                                <a href="/edit/{{e.id}}" style="color:#44d964;">Edit</a>
                                <a href="/delete/{{e.id}}" style="color:#ff6464;margin-left:8px;">Delete</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
                <div class="col2">
                    <div class="card slim" style="margin-bottom:16px;">
                        <h2>Totals by Category</h2>
                        <table>
                            <tr><th>Category</th><th>Total ($)</th></tr>
                            {% for cat, total in totals_by_category.items() %}
                            <tr>
                                <td>{{cat}}</td>
                                <td>${{ '{:,.2f}'.format(total) }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                    <div class="card slim" style="margin-bottom:16px;">
                        <h2>Overall Total Spending</h2>
                        <div class="spending-total">${{ '{:,.2f}'.format(total_spent) }}</div>
                    </div>
                    <div class="row">
                        <div class="chart-box pie-box col2">
                            <h3>Spending Pie Chart</h3>
                            <canvas id="pieChart" height="230"></canvas>
                        </div>
                        <div class="chart-box bar-box col2">
                            <h3>Bar Chart by Category</h3>
                            <canvas id="barChart" height="230"></canvas>
                        </div>
                    </div>
                    <div class="card slim" style="margin-top:16px;">
                        <h2>Income History</h2>
                        <table>
                            <tr><th>Date</th><th>Amount</th></tr>
                            {% for i in incomes %}
                            <tr>
                                <td>{{i.date}}</td>
                                <td>${{ '{:,.2f}'.format(i.amount) }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <script>
            let sidebarOpen = false;
            function toggleSidebar() {
                sidebarOpen = !sidebarOpen;
                document.getElementById('sidebar').classList.toggle('open', sidebarOpen);
            }
            // Hide navbar when scrolling down, show when up/top
            let lastScroll = 0;
            window.addEventListener('scroll', function() {
                let navbar = document.getElementById('navbar');
                let currScroll = window.scrollY;
                if (currScroll > lastScroll && currScroll > 60) { navbar.style.top = "-80px"; }
                else { navbar.style.top = "0"; }
                lastScroll = currScroll;
            });
            // Chart.js
            const chartLabels = {{ chart_labels|tojson }};
            const chartData = {{ chart_data|tojson }};
            new Chart(document.getElementById('barChart'), {
                type: 'bar',
                data: {
                    labels: chartLabels,
                    datasets: [{
                        label: "Total",
                        data: chartData,
                        backgroundColor: "#444ce7",
                        borderRadius: 7,
                        borderSkipped: false,
                        barThickness: 38,
                        maxBarThickness: 52
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {legend:{labels:{color:'#e2e4ea'}}},
                    scales: {x:{ticks:{color:'#e2e4ea'}},y:{ticks:{color:'#e2e4ea'}}}
                }
            });
            new Chart(document.getElementById('pieChart'), {
                type: 'pie',
                data: {
                    labels: chartLabels,
                    datasets: [{
                        data: chartData,
                        backgroundColor: [
                            '#444ce7','#fb6868','#44d964','#ffd95a','#565af7','#ffe37a'
                        ]
                    }]
                },
                options: {responsive:true, plugins:{legend:{labels:{color:'#e2e4ea'}}}}
            });
            // Remove up/down on number inputs (income/expense)
            document.querySelectorAll('input[type=number]').forEach(input => {
                input.addEventListener('wheel', function(e){ e.preventDefault(); });
                input.style.appearance = 'textfield';
            });
            // Reset income confirmation
            function confirmResetIncome() {
                if (confirm("Reset income to $0 and delete all income history?")) {
                    window.location.href = "/reset_income";
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html, expenses=expenses, incomes=incomes, total_income=total_income,
                                 total_spent=total_spent, remaining=remaining,
                                 totals_by_category=totals_by_category, categories=CATEGORIES,
                                 chart_labels=chart_labels, chart_data=chart_data, current_user=current_user)

@app.route("/add", methods=["POST"])
@login_required
def add_expense():
    category = request.form["category"]
    amount = float(request.form["amount"])
    description = request.form.get("description", "")
    date = datetime.now().strftime("%m-%d-%Y")
    new_expense = Expense(category=category, amount=amount, description=description, date=date, user_id=current_user.id)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/delete/<int:expense_id>")
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        return "Unauthorized", 403
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        return "Unauthorized", 403
    if request.method == "POST":
        expense.category = request.form["category"]
        expense.amount = float(request.form["amount"])
        expense.description = request.form.get("description", "")
        expense.date = datetime.now().strftime("%m-%d-%Y")
        db.session.commit()
        return redirect(url_for("home"))
    html = """
    <html><head>
        <title>Edit Expense</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { background: #232529; color: #e2e4ea; font-family: 'Inter', Arial, sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; }
            .card { background: #28292c; border-radius: 16px; padding: 2.2rem; min-width: 340px; }
            label { color: #ffd95a; font-size: 1.1rem;}
            .input-dark { background: #18191b; color: #fff; border: 1.5px solid #444ce7; border-radius: 10px; padding: 0.65rem 1.1rem; font-size: 1.06rem; margin-bottom: .7rem; width: 90%; }
            .btn-main { background: #444ce7; color: #fff; border: none; padding: 0.7rem 1.4rem; border-radius: 8px; font-size: 1.14rem; cursor: pointer; margin-top: 10px;}
        </style>
    </head><body>
    <form class="card" method="POST">
        <h2>Edit Expense</h2>
        <label>Category:</label><br>
        <select name="category" class="input-dark" required>
            {% for cat in categories %}
            <option value="{{cat}}" {% if expense.category == cat %}selected{% endif %}>{{cat}}</option>
            {% endfor %}
        </select><br>
        <label>Amount:</label><br>
        <input name="amount" class="input-dark" type="number" step="0.01" min="0" value="{{expense.amount}}" required autocomplete="off"><br>
        <label>Description:</label><br>
        <input name="description" class="input-dark" type="text" maxlength="100" value="{{expense.description or ''}}"><br>
        <button type="submit" class="btn-main">Save</button>
        <a href="/" class="btn-main" style="background:#232529;color:#ffd95a;margin-left:12px;">Cancel</a>
    </form>
    </body></html>
    """
    return render_template_string(html, expense=expense, categories=CATEGORIES)

@app.route("/add_income", methods=["POST"])
@login_required
def add_income():
    amount = float(request.form["amount"])
    date = datetime.now().strftime("%m-%d-%Y")
    new_income = Income(amount=amount, date=date, user_id=current_user.id)
    db.session.add(new_income)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/reset_income")
@login_required
def reset_income():
    incomes = Income.query.filter_by(user_id=current_user.id).all()
    for i in incomes:
        db.session.delete(i)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        error = "Incorrect username or password."
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { background: #232529; color: #e2e4ea; font-family: 'Inter', Arial, sans-serif; margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;}
            .login-box { background: #28292c; border-radius: 16px; box-shadow: 0 4px 32px rgba(0,0,0,.16); padding: 2.5rem 2rem; min-width: 350px; max-width: 95vw;}
            h2 { font-size: 2.1rem; margin-bottom: 1.7rem; font-weight: 700;}
            .err { color: #e2564a; margin-bottom: 18px; }
            input { background: #18191b; color: #fff; border: 1.5px solid #444ce7; border-radius: 10px; padding: 0.65rem 1.1rem; margin-bottom: 1.3rem; font-size: 1.05rem; width: 45%; outline: none; margin-right: 12px; transition: border .22s;}
            input:focus { border: 1.5px solid #44d964; }
            button { background: #444ce7; color: #fff; border: none; padding: 0.7rem 1.4rem; border-radius: 8px; font-size: 1.1rem; cursor: pointer; margin-top: .5rem;}
            a { color: #8f97ff; text-decoration: underline;}
            .reg-link { margin-top: 1.3rem; }
            .forgot-link { margin-top: 0.9rem; font-size: 1rem;}
        </style>
    </head>
    <body>
        <form method="post" class="login-box">
            <h2>Login</h2>
            {% if error %}<div class="err">{{error}}</div>{% endif %}
            <input name="username" placeholder="Username" required>
            <input name="password" placeholder="Password" type="password" required>
            <button type="submit">Login</button>
            <div class="reg-link">No account? <a href='/register'>Register</a></div>
            <div class="forgot-link"><a href='/forgot_password'>Forgot password?</a></div>
        </form>
    </body>
    </html>
    """, error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            error = "Username already taken."
        else:
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
            user = User(username=username, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("home"))
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { background: #232529; color: #e2e4ea; font-family: 'Inter', Arial, sans-serif; margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;}
            .login-box { background: #28292c; border-radius: 16px; box-shadow: 0 4px 32px rgba(0,0,0,.16); padding: 2.5rem 2rem; min-width: 350px; max-width: 95vw;}
            h2 { font-size: 2.1rem; margin-bottom: 1.7rem; font-weight: 700;}
            .err { color: #e2564a; margin-bottom: 18px; }
            input { background: #18191b; color: #fff; border: 1.5px solid #444ce7; border-radius: 10px; padding: 0.65rem 1.1rem; margin-bottom: 1.3rem; font-size: 1.05rem; width: 45%; outline: none; margin-right: 12px; transition: border .22s;}
            input:focus { border: 1.5px solid #44d964; }
            button { background: #444ce7; color: #fff; border: none; padding: 0.7rem 1.4rem; border-radius: 8px; font-size: 1.1rem; cursor: pointer; margin-top: .5rem;}
            a { color: #8f97ff; text-decoration: underline;}
            .reg-link { margin-top: 1.3rem; }
        </style>
    </head>
    <body>
        <form method="post" class="login-box">
            <h2>Register</h2>
            {% if error %}<div class="err">{{error}}</div>{% endif %}
            <input name="username" placeholder="Username" required>
            <input name="password" placeholder="Password" type="password" required>
            <button type="submit">Register</button>
            <div class="reg-link">Already have an account? <a href='/login'>Login</a></div>
        </form>
    </body>
    </html>
    """, error=error)

@app.route("/reset_password", methods=["GET", "POST"])
@login_required
def reset_password():
    error = None
    success = None
    if request.method == "POST":
        pw1 = request.form["password"]
        pw2 = request.form["confirm_password"]
        if pw1 != pw2:
            error = "Passwords do not match."
        elif len(pw1) < 4:
            error = "Password too short."
        else:
            current_user.password = generate_password_hash(pw1, method="pbkdf2:sha256")
            db.session.commit()
            success = "Password updated successfully!"
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reset Password</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { background: #232529; color: #e2e4ea; font-family: 'Inter', Arial, sans-serif; margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;}
            .reset-box { background: #28292c; border-radius: 16px; box-shadow: 0 4px 32px rgba(0,0,0,.16); padding: 2.5rem 2rem; min-width: 350px; max-width: 95vw;}
            h2 { font-size: 2.1rem; margin-bottom: 1.7rem; font-weight: 700;}
            .err { color: #e2564a; margin-bottom: 18px; }
            .success { color: #44d964; margin-bottom: 18px;}
            input { background: #18191b; color: #fff; border: 1.5px solid #444ce7; border-radius: 10px; padding: 0.65rem 1.1rem; margin-bottom: 1.3rem; font-size: 1.05rem; width: 94%; outline: none; margin-right: 12px; transition: border .22s;}
            input:focus { border: 1.5px solid #44d964; }
            button { background: #444ce7; color: #fff; border: none; padding: 0.7rem 1.4rem; border-radius: 8px; font-size: 1.1rem; cursor: pointer; margin-top: .5rem;}
            a { color: #8f97ff; text-decoration: underline;}
        </style>
    </head>
    <body>
        <form method="post" class="reset-box">
            <h2>Reset Password</h2>
            {% if error %}<div class="err">{{error}}</div>{% endif %}
            {% if success %}<div class="success">{{success}}</div>{% endif %}
            <input name="password" placeholder="New Password" type="password" required>
            <input name="confirm_password" placeholder="Confirm New Password" type="password" required>
            <button type="submit">Update Password</button>
            <div style="margin-top: 1.2rem;"><a href="/">Back to Dashboard</a></div>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, error=error, success=success)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    error = None
    success = None
    if request.method == "POST":
        username = request.form["username"]
        pw1 = request.form["password"]
        pw2 = request.form["confirm_password"]
        user = User.query.filter_by(username=username).first()
        if not user:
            error = "Username not found."
        elif pw1 != pw2:
            error = "Passwords do not match."
        elif len(pw1) < 4:
            error = "Password too short."
        else:
            user.password = generate_password_hash(pw1, method="pbkdf2:sha256")
            db.session.commit()
            success = "Password updated! You can now log in."
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Forgot Password</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { background: #232529; color: #e2e4ea; font-family: 'Inter', Arial, sans-serif; margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;}
            .reset-box { background: #28292c; border-radius: 16px; box-shadow: 0 4px 32px rgba(0,0,0,.16); padding: 2.5rem 2rem; min-width: 350px; max-width: 95vw;}
            h2 { font-size: 2.1rem; margin-bottom: 1.7rem; font-weight: 700;}
            .err { color: #e2564a; margin-bottom: 18px; }
            .success { color: #44d964; margin-bottom: 18px;}
            input { background: #18191b; color: #fff; border: 1.5px solid #444ce7; border-radius: 10px; padding: 0.65rem 1.1rem; margin-bottom: 1.3rem; font-size: 1.05rem; width: 94%; outline: none; margin-right: 12px; transition: border .22s;}
            input:focus { border: 1.5px solid #44d964; }
            button { background: #444ce7; color: #fff; border: none; padding: 0.7rem 1.4rem; border-radius: 8px; font-size: 1.1rem; cursor: pointer; margin-top: .5rem;}
            a { color: #8f97ff; text-decoration: underline;}
        </style>
    </head>
    <body>
        <form method="post" class="reset-box">
            <h2>Forgot Password</h2>
            {% if error %}<div class="err">{{error}}</div>{% endif %}
            {% if success %}<div class="success">{{success}}</div>{% endif %}
            <input name="username" placeholder="Your Username" required>
            <input name="password" placeholder="New Password" type="password" required>
            <input name="confirm_password" placeholder="Confirm New Password" type="password" required>
            <button type="submit">Reset Password</button>
            <div style="margin-top: 1.2rem;"><a href="/login">Back to Login</a></div>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, error=error, success=success)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
