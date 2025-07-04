from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET"])
def home():
    expenses = Expense.query.order_by(Expense.id.desc()).all()
    category_totals = {}
    overall_total = 0

    for exp in expenses:
        overall_total += exp.amount
        if exp.category in category_totals:
            category_totals[exp.category] += exp.amount
        else:
            category_totals[exp.category] = exp.amount

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Budget Tracker</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body class="container mt-4">

        <h1 class="mb-4">💰 Budget Tracker (SQLite)</h1>

        <h2>Add Expense</h2>
        <form method="post" action="/add" class="form-inline mb-4">
            <input type="text" name="name" placeholder="Your Name" required class="form-control mr-2">
            <input type="text" name="category" placeholder="Category" required class="form-control mr-2">
            <input type="number" step="0.01" name="amount" placeholder="Amount" required class="form-control mr-2">
            <button type="submit" class="btn btn-primary">Add</button>
        </form>

        <h2>All Expenses</h2>
        <table class="table table-striped">
            <thead>
                <tr><th>Date</th><th>Name</th><th>Category</th><th>Amount ($)</th><th>Actions</th></tr>
            </thead>
            <tbody>
            {% for exp in expenses %}
            <tr>
                <td>{{ exp.date }}</td>
                <td>{{ exp.name }}</td>
                <td>{{ exp.category }}</td>
                <td>{{ "%.2f"|format(exp.amount) }}</td>
                <td>
                    <a href="/delete/{{ exp.id }}" class="btn btn-sm btn-danger" onclick="return confirm('Delete this expense?');">Delete</a>
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>

        <h2>Totals by Category</h2>
        <table class="table table-bordered">
            <thead>
                <tr><th>Category</th><th>Total ($)</th></tr>
            </thead>
            <tbody>
            {% for category, total in category_totals.items() %}
            <tr><td>{{ category }}</td><td>{{ "%.2f"|format(total) }}</td></tr>
            {% endfor %}
            </tbody>
        </table>

        <h2 class="mt-4">Overall Total Spending: <span class="text-success">${{ "%.2f"|format(overall_total) }}</span></h2>

    </body>
    </html>
    """

    return render_template_string(html, expenses=expenses, category_totals=category_totals, overall_total=overall_total)

@app.route("/add", methods=["POST"])
def add_expense():
    name = request.form["name"]
    category = request.form["category"]
    amount = float(request.form["amount"])
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_expense = Expense(name=name, category=category, amount=amount, date=date)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
