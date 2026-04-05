
from opentelemetry.trace import Span

from models import llm_client
import json
import re


def extract_expenses_llm(user_input: str):
    llm = llm_client.LLMClient()

    prompt = f"""
Extract all expenses from the input. If the input is ambiguous, make the best guess based on common expense patterns.

Return STRICT JSON format:
[
  {{
    "item": "string",
    "amount": number,
    "currency": "string",
    "date": "string (ISO format)",
    "quantity": number

  }}
]

Input:
{user_input}
"""

    response = llm.chat(
        system_prompt="You extract structured expense data.",
        user_prompt=prompt
    )

    import json
    try:
        extraction_dictionary = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "content": response.choices[0].message.content,
        "json": safe_parse_json(response.choices[0].message.content)

        }
        return extraction_dictionary
    except Exception as e:
        print(f"Failed to parse LLM response. Returning empty list. Error: {e}")
        return []

def safe_parse_json(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return []