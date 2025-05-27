from dotenv import load_dotenv
import os
import requests
from bot.main import start_bot

# ✅ Load .env first
load_dotenv()

# ✅ Then use environment variables
print("🔎 LOG_WEBHOOK_URL =", os.getenv("LOG_WEBHOOK_URL"))

def remove_webhook(token):
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook")
        print("✅ Webhook deleted:", response.json())
    except Exception as e:
        print("❌ Failed to delete webhook:", e)

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    webhook = os.getenv("LOG_WEBHOOK_URL")

    print("🧪 DEBUG - TELEGRAM_TOKEN:", token[:5] + "..." if token else "❌ NOT FOUND")
    print("🧪 DEBUG - LOG_WEBHOOK_URL:", webhook if webhook else "❌ NOT FOUND")

    if not token:
        print("❌ TELEGRAM_TOKEN not found in .env")
        exit()

    if not webhook:
        print("⚠️ LOG_WEBHOOK_URL not found. User logging will fail.")

    remove_webhook(token)
    start_bot(token)
