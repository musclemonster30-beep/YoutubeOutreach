import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_message(name, followers):
    prompt = f"""
You are writing a cold DM to a creator.

Your goal: propose selling or partnering on a YouTube channel.

Context:
- We own a YouTube channel in the bizarre / history niche
- We are looking to sell it or partner with creators
- Tone: direct, confident, business-focused
- No generic influencer marketing talk

Lead:
Name: {name}
Audience Size: {followers}

Write a short message (3–5 lines max).
"""

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return completion.choices[0].message.content.strip()
