"""Test OpenRouter API connectivity."""
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-v1-",  # Replace with your OpenRouter key
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "AI-PR Agent",
    }
)

try:
    response = client.chat.completions.create(
        # Option 1: Exact model ID for Nemotron 3 Ultra Free
        model="nvidia/nemotron-3-ultra-550b-a55b:free",
        
        # Option 2 (Alternative): Let OpenRouter select an active free model automatically
        # model="openrouter/free",

        messages=[
            {"role": "system", "content": "You are a helpful assistant. Answer briefly."},
            {"role": "user", "content": "What is best ai model and state your name?"},
        ],
        temperature=0.1,
    )

    print("✅ Connection works!")
    print(f"Response: {response.choices[0].message.content}")

except Exception as e:
    print(f"❌ Error: {e}")