from flask import Flask, render_template_string, request, redirect, url_for
import csv
import os
from collections import defaultdict

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
                category, amount = row
                amount = float(amount)
                expenses.append((category, amount))
                category_totals[category] += amount
                overall_total += amount

    html = """
    <h1>💰 Budget Tracker</h1>

    <h2>Add Expense</h2>
    <form method="post" action="/add">
        Category: <input type="text" name="category" required>
        Amount: <input type="number" step="0.01" name="amount" required>
        <button type="submit">Add</button>
    </form>

    <h2>All Expenses</h2>
    <table border="1" cellpadding="5">
        <tr><th>Category</th><th>Amount ($)</th></tr>
        {% for category, amount in expenses %}
        <tr><td>{{ category }}</td><td>{{ amount }}</td></tr>
        {% endfor %}
    </table>

    <h2>Totals by Category</h2>
    <table border="1" cellpadding="5">
        <tr><th>Category</th><th>Total ($)</th></tr>
        {% for category, total in category_totals.items() %}
        <tr><td>{{ category }}</td><td>{{ "%.2f"|format(total) }}</td></tr>
        {% endfor %}
    </table>

    <h2>Overall Total Spending: ${{ "%.2f"|format(overall_total) }}</h2>
    """

    return render_template_string(html, expenses=expenses, category_totals=category_totals, overall_total=overall_total)

@app.route("/add", methods=["POST"])
def add_expense():
    category = request.form["category"]
    amount = request.form["amount"]
    with open(FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([category, amount])
    return redirect(url_for('home'))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)

