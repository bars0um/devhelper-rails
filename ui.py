from devhelpercore import process_input
import streamlit as st
from utils.ddatastore import DataStore

# Store in session state

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        .scroll-box {
        height: 220px;
        overflow-y: auto;
        overflow-x: hidden;
        white-space: pre-wrap;
        padding: .25rem .5rem;
        border: 1px solid #ddd;
        background: black;
        color: white;
        font-family: monospace, Consolas, "Courier New";
        font-size: 0.8rem;
        white-space: pre-wrap;
    }
    .scroll-box pre {
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    </style>
    """, unsafe_allow_html=True
)

# Initialize session state
for k in ("status", "system", "instr", "llm", "user", "summary", "other", "current_llm", "current_instr", "log"):
    if k not in st.session_state:
        if k == "summary":
            st.session_state.setdefault(k, {})
        else:
            st.session_state.setdefault(k, "")


def boxed(text: str) -> str:
    return f'<div class="scroll-box"><pre>{text}</pre></div>'

def dict_to_text(summary_dict: dict) -> str:
    """Convert a summary dictionary to a formatted string."""
    if not summary_dict:
        return "No summaries available"
    lines = []
    for file, desc in summary_dict.items():
        lines.append(f"{file}: {desc}")
    return "\n".join(lines)

# Function to update the file structure display
def update_file_structure():
    summary_text = dict_to_text(st.session_state.summary)
    return summary_text

# Build the UI with expanders
with st.container():
    # System and Status section
    with st.expander("System and Status", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.header("System")
            system_ph = st.empty()
            system_ph.text((st.session_state.system))
        with c2:
            st.header("Status")
            status_ph = st.empty()
            status_ph.text((st.session_state.status))
    
    # Instructions and LLM Responses section
    with st.expander("Current Instructions and Responses", expanded=True):
        c1 = st.container()
        with c1:
            st.header("Instructions to LLM")
            current_instr_ph = st.empty()
            current_instr_ph.text((st.session_state.current_instr))
        
        c2 = st.container()
        with c2:
            st.header("LLM Responses")
            current_llm_ph = st.empty()
            current_llm_ph.text((st.session_state.current_llm))

    # Instructions and LLM Responses section
    with st.expander("Instructions and LLM Responses", expanded=False):
        c1 = st.container()
        with c1:
            st.header("Instructions to LLM")
            instr_ph = st.empty()
            instr_ph.text((st.session_state.instr))
        
        c2 = st.container()
        with c2:
            st.header("LLM Responses")
            llm_ph = st.empty()
            llm_ph.text((st.session_state.llm))
    
    # File Summaries section
    with st.expander("File Summaries", expanded=False):
        c1 = st.container()
        with c1:
            st.header("File Summaries")
            file_summary_text = st.text((update_file_structure()))

    # livelog
    with st.expander("Debug Log", expanded=False):
        c1 = st.container()
        with c1:
            st.header("Log")
            log_ph = st.empty()
            log_ph.text((st.session_state.log))

# Handle file clicks
if st.session_state.summary:
    for file in st.session_state.summary.keys():
        if st.checkbox(file):
            st.session_state.selected_file = file
            break

user_txt = st.text_input("Enter your input here:")

def update_state(session_state_var_name,value):

    # Update the session state variable
    st.session_state[session_state_var_name] = value
    # Use empty() to force re-render of the relevant text display
    if session_state_var_name == 'system':
        system_ph.text((st.session_state.system))
    elif session_state_var_name == 'status':
        status_ph.text((st.session_state.status))
    elif session_state_var_name == 'instr':
        instr_ph.text((st.session_state.instr))
    elif session_state_var_name == 'current_instr':
        current_instr_ph.text((st.session_state.current_instr))
    elif session_state_var_name == 'current_llm':
        current_llm_ph.text((st.session_state.current_llm))
    elif session_state_var_name == 'llm':
        llm_ph.text((st.session_state.llm))
    elif session_state_var_name == 'summary':
        file_summary_text.text((update_file_structure()))
    elif session_state_var_name == 'selected_file':
        summary_display.text((f"Summary for {st.session_state.selected_file}:\n{st.session_state.summary.get(st.session_state.selected_file, 'No summary available')}"))
    else:
        st.session_state.log += f'\n{session_state_var_name} = {value}'
        log_ph.text((st.session_state.log))

if "datastore" not in st.session_state:
    st.session_state.datastore = DataStore(update_state)

if user_txt:
    st.session_state.user = user_txt
    # Update the summary dictionary here via process_input
    # Make sure process_input updates st.session_state.summary
    process_input(user_txt, update_state, st.session_state.datastore)

    #%analyze /app/lobo lobo