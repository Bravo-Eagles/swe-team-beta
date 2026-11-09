import streamlit, pandas
from api import attendance_api
from src.passwords import require_login
from src.sidebar import sidebar
from src.database import get_connection 
#require Login
require_login()
sidebar()

### Notes & other information
# Stages of processing user file
    # Stage 1 - Getting data for processing
        # Retrieve the character(s) that marks a student as present
        # Retrieve the character(s) that marks a student as absent
        # Get date location(s)
        # Get name location(s)
    # Stage 2 - Display data for user to confirm/modify
        # Allow user to specify how data is stored
            # Ex: How is a name stored? What order? Is there a delimiter? Multiple rows?
    # Stage 3 - Load into database
# Actions should always be reversable 

### TODO
# Add time as importable option
# Error catching for stage 3 needs improved
# Stage 3 has no way to deal with multiple matches, so it just picks one. FIX THIS
# Stage 3 add better defaults for handling date
# Stage 3 add failsafe for database connection
# Fix order of bitwiseFlag
# Make the initialization of the session_state able to be activated by flag. So you can reset for next import

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
    streamlit.session_state.import_classId = 0
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
# 16 = Stage 3
# 20 = Import to database successful
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
classId = streamlit.session_state.import_classId


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
    streamlit.session_state.import_classId = classId
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
    elif bitwiseFlag & (1 << 10): # Stage 2 -> Stage 1
        del (streamlit.session_state.import_nameFormatOrder, streamlit.session_state.import_dateFormatOrder)
        bitwiseFlag &= ~((1<<5)|(1<<6)|(1<<7)|(1<<8)|(1<<9)|(1<<10)) # Pos 5-10 are set to 0, 
        bitwiseFlag |= (1 << 4)
    elif bitwiseFlag & (1<<16): # Stage 3 -> Stage 2
        if bitwiseFlag & (1<<20):
            bitwiseFlag = 0    
            nameFormatOrder = [] # Clears list
            dateFormatOrder = [] # Clears list
            update()
        bitwiseFlag &= ~((1<<16)|(1<<20))
        bitwiseFlag |= (1 << 10)
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
        if file is None:
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
    # parse date formatting
    formatSkipper = ""
    bitwiseFlag &= ~((1<<14)|(1<<15))
    for datePos, char in enumerate(dateFormat):
        char = char.upper()
        if char == 'M':
            bitwiseFlag |= (1<<15)
            dateFormatOrder.append(0)
        elif char == 'Y':
            bitwiseFlag |= (1<<15)
            dateFormatOrder.append(1)
        elif char == 'D':
            bitwiseFlag |= (1<<15)
            dateFormatOrder.append(2)
        else:
            bitwiseFlag |= (1<<14) 
            formatSkipper = f"{formatSkipper}{char}"
        if bitwiseFlag & (1<<15) and formatSkipper != "":
            dateFormatOrder.append(formatSkipper)
            formatSkipper = ""
            bitwiseFlag &= ~((1<<14)|(1<<15))

    save()

    with streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="bottom"):
        if streamlit.button("Back"):
            back()
        if streamlit.button("Process Data") and bitwiseFlag & (1<<11):
            bitwiseFlag ^= (1 << 10) | (1 << 16) # Ends stage 2 | Start stage 3
            update()

elif bitwiseFlag & (1 << 16): # Stage 3 - Put the stuff in the database
    streamlit.progress(1)
    conn = get_connection()
    try:
            formatSkipper = ""
            for rowPos, entry in spreadsheet.iterrows():
                # Import name. If name already exists just get its id
                name: str = str(entry[nameRange["columns"][0]])
                first_name: str|None = None
                middle_name: str|None = None
                last_name: str|None = None
                student_id = -1
                for thing in nameFormatOrder:
                    tmp = name.split()[0]
                    if thing == 0 or thing == 1 or thing == 2:
                        if thing == 0:
                            if first_name is None:
                                first_name = tmp
                            else:
                                first_name = f"{first_name} {tmp}"
                        elif thing == 1:
                            if middle_name is None:
                                middle_name = tmp
                            else:
                                middle_name = f"{middle_name} {tmp}"
                        elif thing == 2:
                            if last_name is None:
                                last_name = tmp
                            else:
                                last_name = f"{last_name} {tmp}"
                        name = name.replace(tmp, "", 1)
                    else:
                        name = name.replace(thing, "", 1)
                if first_name is None or last_name is None:    
                    formatSkipper = f"Error: For a student to exist in the database they must have both a first and last name. One is missing or malformed. Please try again.  \nFirst: {first_name}  \nLast:{last_name}"
                    raise Exception("First and Last name are required")
                print(1)
                if middle_name is None:
                    student_id = conn.execute(
                        """
                        SELECT ID FROM student 
                        WHERE first_name = ? AND last_name = ?
                        """,
                        (first_name, last_name)
                    )
                else:
                    student_id = conn.execute(
                        """
                        SELECT ID FROM student 
                        WHERE first_name = ? AND middle_name = ? AND last_name = ?
                        """,
                        (first_name, middle_name, last_name)
                    ) 

                student_id = student_id.fetchone()
                print(2)
                if student_id is None:
                    student_id = conn.execute(
                             """
                             INSERT INTO student (first_name, middle_name, last_name, active)
                             VALUES (?, ?, ?, ?)
                             """,
                             (first_name, middle_name, last_name, 0)
                    )  
                    student_id = student_id.lastrowid
                else:
                    student_id = student_id["id"]
                # Enrolls the student if not already enrolled
                enrollment_status = conn.execute(
                    """
                    SELECT * FROM enrolled 
                    WHERE teaching_id = ? AND student_id = ?
                    """,
                    (classId, student_id)
                ) 
                enrollment_status = enrollment_status.fetchone()
                if enrollment_status is None:
                    enrollment_status = conn.execute(
                            """
                            INSERT INTO enrolled (teaching_id, student_id)
                            VALUES (?, ?)
                            """,
                            (classId, student_id)
                    )  
                    enrollment_status = enrollment_status.lastrowid
                print(3)
                # Get the date format
                date: str = str(entry[dateRange["columns"][0]])
                date_month = None
                date_year = None
                date_day = None
                for thing in dateFormatOrder:
                    tmp = date[0]
                    if thing == 0 or thing == 1 or thing == 2:
                        if thing == 0: # Month
                            if date_month is None:
                                date_month = int(tmp)
                            else:
                                date_month = (date_month*10)+int(tmp)
                        elif thing == 1: # Year
                            if date_year is None:
                                date_year = int(tmp)
                            else:
                                date_year = (date_year*10)+int(tmp)
                        elif thing == 2: # Day
                            if date_day is None:
                                date_day = int(tmp)
                            else:
                                date_day = (date_day*10)+int(tmp)
                        date = date.replace(tmp, "", 1)
                    else:
                        date = date.replace(thing, "", 1)
                if date_day is None or date_month is None or date_year is None:    
                    formatSkipper = f"Error: For a class to exist in the database they must have an exact date. At least one is missing or malformed. Please try again.  \nMonth: {date_month}  \nDay:{date_day}  \nYear: {date_year}"
                    raise Exception("A full date is required")
                if date_year < 100:
                    date_year = 2000+date_year
                # time 00:00:00
                # date YYYY-MM-DD
                # fstring formater :02d - Allows for padding zeros. Look for more of these later
                print(4)
                scheduledClass = conn.execute(
                    """
                    SELECT * FROM scheduled 
                    WHERE teaching_id = ? AND date = ? AND start_time = ?
                    """,
                    (classId, f"{date_year}-{date_month:02d}-{date_day:02d}", "00:00:00")
                ) 
                scheduledClass = scheduledClass.fetchone()
                if scheduledClass is None:
                    scheduledClass = conn.execute(
                            """
                            INSERT INTO scheduled (teaching_id, date, start_time)
                            VALUES (?, ?, ?)
                            """,
                            (classId, f"{date_year}-{date_month:02d}-{date_day:02d}", "00:00:00")
                    )  
                    scheduledClass = scheduledClass.lastrowid
                else:
                    scheduledClass = scheduledClass["id"]
                attended = spreadsheet[presentString["cells"][0][1]][presentString["cells"][0][0]]
                attended = 1 if (entry[presentString["cells"][0][1]] == attended) else 0
                attendanceRecord = conn.execute(
                    """
                    SELECT * FROM attendance 
                    WHERE scheduled_id = ? AND student_id = ? AND check_in_time = ? AND is_deleted = ?
                    """,
                    (scheduledClass, student_id, "00:00:00", attended)
                ) 
                attendanceRecord = attendanceRecord.fetchone()
                if attendanceRecord is None:
                    attendanceRecord = conn.execute(
                            """
                            INSERT INTO attendance (scheduled_id, student_id, check_in_time, is_deleted)
                            VALUES (?, ?, ?, ?)
                            """,
                            (scheduledClass, student_id, "00:00:00", attended)
                    )  
                    attendanceRecord = attendanceRecord.lastrowid

                
                conn.commit()
                bitwiseFlag |= (1<<20) # Import worked
    except Exception as error:
        if formatSkipper == "":
            streamlit.error("Unknown error. Please contact developers. Issues can be sent to https://github.com/Bravo-Eagles/swe-team-beta/issues  \n Just describe the problem and provide the error data from below.")
            streamlit.error(f"{type(error)}  \n{error}  \n{bitwiseFlag}")
        else:
            streamlit.error(formatSkipper)
        if streamlit.button("Back"):
            back()
    else:
        if streamlit.button("Import more?"):
            back()
        streamlit.success("Import complete")
    finally:
        conn.close()
    save()
    
# Rather than "import more" using back() it should probably handle things itself or be reliant on an error state. I want there to be a back button if an error occurs during the writing to the database

print(f"Import: {bin(bitwiseFlag)}")
