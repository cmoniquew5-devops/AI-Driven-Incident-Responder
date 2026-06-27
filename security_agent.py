import os
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

# =========================================================================
# 1. SETUP CONFIGURATION (SECURE VERSION)
# =========================================================================
# This automatically loads the keys from your hidden .env file
load_dotenv()

# Grab the keys securely from your system environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Initialize the Anthropic client engine using the secure environment variable
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# =========================================================================
# 2. READ THE SECURITY LOG FILE
# =========================================================================
print("📖 Reading local security logs...")
try:
    with open("auth_logs.txt", "r") as file:
        log_data = file.read()
except FileNotFoundError:
    print("❌ Error: Could not find 'auth_logs.txt'. Make sure it's in the same folder!")
    exit()

# =========================================================================
# 3. BUILD THE AI INSTRUCTIONS (PROMPT)
# =========================================================================
prompt = f"""
You are an expert SOC (Security Operations Center) Analyst. 
Analyze the following raw authentication logs. Identify if there is a security threat (like a brute-force attack or unauthorized network access).
Provide a highly structured Incident Triage Report containing:
1. 🚨 **Threat Severity Level** (Low, Medium, High)
2. 📝 **Summary of Malicious Activity** (What happened, which user accounts, and what IP address did it come from?)
3. 🛠️ **Recommended Mitigation Steps** (What immediate action should a junior network admin take?)

Raw Logs to Analyze:
{log_data}
"""

# =========================================================================
# 4. SEND THE DATA TO CLAUDE
# =========================================================================
print("🧠 Sending data to Claude 3.5 Sonnet for analysis...")
try:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    ai_analysis = response.content[0].text
    print("✅ AI Analysis completed successfully.")
except Exception as e:
    print(f"❌ Error talking to Claude API: {e}")
    exit()

# =========================================================================
# 5. AUTOMATICALLY PUSH THE REPORT TO DISCORD (FIXED FOR CHARACTER LIMITS)
# =========================================================================
print("🚀 Pushing report to the team Discord channel...")

# Safeguard: Discord embeds accept up to 4096 characters in the description field.
safe_analysis = ai_analysis[:4000] + "\n\n⚠️ *[Report truncated due to Discord length limits]*" if len(ai_analysis) > 4000 else ai_analysis

payload = {
    "username": "AI Security Agent",
    "embeds": [
        {
            "title": "🛡️ AUTOMATED INCIDENT TRIAGE REPORT",
            "description": safe_analysis,
            "color": 16711680  # This sets the side border color to Red
        }
    ]
}

discord_response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

if discord_response.status_code == 204:
    print("🎉 Success! The Incident Report has been posted to Discord.")
else:
    print(f"⚠️ Discord webhook failed with status code: {discord_response.status_code}")