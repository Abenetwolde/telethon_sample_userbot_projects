import asyncio
from telethon import TelegramClient, events
import requests
import random
from datetime import datetime

# Configuration
API_ID = '16359186'  # From my.telegram.org
API_HASH = '3fe7c833abe9e79527f3e5d3481b225b'  # From my.telegram.org
PHONE = '+251964563093'  # Your Telegram phone number
GEMINI_API_KEY = 'AIzaSyAmRSJAgkWfuH1-T19C1vxlzuyMOQEFc3U'  # Your Gemini API key
MODEL_ID = 'gemini-1.5-flash'  # Valid model as of 2025

# Correct Gemini API endpoint
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent"

# Initialize Telethon client (using your user account, not a bot)
client = TelegramClient('user_session', API_ID, API_HASH)

# Load your chat history
with open('chat_history.txt', 'r') as f:
    CHAT_HISTORY = f.read()

# Flag to identify AI-activated contacts
AI_FLAG = "AI-BOT"

# Simple conversation memory (sender ID -> list of recent messages)
convo_memory = {}
# {{context}}
# Gemini prompt with context
BASE_PROMPT = """
You are an AI trained to sound exactly like me based on my past conversations. Here’s a sample of my successful chats with girls that built rapport and attraction:
{CHAT_HISTORY}

Your goal is to chat naturally, build rapport, and steer the conversation toward either setting up a date or inviting her to a house party. Keep it flirty, fun, and authentic to my style and the reply meesage of you should not exceed more than 30 words. Here’s the recent conversation context:
{{context}}

Respond to this message naturally, as if you’re continuing the chat: '{{message}}'
""".replace('{CHAT_HISTORY}', CHAT_HISTORY)

# Function to generate a response using Gemini API
async def generate_response(sender_id, message):
    # Build conversation context
    context = "\n".join(convo_memory.get(sender_id, []))[-500:] or "No prior context yet."
    # Replace placeholders with actual values
    prompt = BASE_PROMPT.replace('{{context}}', context).replace('{{message}}', message)
    print(f"Context: {context}")
    print(f"Message: {message}")
    print(f"Prompt: {prompt}")
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 150,
            "temperature": 0.9
        }
    }
    
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        # Parse Gemini response
        result = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        # Update conversation memory
        convo_memory[sender_id] = convo_memory.get(sender_id, []) + [f"Her: {message}", f"Me: {result}"]
        return result
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error with Gemini API: {e} - Response: {response.text}")
        return random.choice([
            "Hey, you caught me off guard—give me a sec to recover!",
            "Wow, you’re quick! What’s on your mind?",
            "Oops, my charm’s buffering—what’d you say again?"
        ])
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "Hold up, my vibe’s off—let’s rewind and try that again!"

# Check if contact is flagged for AI
async def is_ai_contact(entity):
    if hasattr(entity, 'title'):  # Group chat
        return False
    contact_name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
    return AI_FLAG in contact_name

# Handle incoming messages
@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    sender = await event.get_sender()
    if not sender or not await is_ai_contact(sender):
        return  # Ignore non-flagged contacts

    message = event.message.text
    if not message:
        return  # Ignore empty messages

    print(f"Received from {sender.first_name}: {message}")

    # Random delay to simulate natural typing (5-60 seconds)
    delay = random.uniform(5, 60)
    await asyncio.sleep(delay)

    # Generate and send response
    response = await generate_response(sender.id, message)
    await event.reply(response)
    print(f"Sent: {response}")

    # Occasionally steer toward goal (20% chance)
    # if random.random() < 0.2:
    #     goal_prompt = "Casually suggest meeting up for a date or invite her to a house party."
    #     goal_response = await generate_response(sender.id, goal_prompt)
    #     await asyncio.sleep(random.uniform(5, 15))  # Short delay for follow-up
    #     await event.reply(goal_response)
    #     print(f"Goal message sent: {goal_response}")

# Start the client
async def main():
    await client.start(phone=PHONE)
    print("Chatbot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())