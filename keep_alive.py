import httpx
import asyncio

SERVICES = [
    "https://promptpal-api.onrender.com/health",
    "https://promptpal-scholar.onrender.com/health",
    "https://promptpal-coach.onrender.com/health",
    "https://promptpal-formatter.onrender.com/health",
]


async def ping():
    async with httpx.AsyncClient(timeout=10) as client:
        for url in SERVICES:
            try:
                r = await client.get(url)
                print(f"✅ {url} → {r.status_code}")
            except Exception as e:
                print(f"❌ {url} → {e}")

asyncio.run(ping())
