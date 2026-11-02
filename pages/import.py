import streamlit, pandas
from src.passwords import require_login
#require Login
require_login()

### Notes & other information
# Stages of processing user file
    # Stage 1 - Getting data for processing
        # Retrieve the character(s) that marks a student as present
        # Retrieve the character(s) that marks a student as absent
        # Get date location(s)
        # Get name location(s)
    # Stage 2 - Display data for user to confirm/modify
        # Allow user to change/enter additional info
        # Allow user to specify how data is stored
            # Ex: How is a name stored? What order? Is there a delimiter? Multiple rows?
    # Stage 3 - Load into database
# Actions should always be reversable 


# Local Variables (Accessable across entire file)
# Streamlit forgets on each pass of the script unless you use st.session_state
if "import_bitwiseFlag" not in streamlit.session_state:
    streamlit.session_state.import_spreadsheet = ""
    streamlit.session_state.import_presentString = "" # Character(s) that marks student as present
    streamlit.session_state.import_absentString = "" # Character(s) that marks student as absent
    streamlit.session_state.import_dateRange = "" # Stores the cell range that contains dates
    streamlit.session_state.import_nameRange = "" # Stores the cell range that contains names
    streamlit.session_state.import_selectionData = "" # A tmp holder for dataframe selection
    streamlit.session_state.import_bitwiseFlag = 0
# 0 = Whether a file has been uploaded
# 1 = Import is XLSX
# 2 = Import is CSV
# 3 = Import is ODS
# 4 = Stage 1 
# 5 = Date(s) Location exists
# 6 = Name(s) Location exists
# 7 = Present String exists
# 8 = Absent String exists
# 9 = Stage 2
#  = User confirmed data


# Local Variable Alias
spreadsheet = streamlit.session_state.import_spreadsheet
presentString = streamlit.session_state.import_presentString
absentString = streamlit.session_state.import_absentString
dateRange = streamlit.session_state.import_dateRange
nameRange = streamlit.session_state.import_nameRange
bitwiseFlag = streamlit.session_state.import_bitwiseFlag
selectionData = streamlit.session_state.import_selectionData


### Helper functions
def save(): # Saves alias back to streamlit variables
    streamlit.session_state.import_spreadsheet = spreadsheet
    streamlit.session_state.import_presentString = presentString
    streamlit.session_state.import_absentString = absentString
    streamlit.session_state.import_dateRange = dateRange
    streamlit.session_state.import_nameRange = nameRange
    streamlit.session_state.import_bitwiseFlag = bitwiseFlag
    streamlit.session_state.import_selectionData = selectionData
def update(): # Save and rerun/reload page
    save()
    streamlit.rerun()
def back():
    global bitwiseFlag
    if bitwiseFlag & (1 << 4):
        bitwiseFlag = 0
    update()
def captureDataSelection(): 
    global selectionData
    selectionData = streamlit.session_state.import_dataframe
    update()

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
            update()


elif bitwiseFlag & (1 << 4): # Stage 1
    inputDefaultText = "Select values from the spreadsheet above"
    streamlit.write("Alright! Now we need your help! Select cells in the spreadsheet. When the selection matches an option below hit Set to lock it in.")
    streamlit.dataframe(spreadsheet, key="import_dataframe", on_select=captureDataSelection, selection_mode=["multi-cell", "multi-column", "multi-row"])

    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        dateRangeBoxText = "Provide the range of cells that contain the date"
        if bitwiseFlag & (1 << 5): # If dateRange has been set, display it 
            dateRangeBoxText = dateRange
        dateRangeBox = streamlit.text_input(value=dateRangeBoxText, label=inputDefaultText, disabled=True)
        if streamlit.button("Set", key="setDatesButton"): # Set dateRange
            dateRange = selectionData 
            bitwiseFlag |= (1 << 5) 
            update()
        if streamlit.button("Clear", key='clearDatesButton'): # Clear dateRange
            dateRange = ""
            bitwiseFlag &= ~(1 << 5)
            update()
    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        nameRangeBoxText = "Provide the range of cells that contain student's names"
        if bitwiseFlag & (1 << 6): # If dateRange has been set, display it 
            nameRangeBoxText = nameRange
        nameRangeBox = streamlit.text_input(value=nameRangeBoxText, label=inputDefaultText, disabled=True)
        if streamlit.button("Set", key="setNamesButton"):
            nameRange = selectionData
            bitwiseFlag |= (1 << 6) 
            update()
        if streamlit.button("Clear", key='clearNamesButton'):
            nameRange = ""
            bitwiseFlag &= ~(1 << 6)
            update()
    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        presentStringBoxText = "Text that marks students as present (Expects one cell)"
        if bitwiseFlag & (1 << 7): # If dateRange has been set, display it 
            presentStringBoxText = presentString
        presentStringBox = streamlit.text_input(value=presentStringBoxText, label=inputDefaultText, disabled=True)
        if streamlit.button("Set", key="setPresentButton"):
            presentString = selectionData
            bitwiseFlag |= (1 << 7) 
            update()
        if streamlit.button("Clear", key='clearPresentButton'):
            presentString = ""
            bitwiseFlag &= ~(1 << 7)
            update()
    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        absentStringBoxText = "Text that marks students as absent (Expects one cell)"
        if bitwiseFlag & (1 << 8): # If dateRange has been set, display it 
            absentStringBoxText = absentString
        absentStringBox = streamlit.text_input(value=absentStringBoxText, label=inputDefaultText, disabled=True)
        if streamlit.button("Set", key="setAbsentButton"):
            absentString = selectionData
            bitwiseFlag |= (1 << 8) 
            update()
        if streamlit.button("Clear", key='clearAbsentButton'):
            absentString = ""
            bitwiseFlag &= ~(1 << 8)
            update()

    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if streamlit.button("Back"):
            back()
        if streamlit.button("Process Data"):
            bitwiseFlag ^= (1 << 4) | (1 << 9) # Ends stage 1 | Start stage 2
            update()


elif bitwiseFlag & (1 << 9): # Stage 2
    streamlit.write(absentString)
    streamlit.write(presentString)
    streamlit.write(nameRange)
    streamlit.write(dateRange)

elif bitwiseFlag & (1 << 12): # Stage 3
    pass

    

print(f"Import: {bin(bitwiseFlag)}")
