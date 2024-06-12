# Rails DevHelper
#

import requests
import sseclient  # pip install sseclient-py
import json
from utils.cli_input import cli_input
from utils.processors import process_response, load_code, load_description, scan_file, load_code_from_list
from utils.extractors import extract_epic_files, extract_and_save_code_to_filepath_in_comments, extract_update_files, extract_task_relevant_files
import utils.datastore as datastore
import utils.constants as constants
import logging
import utils.messages as messages
import sys
import utils.states as states
import utils.llm as llm
import utils.actions as actions
import utils.markers as markers
import utils.bugs as bugs
import time
from utils.tokens import num_tokens_from_string
from utils.panes import start_pane_printer, print_instructions, print_system, print_user, print_llm, get_user_input
import utils.commands as commands

start_pane_printer()
time.sleep(1)

log_format = "%(asctime)s - %(levelname)-5s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s"
logging.basicConfig(filename='dev-ai-assist.log', filemode='w',level=logging.INFO,format=log_format)

url = "http://oobabooga-server:5000/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

history = []
key_message = []

system_message_block = {'role': 'system', 'content':  messages.general_system_message}

def trim_list(mylist):
    return list(filter(lambda x: x is not None, mylist))

def get_update_directive_message():
    if len(datastore.update_directive) > 0:
        return { "role": "user", "content": datastore.update_directive }
    else: 
        return None

def get_update_plan_message():                
    if len(datastore.update_plan) > 0:
        return { "role": "assistant", "content": datastore.update_plan }
    else:
        return None

def get_error_report_message():
    if len(datastore.diagnose_error) > 0:
        return { "role": "user", "content": "The application throws the following error: " + datastore.diagnose_error + " \n " }
    else:
        return None

def get_last_assistant_message():
    return datastore.last_assistant_message

def get_epic_message():
    """
    updates the epic message with any changes to state that are pertinent to the conversation with the LLM
    """
    if len(datastore.app_files) > 0:
        app_files = " , ".join(datastore.app_files)
        return {"role": "system", "content": "The following is the current project description. " \
                + datastore.epic + "\n the following is a listing of the files for this application: \n " + app_files
                #+ " \n the following is the current code base of this application: \n " + datastore.code ## REMOVED AS THIS CAUSES DIVERGENCE...CONSIDER PUTTING SUMMARIES
                }
    else:
        return { "role": "system", "content": "The following is the current project description. " + datastore.epic }

def get_task_relevant_code():

    # if datastore.read_files is set, read the content and return it here
    datastore.task_relevant_code = load_code_from_list(datastore.task_relevant_files)
    if len(datastore.task_relevant_code) > 0:
        #  return {"role":"system", "content":  " original code base: " + datastore.code  + " \n the following is the code for the files that are to be updated: \n " + datastore.task_relevant_code}
        return {"role":"system", "content": " \n the following is the code for the files that are to be updated: \n " + datastore.task_relevant_code}
    else:
        return None

def get_specific_file_code():
    if len(datastore.specific_file_code) > 0:
        datastore.specific_file_code =  " ".join(datastore.specific_file_code.split())
        return {"role":"user", "content": " the following is the target file's code: \n " + datastore.specific_file_code}
    else: 
        return None

def get_loaded_code():
   
    # keep updating the code
    datastore.code = " ".join(load_code(datastore.project_folder).split())
    if len(datastore.code) > 0:
        return {"role":"user", "content": " the following is the current code base: \n " + datastore.code}
    else:
        return None

def get_how_to_write_code():
    return  {
                "role":"user",
                "content": messages.how_to_write_code.replace("file_path", datastore.update_queue[0] )
            }

def create_instructions():
    """
    Creates the instructions that need to be sent to the LLM depending on the next_step state
    """
    if datastore.next_step == states.LLM_CREATES_APPFILES:
        create_message ={"role": "system", "content": "The following is the current project description. Please review the description and create a listing of the files necessary to create the application described. \n" \
                + datastore.epic + "\n" + messages.define_app_files  }  
        history.append(create_message)
        logging.info(create_message)
        return [create_message]

    elif datastore.next_step == states.LLM_WRITES_CODE:

        if len(datastore.update_queue) == 0:
            print_system("all files written, awaiting further input")
            datastore.next_step == states.AWAIT_USER_INPUT
            return actions.NOOP
        
        print_system("Writing File:" + datastore.update_queue[0])
        #TODO: add current code state block here...and then insert it in the returned instructions
        write_code_message= {"role":"user",
                             "content": #"The following is the current project code: " + datastore.code + # REMOVED AS THIS THROWS OFF THE LLM AND CAUSES HUGE DIVERGENCE
                             " \n please only write " + datastore.update_queue[0] + " . " 
                                   }
        history.append(write_code_message)
        return trim_list([
            get_epic_message(),
            get_error_report_message(),
            get_loaded_code(),
            get_specific_file_code(),
            get_update_directive_message(),
            get_update_plan_message(),
            get_task_relevant_code(),
            get_how_to_write_code(),
            write_code_message
            ])

    elif datastore.next_step == states.LLM_FIX_BUGGY_FILE:
            buggy_code = datastore.buggy_code
            
            if datastore.bug_type == bugs.FORMAT:
                fix_code_error= {
                            "role":"user",
                            "content": " STOP, assistant did not use the correct format for writing " + datastore.update_queue[0] }
                datastore.bug_type = bugs.SYNTAX
            elif datastore.bug_type == bugs.FILEPATH:
                fix_code_error= {
                            "role":"user",
                            "content": " STOP, assistant did not use the correct file path " + datastore.update_queue[0] + " " + datastore.bug_details}
                datastore.bug_type = bugs.SYNTAX
            else:
                add_explanation = ""
                if messages.linter_unexpected_end in datastore.last_linter_error:
                    add_explanation=" you have not properly terminated one of the blocks in the code, please fix it "
                fix_code_error= {
                            "role":"user",
                            "content": " linter has detected an issue in the code for " + datastore.update_queue[0] + " please explain the error, correct the problem and rewrite the file. bug report: " + datastore.last_linter_error \
                                    + " " + add_explanation +  " \n " + " here is the code that requires correction: " \
                                    + " \n " + buggy_code + " \n " }

          
            datastore.next_step = states.LLM_WRITES_CODE
            history.append(fix_code_error)
            return trim_list([
                get_epic_message(),
                get_error_report_message(),
                get_update_directive_message(),
                get_task_relevant_code(),
                get_update_plan_message(),
                get_loaded_code(),
                get_last_assistant_message(),
                fix_code_error,
                get_how_to_write_code()
                ])

    elif datastore.next_step == states.LLM_REVIEWS_CURRENT_PROJECT_STATE:
        print_system(f"reading project code from {datastore.project_folder}")
        logging.info("Read project code from {datastore.project_folder}")
        
        datastore.code = load_code(datastore.project_folder)
        print_system("\n".join(datastore.loaded_files))
        
        with open(datastore.project_folder+"/project.md","r") as project_description_file:
            datastore.epic = project_description_file.read()

        system_resume_message ={"role": "system", "content": "Review source code provided by user and wait for further instructions. Confirm that you have reviewed the source code by responding: " + messages.review_complete}
        
        datastore.next_step = states.LLM_CONFIRMS_REVIEW_OF_CURRENT_PROJECT_STATE #not sure if this is an unnessescary step...
 

        return trim_list([
                get_epic_message(),
                get_loaded_code(),
                system_resume_message
                ])
   
    elif datastore.next_step == states.LLM_EXPLAIN_UPDATE_PLAN:
        
        update_code_message ={ "role": "user", "content": datastore.update_directive + " Explain the changes that must be made to fulfill the user update request" }
        history.append(update_code_message)

        return trim_list([
            get_epic_message(),
            get_update_directive_message(),
            get_loaded_code(),
            update_code_message
            ])
   
    elif datastore.next_step == states.LLM_PROVIDES_UPDATE_FILE_QUEUE:

        logging.info("asking llm to provide update queue")
        create_queue_directive={"role":"user","content": messages.define_update_queue.replace("REQUEST_TEXT",datastore.update_directive) }#+ " \n Do this for the user update request: " + update_request["content"] }
    
        return trim_list([
            get_epic_message(),
            get_error_report_message(),
            get_update_directive_message(),
            get_update_plan_message(),
            get_loaded_code(),
            get_task_relevant_code(),
            create_queue_directive
            ])

    elif datastore.next_step == states.USER_PROVIDES_UPDATE_DETAILS:
        return actions.NOOP

    elif datastore.next_step == states.DIAGOSIS_LLM_IDENTIFIES_ROOT_CAUSE_FILES:
        logging.info("asking llm to review error and determine which files it would like to review, update or create to find and fix the error")
        error_to_llm_and_read_files_message={"role": "user", "content": messages.list_files_to_read }
        return trim_list([
            get_epic_message(),
            get_error_report_message(),
            error_to_llm_and_read_files_message
            ])
                
    elif datastore.next_step == states.LLM_DETERMINE_ROOT_CAUSE_FROM_FILES:
        logging.info("ask llm to review code and determine root cause, identifying update plan so we can switch over to update logic")
        determine_root_cause_message = {"role":"user", "content":" please read the relevant code, determine the root cause of the error and explain how to fix the error"}
        return trim_list([
            get_epic_message(),
            get_error_report_message(),
            get_task_relevant_code(),
            determine_root_cause_message
            ])

def count_instruction_tokens(instructions):
    
    total = 0 
    
    for instruction in instructions:
        total += num_tokens_from_string(instruction["content"],"cl100k_base")

    return total


def send_instructions_to_llm(instructions):
    """
        Sends instructions to LLM and collects the response
    """

    print_instructions(instructions)
    print_instructions(f'Token count: {count_instruction_tokens(instructions)}')
    data = {
        "mode": "instruct",
        "stream": True,
        #"temperature": 0,
        "seed": 123,
        "max_tokens": 8192,
        "do_sample":True,
        "messages": instructions
    }

    logging.info(f"SENDING INSTRUCTIONS...")

    stream_response = requests.post(url, headers=headers, json=data, verify=False, stream=True)
    client = sseclient.SSEClient(stream_response)
    
    assistant_message = ''
    for event in client.events():
        payload = json.loads(event.data)
        if 'delta' in payload['choices'][0]:
            chunk = payload['choices'][0]['delta']['content']
            assistant_message += chunk
            print_llm(chunk,streamed=True)

        #print(payload)
    logging.info("<=======RESPONSE=======>")
    logging.info(assistant_message)
    logging.info("<=====/RESPONSE/=======>")
    datastore.last_assistant_message = {"role": "assistant", "content": assistant_message}
    history.append(datastore.last_assistant_message)
    return assistant_message


def process(response):
    """
    processes LLM response and bumps state machine along
    """
    if datastore.next_step == states.LLM_CREATES_APPFILES:
        datastore.app_files = extract_epic_files(response)
        datastore.update_queue = datastore.app_files
        datastore.next_step = states.LLM_WRITES_CODE

    elif datastore.next_step == states.LLM_WRITES_CODE:

        try:
            code_file = extract_and_save_code_to_filepath_in_comments(response)
            print_system("Reading LLM provided File:" + code_file + " for " + datastore.update_queue[0])
        except Exception as e:
            print_system(repr(e))
            if "Missing" in repr(e):
                datastore.buggy_code = response
                datastore.next_step = states.LLM_FIX_BUGGY_FILE
                datastore.bug_type = bugs.FORMAT
                return

        #report = scan_file(code_file) disabled scanning for now as eslint is needed here...
        report = constants.SCAN_SUCCESS
        logging.info("scan step completed")
        logging.info(report)

        if report == constants.SCAN_SUCCESS:
            logging.info("scan succeeded")
            print_system(f'scan succeeded for {code_file}')
            if datastore.command == commands.MODIFY:
                datastore.update_queue.remove(datastore.update_queue[0])
                datastore.done_queue.append(code_file)
                datastore.code += "\n " + response + " \n "
            elif code_file in datastore.update_queue:
                datastore.update_queue.remove(code_file)
                datastore.done_queue.append(code_file)
                datastore.code += "\n " + response + " \n "
            else:
                print_system("LLM did not provide the correct file path")
                datastore.next_step = states.LLM_FIX_BUGGY_FILE
                datastore.bug_type=bugs.FILEPATH
                datastore.bug_details = "incorrect file path used: " + code_file + " you must write to " + datastore.update_queue[0]
        else:
            with open(datastore.update_queue[0],"r") as buggy_file:
                datastore.buggy_code = buggy_file.read()
            print_system(f'scan failed for {code_file}')
            logging.info("----Scan Fail----")
            logging.info(f"datastore file {datastore.update_queue[0]}")
            logging.info(report)
            logging.info("----/Scan Fail/----")
            datastore.next_step = states.LLM_FIX_BUGGY_FILE
            datastore.last_linter_error = report.replace(messages.linter_warning_nonsense,"")

    elif datastore.next_step == states.LLM_CONFIRMS_REVIEW_OF_CURRENT_PROJECT_STATE:
        if messages.review_complete in response:
            print_system("LLM confirmed review of project, now please describe update requirements as follows %update my new requirement")
            datastore.next_step = states.USER_PROVIDES_UPDATE_DETAILS
        else:
            print_system("WARNING: LLM has not conformed to expected response pattern. Continuing, please provide update details as %update details of update")
            datastore.next_step = states.USER_PROVIDES_UPDATE_DETAILS

    elif datastore.next_step == states.LLM_EXPLAIN_UPDATE_PLAN:
        datastore.update_plan = response
        datastore.next_step = states.LLM_PROVIDES_UPDATE_FILE_QUEUE

    elif datastore.next_step == states.LLM_PROVIDES_UPDATE_FILE_QUEUE:
        datastore.update_queue = extract_update_files(response)
        print_system("Update Queue:" + "\n".join(datastore.update_queue))
        datastore.task_relevant_files = datastore.update_queue
        datastore.task_relevant_code = load_code_from_list([datastore.update_queue[0]])
        datastore.next_step = states.LLM_WRITES_CODE

    elif datastore.next_step == states.DIAGOSIS_LLM_IDENTIFIES_ROOT_CAUSE_FILES:
        datastore.task_relevant_code = load_code_from_list(extract_task_relevant_files(response))
        datastore.next_step = states.LLM_DETERMINE_ROOT_CAUSE_FROM_FILES

    # Diagnostic workflow now fuses with update workflow
    elif datastore.next_step == states.LLM_DETERMINE_ROOT_CAUSE_FROM_FILES:
        datastore.update_plan = response
        datastore.next_step = states.LLM_PROVIDES_UPDATE_FILE_QUEUE

def get_main_directive_from_user():
    """
    gets commands and input from user
    """
    user_message = get_user_input() # cli_input("> ")

    if user_message is None:
        return

    print_system(user_message)

    if commands.CREATE in user_message:
        datastore.command=commands.CREATE
        logging.info("Stream Manager: Create new project, this will read project description and ask LLM to create proposed app_files list")
        if len(user_message.split(" ")) < 3:
            print_system("Arguments Missing \n Usage: %create /path/to/project/description.md yourappname \n")
            return actions.NOOP
        project_description_file = user_message.split(" ")[1]
        datastore.app_name = user_message.split(" ")[2]
        messages.customize_app_name(datastore.app_name)
        print_system("creating")
        datastore.epic = load_description(project_description_file)
        datastore.next_step=states.LLM_CREATES_APPFILES

    # user can input resume /app/src/folder app_name
    # assumption: project.md contains the project description...must update to make this obvious to user
    elif commands.RESUME in user_message:
        datastore.command=commands.RESUME
        logging.info("Stream Manager: Resuming an already created project with specific project folder provided")
        datastore.project_folder = user_message.split(" ")[1]
        datastore.app_name = user_message.split(" ")[2]
        messages.customize_app_name(datastore.app_name)
        datastore.next_step = states.LLM_REVIEWS_CURRENT_PROJECT_STATE

    elif commands.MODIFY in user_message:
        datastore.command=commands.MODIFY
        logging.info("Update command detected, asking for update queue list")
        modify_file_path=user_message.split(" ")[1]
        print_system(f'request to modify {modify_file_path}')
        datastore.specific_file_code = load_code_from_list([modify_file_path])
        # removing command details
        user_message = user_message.replace(user_message.split(" ")[0],"")
        user_message = user_message.replace(user_message.split(" ")[0],"")
        datastore.update_directive = user_message
        print_system(f'update directive {datastore.update_directive}')
        datastore.update_queue=[modify_file_path]
        datastore.next_step = states.LLM_WRITES_CODE

    
    elif commands.UPDATE in user_message:
        datastore.command=commands.UPDATE
        logging.info("Update command detected, asking for update queue list")
        if "%file" in user_message:
            datastore.specific_file_code = load_code_from_list([user_message.split(" ")[2]])
            user_message = user_message.replace("%file","")
            user_message = user_message.replace(user_message.split(" ")[2],"")
        datastore.update_directive = user_message.replace("%update","")
        datastore.next_step = states.LLM_EXPLAIN_UPDATE_PLAN

    elif commands.DIAGNOSE in user_message:
        datastore.command=commands.DIAGNOSE
        logging.info("Diagnose error command")
        datastore.diagnose_error = user_message.replace("%diagnose ","")
        datastore.next_step = states.DIAGOSIS_LLM_IDENTIFIES_ROOT_CAUSE_FILES

    elif commands.APPINFO in user_message:
        datastore.command=commands.APPINFO
        print_system("appfiles: ", datastore.app_files)
        print_system("update_queue: ",datastore.update_queue)
        print_system("done: ",datastore.done_queue)

    print_system(f'Next Step: ' + datastore.next_step)

def main():
    
    # first get user intent
    print_instructions("""Please state your intent, you should use one of the following:
        
        * %create /app/myapp/project.md mycoolapp
          make sure you place a clear description of what you want to build in 
          the project.md as this will become the epic that the LLM will work with.
          
        * %resume /app/myapp mycoolapp
          note this will look for app_files.json file which was created by the create
          stage. It will load that code and present it to the LLM. This assumes that
          a project.md file describes the application and is found in project root folder

        * %update add some cool feature blah blah blah
          this needs to be run after a resume to describe what you want to done to the
          existing application you created previously. description ghere becomes the epic
          """
    )

    # determine what epic we will work on today
    get_main_directive_from_user()
    while True:

        logging.info(f"before instruction state: {datastore.next_step}")
        instructions = create_instructions()
        print_system(f'Next Step: ' + datastore.next_step)
        logging.info(f"after instruction state: {datastore.next_step}")
        if instructions != actions.NOOP:
            for instruction in instructions:
                logging.info(instruction["role"] + ":")
                logging.info(instruction["content"])
                logging.info("---------------------")
            response = send_instructions_to_llm(instructions)
            process(response)
        else:
            get_main_directive_from_user()

main()
