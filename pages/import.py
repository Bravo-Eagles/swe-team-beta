import streamlit

streamlit.text("Hello from swe-team-beta!") # Static text
print("Hello from swe-team-beta!")
input_box = streamlit.text_input("Enter your name", "Type name here")
if streamlit.button("Submit name"):
    streamlit.success(f"Hello {input_box}")
    print(f"Hello {input_box}")
streamlit.text("Test file upload")
file = streamlit.file_uploader("Select file")
if streamlit.button("Upload"):
    if file == None:
        streamlit.error("Upload: None")
    else:
        streamlit.success("Upload: Success")

