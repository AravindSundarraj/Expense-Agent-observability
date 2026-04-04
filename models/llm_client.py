from openai import OpenAI
from openai import OpenAI
from models.config_loader import OPENAI_API_KEY

class LLMClient:

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.temperature = temperature

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generic LLM interface usable by ANY agent.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature
        )

        return response