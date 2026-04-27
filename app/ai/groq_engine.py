from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = "You write short, persuasive outreach messages for fitness influencers."

def generate_message(name, platform, followers):
    try:
        prompt = f"""
Write a short DM to a fitness creator.

Name: {name}
Platform: {platform}
Followers: {followers}

Offer:
- monetization opportunity
- YouTube/Instagram asset partnership
- sponsorship integration

Keep it natural, short, and non-spammy.
"""

        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
        )

        return res.choices[0].message.content

    except Exception as e:
        print(f"Groq error: {e}")
        return "Error generating message"
