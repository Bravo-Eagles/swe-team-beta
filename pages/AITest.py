import streamlit
from src.ai_request import AIRequest
from src.passwords import require_login
from src.sidebar import sidebar
from src.style import setup_page

# Must run before any other Streamlit call (including require_login and sidebar)
setup_page("AI Request", gradient=False)

#require Login
require_login()
sidebar()

with streamlit.container(border=True, key="card_request"):
    input_api = streamlit.text_input("Type your api key", "Type api key here")
    input_instruction = streamlit.text_input("Type your instructions", "In what way should I respond")
    input_text = streamlit.text_input("Type your question", "Type question")

if streamlit.button("Submit request", type="primary"):
    print(input_api,input_instruction,input_text)
    Rocky = AIRequest(input_api)
    Response = Rocky.send(input_text, instructions=input_instruction)
    print(Response.json())
    streamlit.success(Response.json()["output_text"])
    streamlit.write(Response.json())