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

## AI summaries (issue #75)

Students use **Exit Slip** to select an enrolled class meeting and submit a
response. Responses are saved in SQLite and a repeat submission updates the
student's response for that meeting.

Teachers open **Professor Dashboard → View Class → Scheduled Sessions**, select
a meeting, and click **Generate AI summary**. Opening the page, changing meetings,
and submitting exit slips never trigger an AI request. The last requested summary
stays in the teacher's browser session; changed submissions are flagged until the
teacher requests another summary. Only the teacher assigned to the meeting can
read its responses. Students cannot view other students' submissions.

Set `AI_API_KEY` in the server environment before starting Streamlit. Optionally
set `AI_API_URL` to an OpenAI-compatible Responses API base URL (default:
`https://rocky.cs.kent.edu/v1`). The existing `AIRequest` integration selects the
first model returned by that server. Never commit API keys. Provider/key settings
management is tracked separately in issue #74.

Only questions and response text are sent for summarization. Account IDs,
student profile names, and timestamps are not added to the prompt (response text
may itself contain personal information). The AI summary covers learning themes, confusion,
and suggested follow-up. Requests time out and errors can be retried manually;
no real student submissions are sent during automated tests.

You can add required packages with 
`uv add (Package)`
