from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = "You write short, persuasive outreach messages for fitness influencers."

def generate_message(name, platform, followers):
    try:
        prompt = f"Write a short DM for {name} ({platform}, {followers} followers) offering monetization and sponsorship opportunities."

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
