# llm.py

import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None


def make_llm_request(prompt_text, rules, temp=0.7, max_tokens=300):
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": rules},
            {"role": "user", "content": prompt_text},
        ],
        temperature=temp,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content.strip()