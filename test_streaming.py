import httpx
import json
import asyncio

async def test_streaming():
    url = "http://localhost:8000/ask"
    payload = {"question": "How do I add fractions with different denominators?"}
    
    print(f"🚀 Testing streaming from: {url}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                print("✅ Connected to stream. Receiving events...\n")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        event_type = data.get("type")
                        
                        if event_type == "hint_delta":
                            print(data.get("delta"), end="", flush=True)
                        elif event_type == "complete":
                            print("\n\n✅ Stream Complete!")
                            print(f"📊 Final Data received (Diagram length: {len(data['data']['diagram'])})")
                        elif event_type == "error":
                            print(f"\n❌ Server Error: {data.get('detail')}")
                            
        except Exception as e:
            print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_streaming())
