from flask import Flask, render_template_string, request, redirect, url_for
import csv
import os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
FILENAME = "expenses.csv"

@app.route("/", methods=["GET"])
def home():
    expenses = []
    category_totals = defaultdict(float)
    overall_total = 0

    if os.path.exists(FILENAME):
        with open(FILENAME, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 3:
                    date, category, amount = row
                    amount = float(amount)
                    expenses.append((date, category, amount))
                    category_totals[category] += amount
                    overall_total += amount

    # Show most recent expenses first
    expenses = expenses[::-1]

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Budget Tracker</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body class="container mt-4">

        <h1 class="mb-4">💰 Budget Tracker</h1>

        <h2>Add Expense</h2>
        <form method="post" action="/add" class="form-inline mb-4">
            <input type="text" name="category" placeholder="Category" required class="form-control mr-2">
            <input type="number" step="0.01" name="amount" placeholder="Amount" required class="form-control mr-2">
            <button type="submit" class="btn btn-primary">Add</button>
        </form>

        <h2>All Expenses</h2>
        <table class="table table-striped">
            <thead>
                <tr><th>Date</th><th>Category</th><th>Amount ($)</th></tr>
            </thead>
            <tbody>
            {% for date, category, amount in expenses %}
            <tr><td>{{ date }}</td><td>{{ category }}</td><td>{{ amount }}</td></tr>
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
    category = request.form["category"]
    amount = request.form["amount"]
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date, category, amount])
    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
