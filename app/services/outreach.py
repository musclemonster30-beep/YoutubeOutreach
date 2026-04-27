from app.ai.groq_engine import generate_message


def run_outreach():
    leads = [
        {"name": "FitnessCreatorAlpha", "niche": "Fitness", "followers": "120k"},
        {"name": "BodybuilderPro", "niche": "Bodybuilding", "followers": "250k"},
    ]

    print(f"Loaded {len(leads)} leads\n")

    for lead in leads:
        try:
            message = generate_message(lead)

            print(f"Sending to: {lead['name']}")
            print(message)
            print("-" * 50)

        except Exception as e:
            print(f"❌ Failed for {lead['name']}: {e}")
