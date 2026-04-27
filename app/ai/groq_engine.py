import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_message(name, followers):
    prompt = f"""
You are writing a cold DM to a creator.

Goal: propose selling or partnering on a YouTube channel.

Context:
- Niche: bizarre history / WWII
- Intent: sell or partner
- Tone: direct, no fluff

Lead:
Name: {name}
Audience: {followers}

Write a short message (3–4 lines).
"""

    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",   # ✅ UPDATED MODEL
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return completion.choices[0].message.content.strip()
