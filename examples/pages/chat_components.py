"""Chat Components page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Chat Components",
    "icon": "💬",
    "order": 90,
}

st.title("💬 Chat Components")
st.caption("Components for building chat interfaces")

# -------------------------------------------------------------------------
# st.chat_message()
# -------------------------------------------------------------------------
st.header("st.chat_message()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `name` (str): Message role - "user", "assistant", "ai", "human", or custom
    - `avatar` (str | None): Avatar emoji, URL, or None for default
    
    **Returns:** Context manager for message content
    """)

st.code('''with st.chat_message("user"):
st.write("Hello! Can you help me with Python?")

with st.chat_message("assistant", avatar="🤖"):
st.write("Of course! What would you like to know about Python?")''', language="python")

with st.container(border=True):
    with st.chat_message("user"):
        st.write("Hello! Can you help me with Python?")
    
    with st.chat_message("assistant", avatar="🤖"):
        st.write("Of course! What would you like to know about Python?")
    
    with st.chat_message("user"):
        st.write("How do I read a CSV file?")
    
    with st.chat_message("assistant", avatar="🤖"):
        st.write("Here's how to read a CSV file:")
        st.code('''import pandas as pd
df = pd.read_csv("data.csv")
print(df.head())''', language="python")

# -------------------------------------------------------------------------
# st.chat_input()
# -------------------------------------------------------------------------
st.header("st.chat_input()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `placeholder` (str): Placeholder text
    - `max_chars` (int | None): Maximum characters
    - `disabled` (bool): Disable input
    - `on_submit` (Callable): Callback on submit
    
    **Returns:** str | None (one-shot, not persisted in session_state)
    
    **Note:** Chat input is pinned to the bottom of the page.
    """)

st.code('''if prompt := st.chat_input("Ask me anything..."):
with st.chat_message("user"):
    st.write(prompt)
with st.chat_message("assistant"):
    st.write(f"You said: {prompt}")''', language="python")

with st.container(border=True):
    st.info("""
    `st.chat_input()` is pinned to the bottom of the page.
    
    Try it! Type a message in the input at the bottom.
    """)

# Demo chat functionality
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hi! I'm a demo chatbot. Ask me anything!"}
    ]

# Display chat history
st.header("Live Chat Demo", divider="blue")

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input (will be at bottom of page)
if prompt := st.chat_input("Type a message..."):
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    
    # Generate response
    response = f"You said: '{prompt}'. This is a demo response!"
    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    st.rerun()
