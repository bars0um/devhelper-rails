import utils.states as states

last_assistant_message = False
next_step=states.UNINITIALIZED

# Code files
app_files=[]
done_queue=[]
update_queue=[]

last_linter_error=0

queue=[]

project_description="" #TODO REMOVE
epic=""
app_name="myapp"
