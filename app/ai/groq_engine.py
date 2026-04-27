from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = "You write short, direct business outreach messages."

def generate_message(name, platform, followers):
    try:
        prompt = f"""
Write a short, direct DM to a fitness influencer.

You are offering access to or sale of an existing YouTube channel.

Context:
- 165k subscriber bodybuilding news channel
- Monetized via sponsorships and placements

Goal:
- Present it as an opportunity
- Make it feel exclusive
- Keep it short and natural

Do NOT sound like an agency.
Do NOT talk about helping them grow.
Be direct.

Lead:
Name: {name}
Platform: {platform}
Followers: {followers}
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
