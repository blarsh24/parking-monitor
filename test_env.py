from dotenv import load_dotenv
import os

load_dotenv()

webhook = os.environ.get('DISCORD_WEBHOOK_URL')
print(f"Webhook loaded: {webhook}")
print(f"Webhook exists: {webhook is not None}")
print(f"Webhook length: {len(webhook) if webhook else 0}")