import requests
import json


def ask_prompt_pal(question):
    url = "http://localhost:8000/ask"
    payload = {"question": question}

    print(f"🚀 Sending question to PromptPal: {question}")

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        print("\n" + "="*60)
        print(f"✨ COACH HINT: {result['data']['hint']}")
        print(f"📊 DIAGRAM: \n{result['data']['diagram']}")
        print("="*60)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Ensure your docker containers are running before starting this!
    ask_prompt_pal("How do I calculate the area of a rectangle?")
