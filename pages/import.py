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
    streamlit.session_state.import_spreadsheet = pandas.DataFrame()
    streamlit.session_state.import_presentString = pandas.DataFrame() # Character(s) that marks student as present
    streamlit.session_state.import_absentString = pandas.DataFrame() # Character(s) that marks student as absent
    streamlit.session_state.import_dateRange = pandas.DataFrame() # Stores the cell range that contains dates
    streamlit.session_state.import_nameRange = pandas.DataFrame() # Stores the cell range that contains names
    streamlit.session_state.import_selectionData = pandas.DataFrame() # A tmp holder for dataframe selection
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
# 9 = Valid combination of 5-8
# 10 = Stage 2
#  = User confirmed data


# Local Variable Alias
spreadsheet = streamlit.session_state.import_spreadsheet
presentString = streamlit.session_state.import_presentString
absentString = streamlit.session_state.import_absentString
dateRange: pandas.DataFrame = streamlit.session_state.import_dateRange
nameRange: pandas.DataFrame = streamlit.session_state.import_nameRange
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
    if bitwiseFlag & (1 << 4): # Stage 1 -> Stage 0
        bitwiseFlag = 0
        del (streamlit.session_state.import_dataframe, streamlit.session_state.import_spreadsheet,
             streamlit.session_state.import_dateRange, streamlit.session_state.import_nameRange, 
             streamlit.session_state.import_presentString, streamlit.session_state.import_absentString)
    if bitwiseFlag & (1 << 10): # Stage 2 -> Stage 1
        bitwiseFlag &= ~((1<<5)|(1<<6)|(1<<7)|(1<<8)|(1<<9)|(1<<10)) # Pos 5-10 are set to 0, 
        bitwiseFlag |= (1 << 4)
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
            streamlit.error("Error: No upload")
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
    streamlit.write("Now we need your help! Select cells in the spreadsheet. When the selection matches an option below, hit Set to lock it in.")
    streamlit.dataframe(spreadsheet, key="import_dataframe", on_select=captureDataSelection, selection_mode=["multi-cell", "multi-column", "multi-row"])

    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if bitwiseFlag & (1 << 5): # If dateRange has been set, display it 
            streamlit.session_state["dateRangeBox"] = dateRange.to_string()
        else:
            streamlit.session_state["dateRangeBox"] = "Provide the range of cells that contain the date"
        dateRangeBox = streamlit.text_input(label=inputDefaultText, key="dateRangeBox", disabled=True)
        if streamlit.button("Set", key="setDatesButton"): # Set dateRange
            dateRange = pandas.DataFrame({
                "rows": pandas.Series(selectionData.selection["rows"]),
                "columns": pandas.Series(selectionData.selection["columns"]),
                "cells": pandas.Series(selectionData.selection["cells"]),
            }) 
            bitwiseFlag |= (1 << 5) 
            update()
        if streamlit.button("Clear", key='clearDatesButton'): # Clear dateRange
            dateRange = pandas.DataFrame()
            bitwiseFlag &= ~(1 << 5)
            update()
    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if bitwiseFlag & (1 << 6): # If nameRange has been set, display it 
            streamlit.session_state["nameRangeBox"] = nameRange.to_string()
        else:
            streamlit.session_state["nameRangeBox"] = "Provide the range of cells that contain student's names"
        nameRangeBox = streamlit.text_input(label=inputDefaultText, key="nameRangeBox", disabled=True)
        if streamlit.button("Set", key="setNamesButton"):
            nameRange = pandas.DataFrame({
                "rows": pandas.Series(selectionData.selection["rows"]),
                "columns": pandas.Series(selectionData.selection["columns"]),
                "cells": pandas.Series(selectionData.selection["cells"]),
            }) 
            bitwiseFlag |= (1 << 6) 
            update()
        if streamlit.button("Clear", key='clearNamesButton'):
            nameRange = pandas.DataFrame()
            bitwiseFlag &= ~(1 << 6)
            update()
    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if bitwiseFlag & (1 << 7): # If presentString has been set, display it 
            streamlit.session_state["presentStringBox"] = presentString.to_string()
        else:
            streamlit.session_state["presentStringBox"] = "Text that marks students as present (Expects one cell)"
        presentStringBox = streamlit.text_input(label=inputDefaultText, key="presentStringBox", disabled=True)
        if streamlit.button("Set", key="setPresentButton"):
            presentString = pandas.DataFrame({
                "rows": pandas.Series(selectionData.selection["rows"]),
                "columns": pandas.Series(selectionData.selection["columns"]),
                "cells": pandas.Series(selectionData.selection["cells"]),
            }) 
            bitwiseFlag |= (1 << 7) 
            update()
        if streamlit.button("Clear", key='clearPresentButton'):
            presentString = pandas.DataFrame()
            bitwiseFlag &= ~(1 << 7)
            update()
    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if bitwiseFlag & (1 << 8): # If absentString has been set, display it 
            streamlit.session_state["absentStringBox"] = absentString.to_string()
        else:
            streamlit.session_state["absentStringBox"] = "Text that marks students as absent (Expects one cell)"
        absentStringBox = streamlit.text_input(label=inputDefaultText, key="absentStringBox", disabled=True)
        if streamlit.button("Set", key="setAbsentButton"):
            absentString = pandas.DataFrame({
                "rows": pandas.Series(selectionData.selection["rows"]),
                "columns": pandas.Series(selectionData.selection["columns"]),
                "cells": pandas.Series(selectionData.selection["cells"]),
            }) 
            bitwiseFlag |= (1 << 8) 
            update()
        if streamlit.button("Clear", key='clearAbsentButton'):
            absentString = pandas.DataFrame()
            bitwiseFlag &= ~(1 << 8)
            update()

    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if streamlit.button("Back"):
            back()
        if streamlit.button("Process Data") and (bitwiseFlag & (1<<9)): 
            bitwiseFlag ^= (1 << 4) | (1 << 10) # Ends stage 1 | Start stage 2
            update()

    # Error for bad data combinations
    if not (bitwiseFlag & ((1<<5)|(1<<6)|(1<<7)|(1<<8))): # If no 5-8 error
        streamlit.error("Error: No selection")
    elif (bitwiseFlag | ((1<<7)|(1<<8)) and not bitwiseFlag & ((1<<5)|(1<<6))): # No 5 and 6 but 7 or 8, error
        streamlit.error("Error: No name or date have been provided")
    else:
        bitwiseFlag |= (1<<9) # A valid combination

    # Error for invalid data entry
    if (bitwiseFlag & (1<<5) and not dateRange["cells"].dropna().empty):
        streamlit.error("Error: Date Range is a single cell when it should be a range")
        bitwiseFlag &= ~(1<<9)
    if (bitwiseFlag & (1<<6) and not nameRange["cells"].dropna().empty):
        streamlit.error("Error: Name Range is a single cell when it should be a range")
        bitwiseFlag &= ~(1<<9)
    if (bitwiseFlag & (1<<7) and (not presentString["rows"].dropna().empty or not presentString["columns"].dropna().empty)):
        streamlit.error("Error: The text that marks the students as present is a range when it should be a cell")
        bitwiseFlag &= ~(1<<9)
    if (bitwiseFlag & (1<<8) and (not absentString["rows"].dropna().empty or not absentString["columns"].dropna().empty)):
        streamlit.error("Error: The text that marks the students as absent is a range when it should be a cell")
        bitwiseFlag &= ~(1<<9)

elif bitwiseFlag & (1 << 10): # Stage 2
    # Read by row, sorry I can add column support later
    # Add actual support for absentString
    nameRange = nameRange.selection["columns"][0]
    dateRange = dateRange.selection["columns"][0]
    presentString = presentString.selection["cells"][0]
    absentString = absentString.selection["cells"][0]
    attendanceRange = presentString[1] 
    print(spreadsheet[[nameRange, attendanceRange, dateRange]])
    streamlit.dataframe(spreadsheet[[nameRange, attendanceRange, dateRange]])
    streamlit.write("Alright, now we have the data organized. But we aren't quite sure how to read it. Complete the prompts below to import your data.")
    
    nameFormat = streamlit.text_input("Name formating")
    streamlit.write("{f} - first name, {m} - middle name, {l} - last name")
    dateFormat = streamlit.text_input("Date formating")
    streamlit.write("MM-DD-YYYY")


    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if streamlit.button("Back"):
            back()
        if streamlit.button("Process Data"):
            bitwiseFlag ^= (1 << 4) | (1 << 10) # Ends stage 2 | Start stage 3
            update()




elif bitwiseFlag & (1 << 12): # Stage 3
    pass

    

print(f"Import: {bin(bitwiseFlag)}")
