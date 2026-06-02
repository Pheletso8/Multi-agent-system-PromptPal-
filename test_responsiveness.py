#!/usr/bin/env python3
"""
Test script to verify the multi-agent system is responsive and interactive.
Tests different question types to ensure varied responses.
"""

import asyncio
import httpx
import json
from typing import Optional

# API endpoint
API_BASE = "http://localhost:8000"
ASK_ENDPOINT = f"{API_BASE}/ask"
STREAM_ENDPOINT = f"{API_BASE}/ask/stream"

# Test cases
TEST_QUESTIONS = [
    {
        "question": "Hello!",
        "type": "greeting",
        "expect": "Coach Pal"
    },
    {
        "question": "Hi there",
        "type": "greeting",
        "expect": "Coach Pal"
    },
    {
        "question": "What is 7 + 7?",
        "type": "math_simple",
        "expect": "guiding questions"
    },
    {
        "question": "How do I calculate the area of a rectangle?",
        "type": "math_concept",
        "expect": "measurements"
    },
    {
        "question": "Explain photosynthesis",
        "type": "science",
        "expect": "question"
    },
    {
        "question": "What is the capital of France?",
        "type": "geography",
        "expect": "think"
    }
]


async def test_regular_endpoint():
    """Test the regular /ask endpoint"""
    print("\n" + "="*60)
    print("TESTING REGULAR ENDPOINT (/ask)")
    print("="*60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, test in enumerate(TEST_QUESTIONS, 1):
            print(f"\n[Test {i}] {test['type'].upper()}: '{test['question']}'")
            print("-" * 60)

            try:
                response = await client.post(
                    ASK_ENDPOINT,
                    json={"question": test["question"]}
                )
                response.raise_for_status()
                data = response.json()

                print(f"✅ Status: {data.get('status')}")
                print(f"📝 Type: {data.get('type')}")
                print(
                    f"🎯 Contains '{test['expect']}': {test['expect'].lower() in str(data).lower()}")

                # Extract and display main content
                if "content" in data:
                    hint = data["content"]
                else:
                    hint = data.get("data", {}).get("hint", "")

                if hint:
                    preview = hint[:200] + "..." if len(hint) > 200 else hint
                    print(f"📄 Response preview:\n{preview}")

                # Check for diagram
                diagram = data.get("diagram", data.get(
                    "data", {}).get("diagram", ""))
                if diagram:
                    print(f"📊 Diagram found: Yes ({len(diagram)} chars)")
                else:
                    print(f"📊 Diagram found: No")

            except Exception as e:
                print(f"❌ Error: {e}")


async def test_streaming_endpoint():
    """Test the streaming /ask/stream endpoint"""
    print("\n" + "="*60)
    print("TESTING STREAMING ENDPOINT (/ask/stream)")
    print("="*60)

    test = TEST_QUESTIONS[2]  # Use a math question
    print(f"\n[Stream Test] {test['type'].upper()}: '{test['question']}'")
    print("-" * 60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST",
                STREAM_ENDPOINT,
                json={"question": test["question"]},
                timeout=120.0
            ) as response:
                response.raise_for_status()
                print("📡 Receiving stream events:")

                event_count = 0
                final_response = None

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        event_count += 1
                        try:
                            event_data = json.loads(line[6:])

                            if event_data.get("status") == "processing":
                                stage = event_data.get("stage", "unknown")
                                print(f"  ⏳ Stage {event_count}: {stage}")
                            elif event_data.get("status") == "success":
                                final_response = event_data
                                print(f"  ✅ Final response received")
                            elif event_data.get("status") == "error":
                                print(
                                    f"  ❌ Error: {event_data.get('message')}")
                        except json.JSONDecodeError:
                            pass

                print(f"\n📊 Total events: {event_count}")
                if final_response:
                    print(f"✅ Stream completed successfully")
                    content = final_response.get("content", "")
                    if content:
                        preview = content[:150] + \
                            "..." if len(content) > 150 else content
                        print(f"📄 Response preview:\n{preview}")

        except Exception as e:
            print(f"❌ Stream error: {e}")


async def test_response_consistency():
    """Test that different questions produce different responses"""
    print("\n" + "="*60)
    print("TESTING RESPONSE CONSISTENCY")
    print("="*60)

    responses = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for test in TEST_QUESTIONS[:3]:  # Test first 3
            try:
                response = await client.post(
                    ASK_ENDPOINT,
                    json={"question": test["question"]}
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("content", data.get(
                    "data", {}).get("hint", ""))
                responses.append((test["question"], content))

            except Exception as e:
                print(f"❌ Error testing '{test['question']}': {e}")

    print(f"\n📋 Testing if responses are unique:")
    print("-" * 60)

    unique_responses = len(set(resp[1][:100]
                           for resp in responses))  # First 100 chars
    print(f"Total responses: {len(responses)}")
    print(f"Unique responses: {unique_responses}")

    if unique_responses == len(responses):
        print("✅ All responses are different (system is interactive)")
    else:
        print("⚠️  Some responses are similar (check for duplicate logic)")

    # Print each response
    for question, response in responses:
        print(f"\n❓ Q: {question}")
        preview = response[:100] + "..." if len(response) > 100 else response
        print(f"📄 A: {preview}")


async def main():
    """Run all tests"""
    print("\n🚀 MULTI-AGENT SYSTEM RESPONSIVENESS TEST")
    print("=" * 60)

    # Check API health first
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{API_BASE}/health", timeout=5.0)
            print(f"✅ API is running (health status: {health.status_code})")
    except Exception as e:
        print(f"❌ API is not running: {e}")
        print("Please start the API server first!")
        return

    # Run tests
    try:
        await test_regular_endpoint()
        await test_streaming_endpoint()
        await test_response_consistency()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

    print("\n" + "="*60)
    print("🏁 TEST SUITE COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
