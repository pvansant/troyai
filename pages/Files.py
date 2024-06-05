import streamlit as st

st.title("File Upload")

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if st.session_state.uploaded_files:
    with st.expander("Previously Uploaded Files", expanded=True):
        # st.markdown("### Uploaded Files:")
        for uploaded_file in st.session_state.uploaded_files:
            st.markdown(f"{uploaded_file.name}")

# Create a file input for the user to upload a CSV
newly_uploaded_files = st.file_uploader(
    "Upload a CSV", type="csv", label_visibility="collapsed", accept_multiple_files=True
)

# If the user has uploaded a file, start the assistant process...
if newly_uploaded_files:
    files_to_process = len(newly_uploaded_files)
    files_processed = 0
    # Create a status indicator to show the user the assistant is working
    with st.status("Starting work...", expanded=False) as status_box:
        for uploaded_file in newly_uploaded_files:
            # Upload the file to OpenAI
            file = st.session_state.client.files.create(
                file=uploaded_file, purpose="assistants"
            )

            # Create a new thread with a message that has the uploaded file's ID
            thread = st.session_state.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Use this data to answer any questions.",
                        "attachments": [
                            {
                                "file_id": file.id,
                                "tools": [{"type": "code_interpreter"}],
                            }
                        ],
                    }
                ]
            )
            files_processed += 1
            status_box.update(
                label=f"Processing files: {files_processed} / {files_to_process} done.",
                state="running",
                expanded=True,
            )
        status_box.update(label="Complete", state="complete", expanded=True)
        st.session_state.thread_id = thread.id
        st.session_state.uploaded_files.extend(newly_uploaded_files)
        st.success("Your files have been processed and your chatbot has been updated.")

if st.session_state.uploaded_files:
    # Add a button to clear the uploaded files
    if st.button("Clear Uploaded Files"):
        st.session_state.uploaded_files = []
        st.rerun()
