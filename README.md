# swe-team-beta Project
Add a read me one day

# How to use UV
UV is a python package manager that makes it much simpler to manage required packages and ensure you are working in a virtual environment.
You can insall UV from https://docs.astral.sh/uv/#installation
or running
`curl -LsSf https://astral.sh/uv/install.sh | sh`
On Mac/Linux
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Once UV is installed, run the Streamlit app with
`uv run streamlit run main.py`

The **Attendance Data Editor** page lets you select a class offering and meeting,
then mark enrolled students present or absent and update their check-in times.
You can add a meeting date from the editor when one is not already scheduled.
Classes, teaching assignments, and student enrollments must be set up separately.

You can add required packages with 
`uv add (Package)`
