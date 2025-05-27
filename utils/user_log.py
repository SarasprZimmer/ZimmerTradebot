import os
import requests

# ✅ Log user when they start the bot
def log_user(chat_id, username):
    webhook = os.getenv("LOG_WEBHOOK_URL")
    if not webhook:
        print("⚠️ LOG_WEBHOOK_URL not set.")
        return

    payload = {
        "type": "user",
        "chat_id": chat_id,
        "username": username
    }

    try:
        res = requests.post(webhook, json=payload)
        print("✅ User logged:", res.text)
    except Exception as e:
        print("❌ Error logging user:", e)

# ✅ Check if a user is returning (stub version for now)
def is_returning_user(chat_id):
    # Always returns False for now
    # You can later check a local cache or saved file if needed
    return False

# ✅ Log feedback to Google Sheet
def log_feedback(chat_id, username, feedback):
    webhook = os.getenv("LOG_WEBHOOK_URL")
    if not webhook:
        print("⚠️ LOG_WEBHOOK_URL not set.")
        return

    payload = {
        "type": "feedback",
        "chat_id": chat_id,
        "username": username,
        "feedback": feedback
    }

    try:
        res = requests.post(webhook, json=payload)
        print("✅ Feedback logged:", res.text)
    except Exception as e:
        print("❌ Error logging feedback:", e)

# ✅ Track usage of analysis per user
def increment_usage_count(chat_id, username):
    webhook = os.getenv("LOG_WEBHOOK_URL")
    if not webhook:
        print("⚠️ LOG_WEBHOOK_URL not set.")
        return

    payload = {
        "type": "usage",
        "chat_id": chat_id,
        "username": username
    }

    try:
        res = requests.post(webhook, json=payload)
        print("✅ Usage updated:", res.text)
    except Exception as e:
        print("❌ Error updating usage:", e)
