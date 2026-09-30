import streamlit, pandas

### Notes & other information
# Stages of processing user file
    # Stage 1 - Getting data for processing
        # Retrieve the character(s) that marks a student as present
        # Retrieve the character(s) that marks a student as absent
        # Get date location(s)
        # Get name location(s)
    # Stage 2 - Display data for user to confirm/modify
        # Allow user to change/enter additional info
    # Stage 3 - Load into database
# Actions should always be reversable 


# Local Variables (Accessable across entire file)
# Streamlit forgets on each pass of the script unless you use st.session_state
# TODO: FIX THIS YOU!!!
if "import_bitwiseFlag" not in streamlit.session_state:
    streamlit.session_state.import_spreadsheet = ""
    streamlit.session_state.import_presentString = "" # Character(s) that marks student as present
    streamlit.session_state.import_absentString = "" # Character(s) that marks student as absent
    streamlit.session_state.import_dateRange = "" # Stores the cell range that contains dates
    streamlit.session_state.import_nameRange = "" # Stores the cell range that contains names
    streamlit.session_state.import_bitwiseFlag = 0
# 0 = Whether a file has been uploaded
# 1 = Import is XLSX
# 2 = Import is CSV
# 3 = Import is ODS
# 4 = Stage 1 
# 5 = Present String exists
# 6 = Absent String exists
# 7 = Date(s) Location exists
# 8 = Name(s) Location exists
# 9 = Stage 1
# 11 = Stage 2
#  = User confirmed data


# Local Variable Alias
spreadsheet = streamlit.session_state.import_spreadsheet
presentString = streamlit.session_state.import_presentString
absentString = streamlit.session_state.import_absentString
dateRange = streamlit.session_state.import_dateRange
nameRange = streamlit.session_state.import_nameRange
bitwiseFlag = streamlit.session_state.import_bitwiseFlag


### Helper functions
def save():
    streamlit.session_state.import_spreadsheet = spreadsheet
    streamlit.session_state.import_presentString = presentString
    streamlit.session_state.import_absentString = absentString
    streamlit.session_state.import_dateRange = dateRange
    streamlit.session_state.import_nameRange = nameRange
    streamlit.session_state.import_bitwiseFlag = bitwiseFlag
def back():
    global bitwiseFlag
    if bitwiseFlag & (1 << 4):
        bitwiseFlag = 0
    save()
    streamlit.rerun()

### Real code (Congrats! You survived)
if not (bitwiseFlag & 1): # If file hasn't been uploaded
    streamlit.header("Test file upload")
    file = streamlit.file_uploader("Select file", accept_multiple_files=False, type=["csv", "ods", "xlsx"])

    if streamlit.button("Upload"):
        if file == None:
            streamlit.error("Upload: None")
            bitwiseFlag &= ~(1 | 2 | 4 | 8) # Sets 0,1,2,3 to 0
        else:
            streamlit.success("Upload: Success")
            user_file_ext = file.name.split('.')[-1].lower()
            print(f"streamlit file: {file.name}\nstreamlit file ext: {user_file_ext}")
            if 'xlsx' in user_file_ext:
                spreadsheet = pandas.read_excel(file) # Requires openpyxl installed
                bitwiseFlag |= (1 << 0) | (1 << 1) # Received XLSX
            elif 'csv' in user_file_ext:
                spreadsheet = pandas.read_csv(file)
                bitwiseFlag |= (1 << 0) | (1 << 2) # Received CSV
            elif 'ods' in user_file_ext:
                spreadsheet = pandas.read_excel(file, engine="odf") # Requies odfpy installed
                bitwiseFlag |= (1 << 0) | (1 << 3) # Received ODS
            else:
                print(f"\nAcceptable document types: csv, ods, xlsx\nUnknown document type: {user_file_ext}\nBitwise: {bin(bitwiseFlag)}")
                streamlit.error(f"\nAcceptable document types: csv, ods, xlsx\nUnknown document type: {user_file_ext}")
                bitwiseFlag &= ~(2 | 4 | 8) # Resets file type flags to 0
            bitwiseFlag |= (1 << 4) # Starts stage 1 - Get user input for data processing
            save()
            streamlit.rerun()

elif bitwiseFlag & (1 << 4): # Stage 1
    streamlit.write(spreadsheet)
    streamlit.write("Alright! Now we need your help! Use the boxes below so we can import your file correctly.")
    
    dateRange = streamlit.text_input("Provide the range of cells that contain the date", "Type here")
    nameRange = streamlit.text_input("Provide the range of cells that contain student's names", "Type here")
    presentString = streamlit.text_input("Text that marks students as present", "Type here")
    absentString = streamlit.text_input("Text that marks students as absent", "Type here")
    if streamlit.button("Back"):
        back()
    if streamlit.button("Process Data"):
        pass
        bitwiseFlag ^= (1 << 4) | (1 << 11) # Ends stage 1 | Start stage 2

elif bitwiseFlag & (1 << 11): # Stage 2
    pass

elif bitwiseFlag & (1 << 12): # Stage 3
    pass

    

print(f"Import: {bin(bitwiseFlag)}")
