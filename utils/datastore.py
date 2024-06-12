import utils.states as states

last_assistant_message = False
next_step=states.UNINITIALIZED
specific_file_code=""
# Code files
loaded_files=[]
app_files=[]
done_queue=[]
update_queue=[]
task_relevant_files=[]
project_folder=""
diagnose_error=""
last_linter_error=""
code=""
queue=[]
update_directive=""
update_plan=""
project_description="" #TODO REMOVE
task_relevant_code=""
epic=""
app_name="myapp"
bug_type=""
last_assistant_message=""
bug_details=""
