import streamlit, pandas

spreadsheet = ""

streamlit.header("Test file upload")
file = streamlit.file_uploader("Select file", accept_multiple_files=False, type=["csv", "ods", "xlsx"])

if streamlit.button("Upload"):
    if file == None:
        streamlit.error("Upload: None")
    else:
        streamlit.success("Upload: Success")
        user_file_ext = file.name.split('.')[-1].lower()
        print(f"streamlit file: {file.name}\nstreamlit file ext: {user_file_ext}")
        if 'xlsx' in user_file_ext:
            spreadsheet = pandas.read_excel(file) # Requires openpyxl installed
        elif 'csv' in user_file_ext:
            spreadsheet = pandas.read_csv(file)
        elif 'ods' in user_file_ext:
            spreadsheet = pandas.read_excel(file, engine="odf") # Requies odfpy installed
        else:
            print(f"\nAcceptable document types: csv, ods, xlsx\nUnknown document type: {user_file_ext}")
            streamlit.error(f"\nAcceptable document types: csv, ods, xlsx\nUnknown document type: {user_file_ext}")
        streamlit.write(spreadsheet)

