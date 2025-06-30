import asyncio
import os
import psycopg2
import chainlit as cl
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "chatbot-db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "your_password_here")
)
cursor = conn.cursor()

def ensure_table_exists():
    with open("init.sql", "r") as f:
        cursor.execute(f.read())
        conn.commit()

ensure_table_exists()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Save message to DB
def save_message(role, content):
    cursor.execute(
        "INSERT INTO chat_messages (role, content) VALUES (%s, %s)",
        (role, content)
    )
    conn.commit()

# Get last 25 messages for context
def get_message_history(limit=25):
    cursor.execute(
        "SELECT role, content FROM chat_messages ORDER BY timestamp DESC LIMIT %s",
        (limit,)
    )
    rows = cursor.fetchall()
    return list(reversed(rows))  # Ensure oldest to newest order

@cl.on_message
async def handle_message(message: cl.Message):
    save_message("user", message.content)

    # Include past 25 messages
    history = [{"role": role, "content": content} for role, content in get_message_history()]
    history.append({"role": "user", "content": message.content})

    response = client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=history,
        stream=True
    )

    stream_msg = cl.Message(content="")

    async def stream_tokens():
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                await stream_msg.stream_token(token)

    await asyncio.create_task(stream_tokens())
    await stream_msg.send()

    # Save assistant's reply to DB
    save_message("assistant", stream_msg.content)
