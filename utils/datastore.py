import utils.states as states

last_assistant_message = False
next_step=states.UNINITIALIZED

# Code files
app_files=[]
done_queue=[]
update_queue=[]
project_folder=""
diagnose_error=""
last_linter_error=0
code=""
queue=[]
update_directive=""
update_plan=""
project_description="" #TODO REMOVE
task_relevant_code=""
epic=""
app_name="myapp"
bug_type=""
