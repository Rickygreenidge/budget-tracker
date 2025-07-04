import csv
import os

FILENAME = "expenses.csv"

def add_expense():
    category = input("Enter category (e.g. Food, Bills, Gas): ")
    amount = input("Enter amount: ")
    with open(FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([category, amount])
    print(f"✅ Added expense: {category} - ${amount}")

def view_expenses():
    if not os.path.exists(FILENAME):
        print("No expenses recorded yet.")
        return

    total = 0
    print("\n📊 Expenses:")
    with open(FILENAME, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            category, amount = row
            print(f"{category}: ${amount}")
            total += float(amount)
    print(f"\n💰 Total spending: ${total:.2f}")

def main():
    while True:
        print("\n--- Budget Tracker Menu ---")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Exit")

        choice = input("Choose an option (1-3): ")

        if choice == '1':
            add_expense()
        elif choice == '2':
            view_expenses()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()