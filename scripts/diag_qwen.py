import asyncio
import httpx
import time

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"

async def test_qwen():
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'hello world' and nothing else."},
        ],
        "stream": False,
        "options": {"temperature": 0.8, "num_ctx": 4096},
    }
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=90.0) as c:
            r = await c.post(OLLAMA, json=body)
            r.raise_for_status()
            print(f"Reply: {r.json()['message']['content']}")
    except Exception as e:
        print(f"Error: {e}")
    print(f"Time: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_qwen())
