import os
import requests

def generate_ad_content(prompt):
    """Send a prompt to Gemini API and return the generated ad text."""
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + gemini_api_key
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        try:
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print("Gemini response parse error:", e)
            return ""
    else:
        print(f"Gemini error: {resp.status_code} {resp.text}")
        return ""
