import utils.states as states

last_assistant_message = False
next_step=states.UNINITIALIZED

# Code files
app_files=[]
done_queue=[]
update_queue=[]
project_folder=""
last_linter_error=0
code=""
queue=[]
update_directive=""
update_plan=""
project_description="" #TODO REMOVE
epic=""
app_name="myapp"
