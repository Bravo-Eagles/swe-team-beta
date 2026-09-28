import streamlit

streamlit.text("Hello from swe-team-beta!") # Static text
print("Hello from swe-team-beta!")
input_box = streamlit.text_input("Enter your name", "Type name here")
if streamlit.button("Submit name"):
    streamlit.success(f"Hello {input_box}")
    print(f"Hello {input_box}")

