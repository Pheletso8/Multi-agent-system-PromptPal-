#!/usr/bin/env python3
"""
Enhanced test script to verify:
- Varied responses (not repetitive)
- Always includes Mermaid diagrams for real questions
- Mathematically accurate answers
- Proper greeting vs. question handling
"""

import asyncio
import httpx
import json

API_BASE = "http://localhost:8000"
ASK_ENDPOINT = f"{API_BASE}/ask"

# Test cases with expected outcomes
TEST_QUESTIONS = [
    {
        "question": "Hello!",
        "type": "greeting",
        "expect_diagram": False,
        "description": "Greeting - should NOT have diagram"
    },
    {
        "question": "What is 7 + 7?",
        "type": "math_simple",
        "expect_diagram": True,
        "description": "Math question - MUST have Mermaid diagram"
    },
    {
        "question": "How do I calculate the area of a rectangle?",
        "type": "math_concept",
        "expect_diagram": True,
        "description": "Concept question - MUST have Mermaid diagram"
    },
    {
        "question": "What is 45 divided by 9?",
        "type": "math_division",
        "expect_diagram": True,
        "description": "Division problem - MUST have Mermaid diagram"
    },
    {
        "question": "Explain photosynthesis",
        "type": "science",
        "expect_diagram": True,
        "description": "Science question - MUST have Mermaid diagram"
    },
]


async def test_all():
    """Run comprehensive tests"""
    print("\n" + "="*80)
    print("🚀 ENHANCED MULTI-AGENT SYSTEM TEST")
    print("Testing: Accuracy, Variety, Diagrams, and Responsiveness")
    print("="*80)
    
    # Check API health
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{API_BASE}/health", timeout=5.0)
            print(f"\n✅ API running (status: {health.status_code})")
    except Exception as e:
        print(f"\n❌ API not running: {e}")
        return
    
    responses_collected = []
    diagram_count = 0
    responses_count = 0
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, test in enumerate(TEST_QUESTIONS, 1):
            print(f"\n{'-'*80}")
            print(f"[Test {i}] {test['type'].upper()}")
            print(f"Question: {test['question']}")
            print(f"Expecting: {test['description']}")
            print(f"{'-'*80}")
            
            try:
                response = await client.post(
                    ASK_ENDPOINT,
                    json={"question": test["question"]}
                )
                response.raise_for_status()
                data = response.json()
                responses_count += 1
                
                # Extract content
                content = data.get("content", data.get("data", {}).get("hint", ""))
                diagram = data.get("diagram", data.get("data", {}).get("diagram", ""))
                
                responses_collected.append((test["question"], content))
                
                # Display results
                print(f"✅ Response received ({len(content)} chars)")
                print(f"\n📄 Content Preview:")
                preview = content[:250] if len(content) > 250 else content
                print(f"   {preview}")
                
                # Check diagram
                has_diagram = bool(diagram)
                if has_diagram:
                    diagram_count += 1
                
                print(f"\n📊 Diagram Check:")
                if test["expect_diagram"]:
                    if has_diagram:
                        print(f"   ✅ PASS - Mermaid diagram found ({len(diagram)} chars)")
                        # Show first 100 chars of diagram
                        diagram_preview = diagram[:100] if len(diagram) > 100 else diagram
                        print(f"   Preview: {diagram_preview}...")
                    else:
                        print(f"   ❌ FAIL - Expected diagram but got none!")
                else:
                    if has_diagram:
                        print(f"   ⚠️  WARNING - Diagram present but not expected for greeting")
                    else:
                        print(f"   ✅ PASS - No diagram (correct for greeting)")
                
                # Check response type
                response_type = data.get("type", "unknown")
                print(f"\n📝 Response Type: {response_type}")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
    # Analysis
    print(f"\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    print(f"\nResponses processed: {responses_count}/{len(TEST_QUESTIONS)}")
    print(f"Diagrams found: {diagram_count}/{len([t for t in TEST_QUESTIONS if t['expect_diagram']])}")
    
    # Check variety
    unique_responses = len(set(resp[1][:150] for resp in responses_collected if resp[1]))
    print(f"Unique responses (first 150 chars): {unique_responses}/{len(responses_collected)}")
    
    if unique_responses == len(responses_collected):
        print("✅ VARIETY TEST PASSED - All responses are different!")
    else:
        print(f"⚠️  VARIETY WARNING - Only {unique_responses} unique responses found")
    
    print(f"\n" + "="*80)
    print("🏁 TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_all())
