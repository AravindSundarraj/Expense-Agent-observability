EXPENSE_SYSTEM_PROMPT = """
You are a helpful financial assistant.
You analyze expenses and provide clear insights.
"""

EXPENSE_USER_PROMPT_TEMPLATE = """
User input:
{user_input}

Classified items:
{classified_items}

Summary:
{summary}

Task:
Generate a short, human-friendly financial insight.
"""