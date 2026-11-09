import os
from dotenv import load_dotenv
from groq import AsyncGroq
import asyncio

load_dotenv()
key = os.getenv("GROQ_API_KEY")
print("Key loaded:", bool(key))

client = AsyncGroq(api_key=key)

async def test():
    resp = await client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": "Say hello in JSON: {\"msg\": \"hi\"}"}],
        response_format={"type": "json_object"},
        max_tokens=20,
    )
    print(resp.choices[0].message.content)

asyncio.run(test())