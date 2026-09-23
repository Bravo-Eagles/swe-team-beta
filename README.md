# swe-team-beta Project
Add a read me one day

# How to use UV
UV is a python package manager that makes it much simpler to manage required packages and ensure you are working in a virtual environment.
You can insall UV from https://docs.astral.sh/uv/#installation
or running
`curl -LsSf https://astral.sh/uv/install.sh | sh`
On Mac/Linux
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Once UV is installed you can run the project by doing
`uv run main.py`

You can add required packages with 
`uv add (Package)`
