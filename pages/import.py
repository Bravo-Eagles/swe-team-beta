import streamlit, pandas
from src.passwords import require_login
from api import attendance_api
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
    streamlit.session_state.import_nameFormatOrder = [] # Holds format of names
    streamlit.session_state.import_dateFormatOrder = [] # Holds format of names
    streamlit.session_state.import_formatSkipper = ""
    streamlit.session_state.import_bitwiseFlag = 0
# This is no longer ordered nicely
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
# 11 = Valid formatting
# 12 = Database has classes/courses
# 13 = Seen '{'
# 14 = Format skipper active
# 15 = Format skipper end

# 20 = Stage 3
#  = User confirmed data


# Local Variable Alias
spreadsheet = streamlit.session_state.import_spreadsheet
presentString = streamlit.session_state.import_presentString
absentString = streamlit.session_state.import_absentString
dateRange: pandas.DataFrame = streamlit.session_state.import_dateRange
nameRange: pandas.DataFrame = streamlit.session_state.import_nameRange
bitwiseFlag = streamlit.session_state.import_bitwiseFlag
selectionData = streamlit.session_state.import_selectionData
nameFormatOrder = streamlit.session_state.import_nameFormatOrder 
dateFormatOrder = streamlit.session_state.import_dateFormatOrder 
formatSkipper = streamlit.session_state.import_formatSkipper


### Helper functions
# Saves local variables back into streamlit session_state
def save(): 
    streamlit.session_state.import_spreadsheet = spreadsheet
    streamlit.session_state.import_presentString = presentString
    streamlit.session_state.import_absentString = absentString
    streamlit.session_state.import_dateRange = dateRange
    streamlit.session_state.import_nameRange = nameRange
    streamlit.session_state.import_bitwiseFlag = bitwiseFlag
    streamlit.session_state.import_selectionData = selectionData
    streamlit.session_state.import_nameFormatOrder = nameFormatOrder
    streamlit.session_state.import_dateFormatOrder = dateFormatOrder
    streamlit.session_state.import_formatSkipper = formatSkipper
# Runs save, then reloads the page
def update(): 
    save()
    streamlit.rerun()
# Moves bitwiseFlag/state back based on current stage/state
def back():
    global bitwiseFlag
    if bitwiseFlag & (1 << 4): # Stage 1 -> Stage 0
        bitwiseFlag = 0
        del (streamlit.session_state.import_dataframe, streamlit.session_state.import_spreadsheet,
             streamlit.session_state.import_dateRange, streamlit.session_state.import_nameRange, 
             streamlit.session_state.import_presentString, streamlit.session_state.import_absentString)
    if bitwiseFlag & (1 << 10): # Stage 2 -> Stage 1
        del (streamlit.session_state.import_nameFormatOrder, streamlit.session_state.import_dateFormatOrder)
        bitwiseFlag &= ~((1<<5)|(1<<6)|(1<<7)|(1<<8)|(1<<9)|(1<<10)) # Pos 5-10 are set to 0, 
        bitwiseFlag |= (1 << 4)
    update()
# Captures selection from import_dataframe
def captureDataSelection(): 
    global selectionData
    selectionData = streamlit.session_state.import_dataframe
    update()
# Checks if cells are in a the same column or row
#
# Args:
#     cells (pandas.Series): Cells to check
#
# Returns:
#     bool: Were all cells found in the same row or column?
def checkCellsInSame(cells):
    if cells.dropna().empty:
        return False
    previous_cell = cells[1]
    first_run:bool = True
    isRow:bool = False
    isColumn:bool = False
    for cell in cells:
        if first_run:
            if cell[0] == previous_cell[0]:
                isRow = True
            elif cell[1] == previous_cell[1]:
                isColumn = True
        if isRow and cell[0] != previous_cell[0] or isColumn and cell[1] != previous_cell[1]:
            return False
    return True


### Real code (Congrats! You survived)
if not (bitwiseFlag & 1): # If file hasn't been uploaded
    streamlit.header("Test file upload")
    file = streamlit.file_uploader("Select file", accept_multiple_files=False, type=["csv", "ods", "xlsx"])
    classlist = attendance_api.list_class_offerings()
    if classlist:
        bitwiseFlag |= (1<<12)
        # Grabbing teaching_id from classlist
        classlist_by_id = {c["teaching_id"]: f'{c["class_name"]} ({c["semester"]} {c["year"]})' for c in classlist}
        streamlit.session_state.import_classId = streamlit.selectbox("Class", options=list(classlist_by_id), format_func=lambda format:classlist_by_id[format])
    else:
        streamlit.warning("No classes available. Please create a class first before importing attendance records")

    if streamlit.button("Upload"):
        if file == None:
            streamlit.error("Error: No upload")
            bitwiseFlag &= ~(1 | 2 | 4 | 8) # Sets 0,1,2,3 to 0
        elif not bitwiseFlag & (1<<12):
            streamlit.error("Error: No classes available")
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


elif bitwiseFlag & (1 << 4): # Stage 1 - Select data from spreadsheet and put it in usable format
    inputDefaultText = "Select values from the spreadsheet above"
    streamlit.write("Now we need your help! Select cells in the spreadsheet. When the selection matches an option below, hit Set to lock it in.")
    streamlit.dataframe(spreadsheet, key="import_dataframe", on_select=captureDataSelection, selection_mode=["multi-cell", "multi-column", "multi-row"])

    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        # If dateRange has been set, display it 
        streamlit.session_state["dateRangeBox"] = dateRange.to_string() if bitwiseFlag & (1 << 5) else inputDefaultText
        dateRangeBox = streamlit.text_input(label="Provide the range of cells that contain the date", key="dateRangeBox", disabled=True)
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
        # If nameRange has been set, display it 
        streamlit.session_state["nameRangeBox"] = nameRange.to_string() if bitwiseFlag & (1 << 6) else inputDefaultText
        nameRangeBox = streamlit.text_input(label="Provide the range of cells that contain student's names", key="nameRangeBox", disabled=True)
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
        # If presentString has been set, display it
        streamlit.session_state["presentStringBox"] = presentString.to_string() if bitwiseFlag & (1 << 7) else inputDefaultText
        presentStringBox = streamlit.text_input(label="Text that marks students as present (Expects one cell)", key="presentStringBox", disabled=True)
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
        # If absentString has been set, display it 
        streamlit.session_state["absentStringBox"] = absentString.to_string() if bitwiseFlag & (1 << 8) else inputDefaultText
        absentStringBox = streamlit.text_input(label="Text that marks students as absent (Expects one cell)", key="absentStringBox", disabled=True)
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

    ## Error for bad data combinations
    if not (bitwiseFlag & ((1<<5)|(1<<6)|(1<<7)|(1<<8))): # If no 5-8 error
        streamlit.error("Error: No selection")
    elif (bitwiseFlag & ((1<<7)|(1<<8)) and not bitwiseFlag & ((1<<5)|(1<<6))): # No 5 and 6 but 7 or 8, error
        streamlit.error("Error: No name or date have been provided")
    else:
        bitwiseFlag |= (1<<9) # A valid combination

    ## Error for invalid data entry
    # Ranges will need to be expanded, but at this point I'm not updating to it's finished
    # Otherwise I'll be doing this forever; so don't break it
    if (bitwiseFlag & (1<<5) or bitwiseFlag & (1<<6)):
        if (("cells" in dateRange.columns and not dateRange["cells"].dropna().empty and not checkCellsInSame(dateRange["cells"])) or
            ("cells" in nameRange.columns and not nameRange["cells"].dropna().empty and not checkCellsInSame(nameRange["cells"]))
        ):
            streamlit.error("Error: Selected cells are not in the same row or column")
            bitwiseFlag &= ~(1<<9)
        if (("cells" in dateRange.columns and not dateRange["cells"].dropna().empty and (not dateRange["rows"].dropna().empty or not dateRange["columns"].dropna().empty)) or
            ("cells" in dateRange.columns and not nameRange["cells"].dropna().empty and (not nameRange["rows"].dropna().empty or not nameRange["columns"].dropna().empty))
        ): 
            streamlit.error("Error: Multiple cells and rows or columns have been selected at the same time")
            bitwiseFlag &= ~(1<<9)
    if (bitwiseFlag & (1<<5)) and (not dateRange["cells"].dropna().empty and len(dateRange) == 1):
            streamlit.error("Error: Date Range is a single cell when it should be a range")
            bitwiseFlag &= ~(1<<9)
    if (bitwiseFlag & (1<<6) and (not nameRange["cells"].dropna().empty and len(nameRange) == 1)):
            streamlit.error("Error: Name Range is a single cell when it should be a range")
            bitwiseFlag &= ~(1<<9) 
    if (bitwiseFlag & (1<<7) and ((not presentString["rows"].dropna().empty or not presentString["columns"].dropna().empty) or len(presentString) != 1)):
        streamlit.error("Error: The text that marks the students as present is a range when it should be a cell")
        bitwiseFlag &= ~(1<<9)
    if (bitwiseFlag & (1<<8) and ((not absentString["rows"].dropna().empty or not absentString["columns"].dropna().empty) or len(absentString) != 1)):
        streamlit.error("Error: The text that marks the students as absent is a range when it should be a cell")
        bitwiseFlag &= ~(1<<9)
    save() # This save might be unnecessary, but right now it works

elif bitwiseFlag & (1 << 10): # Stage 2 - Figure out formatting
    nameFormatOrder = [] # Clears list
    dateFormatOrder = [] # Clears list
    bitwiseFlag |= (1<<11) # Sets valid formatting to true, until proven otherwise 
    # Read by row, sorry I can add column support later
    # Add actual support for absentString
    streamlit.dataframe(spreadsheet)
    streamlit.write("Alright, now we have the data organized. But we aren't quite sure how to read it. Complete the prompts below to import your data.")
    
    nameFormat = streamlit.text_input("Name formating")
    streamlit.write("{f} - first name, {m} - middle name, {l} - last name")
    dateFormat = streamlit.text_input("Date formating")
    streamlit.write("EX:MM-DD-YYYY")

    # parse name formatting
    for namePos, char in enumerate(nameFormat):
        char = char.lower()
        if char == '{':
            if bitwiseFlag & (1<<13):
                streamlit.error(f"Error: Invalid character \'{{\' in name format at position {namePos}")
                bitwiseFlag &= ~(1<<11)
            else:
                bitwiseFlag |= (1<<13)|(1<<15)
        elif char == '}':
            if bitwiseFlag & (1<<13):
                bitwiseFlag &= ~(1<<13)
            else:
                streamlit.error(f"Error: Invalid character \'}}\' in name format at position {namePos}")
                bitwiseFlag &= ~(1<<11)
        elif char == 'f' or char == 'm' or char == 'l':
            if bitwiseFlag & (1<<13):
                if char == 'f':
                    nameFormatOrder.append(0)
                elif char == 'm':
                    nameFormatOrder.append(1)
                elif char == 'l':
                    nameFormatOrder.append(2)
            else:
                streamlit.error(f"Error: Name format missing \'{{\' before {char} at postion {namePos}")
                bitwiseFlag &= ~(1<<11)
        else:
            if bitwiseFlag & (1<<13):
                streamlit.error(f"Error: Missing character \'}}\' in name format at position {namePos}")
                bitwiseFlag &= ~(1<<11)
            else:
                bitwiseFlag |= (1<<14) 
                formatSkipper = f"{formatSkipper}{char}"
        if bitwiseFlag & (1<<15) and formatSkipper != "":
            nameFormatOrder.append(formatSkipper)
            formatSkipper = ""
            bitwiseFlag &= ~((1<<14)|(1<<15))
        for datePos, char in enumerate(dateFormat):
            char = char.upper()
            if char == '-':
                pass
            elif char == 'M':
                pass
            elif char == 'Y':
                pass
            elif char == 'D':
                pass
            else:
                streamlit.error(f"Error: Date formating invalid character \'{char}\' at position {datePos}")
    save()

    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if streamlit.button("Back"):
            back()
        if streamlit.button("Process Data") and bitwiseFlag & (1<<11):
            bitwiseFlag ^= (1 << 10) | (1 << 20) # Ends stage 2 | Start stage 3
            update()

elif bitwiseFlag & (1 << 20): # Stage 3 - Put the stuff in the database
    streamlit.progress(1)
    for entry in spreadsheet:
        streamlit.write(entry)
    if streamlit.button("Import more?"):
        back()

print(f"Import: {bin(bitwiseFlag)}")
