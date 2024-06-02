import os

import streamlit as st
from openai import OpenAI

CHATBOT_PROMPT = "How can TroyAI help?"

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create OpenAI assistant
assistant = client.beta.assistants.create(
    name="Troy AI",
    description="You are Troy AI, you help restaurants.",
    instructions="Try to be clear and brief. Don't invent data.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-3.5-turbo-0125",  # this is currently the cheapest model
)

# Initialize Streamlit app
st.title("TroyAI Demo")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Check if thread_id exists in session state, otherwise create a new thread
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input(CHATBOT_PROMPT):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Create user message in OpenAI thread
    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt,
    )

    # Stream OpenAI assistant response
    with client.beta.threads.runs.stream(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant.id,
    ) as stream:
        stream.until_done()

    # Get list of messages in the thread
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)

    # get only the assistant messages since the last user message
    latest_assistant_messages = []
    for msg in messages.data:
        if msg.role == "user":
            break
        latest_assistant_messages.append(msg)

    # Get the latest assistant message and display it
    for m in latest_assistant_messages[::-1]:
        for msg in m.content:
            if msg.type == "text":
                response = msg.text.value

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(response)
                # Add assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

            if msg.type == "image_file":
                image_file_id = msg.image_file.file_id

                chart_out_path = f"./outputs/{image_file_id}.png"
                image_data = client.files.content(image_file_id)
                image_data_bytes = image_data.read()

                with open(chart_out_path, "wb") as file:
                    file.write(image_data_bytes)

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.image(chart_out_path)
                # Add assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"![image]({chart_out_path})"}
                )