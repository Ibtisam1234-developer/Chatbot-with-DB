import streamlit as st
from supabase import create_client, Client
from openai import OpenAI
from datetime import datetime

SUPABASE_URL = "https://bzcrwohnbzvcysujznfi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ6Y3J3b2huYnp2Y3lzdWp6bmZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzMDM0MTMsImV4cCI6MjA2Njg3OTQxM30.K2i0JCusci2k6bTt_ivh7qI71erlDiYam7ZDMU_bqXI"
GEMINI_API_KEY = "AIzaSyCNxpgOwLzhaynmX-ylfFz9j-6knNv28G4"

# Setup Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Setup Gemini client
client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/"
)

# Streamlit config
st.set_page_config(page_title="Chatbot", layout="centered")
page = st.sidebar.selectbox("Choose a page", ["💬 Chat", "📜 Chat History"])

# Save message to Supabase
def save_message(role, content):
    supabase.table("chat_messages").insert({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

# Get history from Supabase
def get_history():
    res = supabase.table("chat_messages").select("*").order("timestamp", desc=True).limit(25).execute()
    return list(reversed(res.data)) if res.data else []

# Clear all chat history
def clear_history():
    supabase.table("chat_messages").delete().neq("id", 0).execute()

# 💬 Chat Page
if page == "💬 Chat":
    st.title("💬 Talk to the Bot")

    # Initialize session state for messages if not already set
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Load historical messages from Supabase into session state (only once)
    if not st.session_state.messages:
        history = get_history()
        st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in history]

    # Display all messages
    for msg in st.session_state.messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        with st.chat_message(msg["role"]):
            st.markdown(content)

    # Chat input (submits on Enter)
    prompt = st.chat_input("Type your message")
    if prompt:
        # Append and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Save user message to Supabase
        save_message("user", prompt)

        # Get assistant response
        try:
            response = client.chat.completions.create(
                model="gemini-1.5-flash",
                messages=st.session_state.messages,
            )
            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
            # Save assistant response to Supabase
            save_message("assistant", reply)
        except Exception as e:
            st.error(f"An error occurred: {e}")

# 📜 History Page
elif page == "📜 Chat History":
    st.title("📜 Chat History")
    messages = get_history()

    if st.button("🧹 Clear Chat History"):
        clear_history()
        st.session_state.messages = []  # Clear session state too
        st.success("Chat history cleared.")
        st.rerun()

    if not messages:
        st.warning("No chat messages found.")
    else:
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]
            timestamp = msg.get("timestamp", "Unknown")
            label = f"**{role}** @{timestamp}"
            if role == "User":
                st.success(f"{label}\n\n{content}")
            elif role == "Assistant":
                st.info(f"{label}\n\n{content}")
            else:
                st.write(f"{label}\n\n{content}")
