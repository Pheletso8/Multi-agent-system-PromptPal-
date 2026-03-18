import os
import json
import logging
import tempfile

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [Ingestor]: %(message)s")
logger = logging.getLogger("ingestor")

# Path inside the container (mapped via volume)
OUTPUT_FILE = '/app/data/task.json'


def run():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Check if task already exists from test_tutor.py
    if os.path.exists(OUTPUT_FILE):
        logger.info("⏩ Task file already exists. Skipping creation.")
        return

    task = {
        "query": "If a taxi travels 60km in one hour, how far does it travel in 3 hours?"}

    try:
        # Atomic write strategy
        with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(OUTPUT_FILE), delete=False) as tf:
            json.dump(task, tf, indent=2)
            temp_name = tf.name
        os.replace(temp_name, OUTPUT_FILE)
        logger.info(f"✅ Task created successfully at {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"❌ Ingestor failed: {e}")


if __name__ == "__main__":
    run()
