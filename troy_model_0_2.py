import os

import streamlit as st
from openai import OpenAI

ASSISTANT_NAME = "TroyAI"
ASSISTANT_DESCRIPTION = "You are TroyAI, you help restaurants."
ASSISTANT_INSTRUCTIONS = "Try to be clear and brief. Don't invent data."
ASSISTANT_MODEL = "gpt-3.5-turbo-0125"  # this is currently the cheapest model

CHATBOT_TITLE = "TroyAI Demo"
CHATBOT_PROMPT = "How can TroyAI help?"

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Create OpenAI assistant
assistant = client.beta.assistants.create(
    name=ASSISTANT_NAME,
    description=ASSISTANT_DESCRIPTION,
    instructions=ASSISTANT_INSTRUCTIONS,
    model=ASSISTANT_MODEL,
    tools=[{"type": "code_interpreter"}],
)

# Initialize Streamlit app
st.title(CHATBOT_TITLE)

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
        if message["type"] == "text":
            st.markdown(message["content"])
        elif message["type"] == "image_file":
            st.image(message["content"])
        else:
            unknown_type = message["type"]
            msg = f"Unknown type: {unknown_type}"
            raise ValueError(msg)

# React to user input
if prompt := st.chat_input(CHATBOT_PROMPT):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "type": "text"}
    )

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
                    {"role": "assistant", "content": response, "type": "text"}
                )

            if msg.type == "image_file":
                image_file_id = msg.image_file.file_id
                chart_out_path = f"./outputs/{image_file_id}.png"
                image_data = client.files.content(image_file_id)
                image_data_bytes = image_data.read()

                # This doesn't work with a deployed TroyAI app.
                # with open(chart_out_path, "wb") as file:
                #     file.write(image_data_bytes)

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.image(image_data_bytes)
                # Add assistant response to chat history
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "type": "image_file",
                        "content": image_data_bytes,
                    }
                )
