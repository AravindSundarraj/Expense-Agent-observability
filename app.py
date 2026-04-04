from observability.phoenix_setup import init_phoenix
from agents.expense_agent import run_expense_agent


def main():
    # 🔥 Initialize Phoenix Observability (must be first)
    init_phoenix()

    print("🚀 Expense Agent Started...")

    # Sample user input
    user_input = "I spent $120 on Uber and $50 on food"

    print(f"📥 User Input: {user_input}")

    # Run agent
    result = run_expense_agent(user_input)

    print("📊 Agent Output:")
    print(result)


if __name__ == "__main__":
    main()