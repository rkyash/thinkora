import asyncio

import litellm
from backend.app.schemas import response

from app.config import settings


async def main():
    try:
        # response = await litellm.co(
        #     model="sentence-transformers/all-MiniLM-L6-v2",
        #     input=["hello world"]
        # )
        response = litellm.completion(
                model="ollama/qwen2.5-coder:14b",
                messages=[{"role": "user", "content": "Hello, how are you?"}],
                api_base="http://localhost:11434"
        )
        print(response.choices[0].message.content)

    except Exception as e:
        print("Error:", type(e).__name__, e)

if __name__ == "__main__":
    asyncio.run(main())
