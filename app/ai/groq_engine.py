from groq import Groq
import os

# Initialize client using env variable (Render safe)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_message(lead):
    """
    Generate a HIGH-CONVERSION outreach message
    focused on selling / partnering around a YouTube asset
    """

    prompt = f"""
You are an elite dealmaker reaching out to creators.

You are NOT offering sponsorships.

You are offering access to an already-built YouTube channel asset
that can be:
- acquired
- partnered on
- or scaled together

This is a BUSINESS opportunity.

Lead Info:
Name: {lead['name']}
Niche: {lead['niche']}
Audience: {lead['followers']}

Rules:
- 3 to 4 lines max
- Make it feel exclusive
- No corporate tone
- No generic influencer marketing language
- Sound like a serious opportunity, not a pitch

Write the message:
"""

    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
