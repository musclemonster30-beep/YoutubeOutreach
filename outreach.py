import time
from app.ai.groq_engine import generate_message

leads = [
    {"name": "FitnessCreatorAlpha", "niche": "fitness", "followers": "120k"},
    {"name": "BodybuilderPro", "niche": "bodybuilding", "followers": "250k"},
]

def run_outreach():
    print("Starting outreach loop...")

    while True:
        for lead in leads:
            try:
                message = generate_message(
                    name=lead["name"],
                    niche=lead["niche"],
                    followers=lead["followers"]
                )

                print(f"\nSending to: {lead['name']}")
                print(message)

                time.sleep(10)

            except Exception as e:
                print(f"Error: {e}")

        print("Cycle complete. Sleeping...")
        time.sleep(60)
