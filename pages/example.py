import csv
import io
from html import escape

import streamlit as st


st.set_page_config(
    page_title="Team Bravo | Classroom Tool Catalogue",
    page_icon="B",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #202b28;
        --muted: #687570;
        --paper: #f6f7f1;
        --line: #dce2d9;
        --green: #176b58;
        --coral: #db735e;
    }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stSidebar"] { background: #e9eee6; }
    .block-container { max-width: 1180px; padding-top: 2.2rem; }
    .eyebrow {
        color: var(--green); font-size: 0.76rem; font-weight: 750;
        letter-spacing: 0.12em; text-transform: uppercase;
    }
    .hero-title {
        color: var(--ink); font-family: Georgia, 'Times New Roman', serif;
        font-size: 2.65rem; line-height: 1.05; margin: 0.35rem 0 0.65rem;
    }
    .hero-copy { color: var(--muted); font-size: 1.02rem; max-width: 690px; }
    .tool-card {
        background: #fffefa; border: 1px solid var(--line); border-top: 4px solid var(--green);
        border-radius: 6px; padding: 1.1rem 1.15rem 1.2rem; min-height: 245px;
        margin-bottom: 1rem;
    }
    .tool-kind {
        color: var(--green); font-size: 0.72rem; font-weight: 750;
        letter-spacing: 0.1em; text-transform: uppercase;
    }
    .tool-number { color: var(--coral); }
    .tool-name {
        color: var(--ink); font-family: Georgia, 'Times New Roman', serif;
        font-size: 1.35rem; line-height: 1.15; margin: 0.5rem 0;
    }
    .tool-copy { color: var(--muted); font-size: 0.92rem; line-height: 1.5; }
    .tool-label { color: var(--ink); font-size: 0.78rem; font-weight: 700; margin-top: 0.85rem; }
    div[data-testid="stMetric"] {
        background: #fffefa; border: 1px solid var(--line); border-radius: 6px; padding: 0.8rem 1rem;
    }
    h2, h3 { color: var(--ink); }
    </style>
    """,
    unsafe_allow_html=True,
)

TOOL_CATEGORIES = {
    "01": "Attendance",
    "02": "Feedback",
    "03": "Engagement",
    "04": "Follow-up",
    "05": "Insights",
}

DEFAULT_TOOLS = [
    # Records after-class attendance from a rotating QR code and timestamp.
    {
        "No.": "01",
        "Tool": "After-Class QR Check-in",
        "Type": TOOL_CATEGORIES["01"],
        "What it does": "Students scan a rotating QR code after class; the instructor gets a timestamped attendance list.",
        "Best for": "Fast, low-friction attendance that is easy to review later.",
        "Build idea": "Add a short-lived code, duplicate-scan prevention, and a manual correction queue.",
    },
    # Collects a quick student confidence or comprehension response after class.
    {
        "No.": "02",
        "Tool": "Class Pulse",
        "Type": TOOL_CATEGORIES["02"],
        "What it does": "Collects a one-question confidence or comprehension check as students leave.",
        "Best for": "Spotting topics that need a quick follow-up before the next class.",
        "Build idea": "Show an anonymous response mix and let the instructor add a follow-up prompt.",
    },
    # Tracks student contributions to help instructors balance class discussion.
    {
        "No.": "03",
        "Tool": "Participation Map",
        "Type": TOOL_CATEGORIES["03"],
        "What it does": "Gives the instructor a lightweight way to note who contributed and how.",
        "Best for": "Balancing discussion and noticing students who may need an invitation in.",
        "Build idea": "Use contribution tags such as question, example, peer help, or presentation.",
    },
    # Organizes missed class materials and next steps for absent students.
    {
        "No.": "04",
        "Tool": "Catch-up Queue",
        "Type": TOOL_CATEGORIES["04"],
        "What it does": "Turns absences into a small, trackable list of materials and next steps.",
        "Best for": "Helping absent students rejoin without searching through scattered messages.",
        "Build idea": "Pair each missed session with notes, a task, an owner, and a completion state.",
    },
    # Combines attendance and feedback to show patterns across class sessions.
    {
        "No.": "05",
        "Tool": "Session Signal Board",
        "Type": TOOL_CATEGORIES["05"],
        "What it does": "Combines attendance and quick feedback into a simple view of class patterns.",
        "Best for": "Seeing whether participation or confidence shifts across sessions.",
        "Build idea": "Compare weekly totals and flag changes worth discussing with the class.",
    },
]

if "catalogue" not in st.session_state:
    st.session_state.catalogue = [tool.copy() for tool in DEFAULT_TOOLS]


def save_catalogue_edits():
    edited = st.session_state.get("tool_catalogue_editor")
    if edited is None:
        return

    if hasattr(edited, "to_dict"):
        edited = edited.to_dict(orient="records")
    st.session_state.catalogue = [tool.copy() for tool in edited]


catalogue = st.session_state.catalogue
tool_types = ["All tool types", *sorted({tool["Type"] for tool in catalogue})]

with st.sidebar:
    st.markdown('<div class="eyebrow">Team Bravo / Lab</div>', unsafe_allow_html=True)
    st.title("Tool catalogue")
    st.caption("A working shelf of small ideas for a better after-class experience.")
    search = st.text_input("Find a tool", placeholder="Try attendance or feedback")
    selected_type = st.selectbox("Tool type", tool_types)
    st.divider()
    st.caption("Edit any field in the catalogue below. Changes stay in this session.")

st.markdown('<div class="eyebrow">Classroom tools / 01—05</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Small tools. Better class follow-through.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-copy">Five practical prototypes for attendance, engagement, feedback, and the moments after class. Browse the ideas, then make the catalogue your team\'s own.</div>',
    unsafe_allow_html=True,
)
st.write("")

metric_columns = st.columns(3)
metric_columns[0].metric("Tools in the catalogue", len(catalogue))
metric_columns[1].metric("Tool types", len({tool["Type"] for tool in catalogue}))
metric_columns[2].metric("Starting point", "After-class QR")

query = search.strip().casefold()
visible_tools = []
for tool in catalogue:
    if selected_type != "All tool types" and tool["Type"] != selected_type:
        continue
    if query and not any(query in str(value).casefold() for value in tool.values()):
        continue
    visible_tools.append(tool)

st.subheader("Browse the ideas")
st.caption(f"Showing {len(visible_tools)} of {len(catalogue)} tools")
if not visible_tools:
    st.info("No tools match those filters. Try another search or tool type.")
else:
    for start in range(0, len(visible_tools), 2):
        columns = st.columns(2, gap="medium")
        for column, tool in zip(columns, visible_tools[start : start + 2]):
            with column:
                display_tool = {name: escape(str(value)) for name, value in tool.items()}
                st.markdown(
                    f"""
                    <div class="tool-card">
                        <div class="tool-kind"><span class="tool-number">{display_tool['No.']}</span> / {display_tool['Type']}</div>
                        <div class="tool-name">{display_tool['Tool']}</div>
                        <div class="tool-copy">{display_tool['What it does']}</div>
                        <div class="tool-label">USE</div>
                        <div class="tool-copy">{display_tool['Best for']}</div>
                        <div class="tool-label">BUILD NEXT</div>
                        <div class="tool-copy">{display_tool['Build idea']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.divider()
st.subheader("Edit the catalogue")
st.caption("Select a cell to change a name, type, description, use case, or next build idea.")
edited_catalogue = st.data_editor(
    catalogue,
    hide_index=True,
    num_rows="fixed",
    use_container_width=True,
    column_config={
        "No.": st.column_config.TextColumn("No.", disabled=True),
        "Tool": st.column_config.TextColumn("Tool", required=True),
        "Type": st.column_config.TextColumn("Type", required=True),
        "What it does": st.column_config.TextColumn("What it does"),
        "Best for": st.column_config.TextColumn("Best for"),
        "Build idea": st.column_config.TextColumn("Build idea"),
    },
    key="tool_catalogue_editor",
    on_change=save_catalogue_edits,
)
if hasattr(edited_catalogue, "to_dict"):
    edited_catalogue = edited_catalogue.to_dict(orient="records")
st.session_state.catalogue = [tool.copy() for tool in edited_catalogue]

csv_file = io.StringIO(newline="")
fieldnames = ["No.", "Tool", "Type", "What it does", "Best for", "Build idea"]
writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
writer.writeheader()
writer.writerows(st.session_state.catalogue)
st.download_button(
    "Download catalogue as CSV",
    data=csv_file.getvalue(),
    file_name="team_bravo_tool_catalogue.csv",
    mime="text/csv",
)

