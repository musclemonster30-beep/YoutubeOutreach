import json

def load_leads():
    with open("data/leads.json", "r") as f:
        return json.load(f)
