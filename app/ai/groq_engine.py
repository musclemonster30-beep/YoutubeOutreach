import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_message(name, niche, followers):
    prompt = f"""
You are an expert dealmaker.

Your goal is to pitch the SALE of a YouTube channel.

Lead Info:
Name: {name}
Niche: {niche}
Followers: {followers}

Write a SHORT, direct message proposing:
- Selling a YouTube channel asset
- Monetization opportunity
- Keep it natural, human, not spammy
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # ✅ updated working model
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content
