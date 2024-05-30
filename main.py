# Rails DevHelper
#

import requests
import sseclient  # pip install sseclient-py
import json
from utils.cli_input import cli_input
from utils.processors import process_response, load_code, load_description,scan_file
from utils.extractors import extract_epic_files, extract_and_save_code_to_filepath_in_comments, extract_update_files
import utils.datastore as datastore
import utils.constants as constants
import logging
import utils.messages as messages
import sys
import utils.states as states
import utils.llm as llm
import utils.actions as actions
import utils.markers as markers

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

def get_epic_message():
    """
    updates the epic message with any changes to state that are pertinent to the conversation with the LLM
    """
    if len(datastore.app_files) > 0:
        app_files = " , ".join(datastore.app_files)
        return {"role": "system", "content": "The following is the current project description." \
                + datastore.epic + "\n the following is a listing of the files for this application: \n " + app_files
                #+ " \n the following is the current code base of this application: \n " + datastore.code ## REMOVED AS THIS CAUSES DIVERGENCE...CONSIDER PUTTING SUMMARIES
                }
    else:
        return { "role": "system", "content": "The following is the current project description." + datastore.epic }

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
            print("all files written, awaiting further input")
            datastore.next_step == states.AWAIT_USER_INPUT
            return actions.NOOP

        #TODO: add current code state block here...and then insert it in the returned instructions
        write_code_message= {"role":"user",
                             "content": #"The following is the current project code: " + datastore.code + # REMOVED AS THIS THROWS OFF THE LLM AND CAUSES HUGE DIVERGENCE
                             " \n please only write " + datastore.update_queue[0] + ". Please add descriptive comments in all the code you write." \
                                    + " Note: " +  messages.how_to_write_code.replace("FILE_PATH", datastore.update_queue[0])}
        history.append(write_code_message)
        return trim_list([get_epic_message(),get_update_directive_message(),get_update_plan_message(),write_code_message])

    elif datastore.next_step == states.LLM_FIX_BUGGY_FILE:
        with open(datastore.update_queue[0],"r") as buggy_file:
            buggy_code = buggy_file.read()
            fix_code_error= {
                            "role":"user",
                            "content": "linter has detected an issue in the code for " + datastore.update_queue[0] + " please correct the problem and rewrite the file. bug report: " + datastore.last_linter_error \
                                    + " \n " + messages.how_to_write_code.replace("file_path", datastore.update_queue[0] ) + " here is the code that requires correction: " \
                                    + markers.START_CODE_RESPONSE + " \n " + buggy_code + " \n " + markers.END_CODE_RESPONSEmain.py                }
            datastore.next_step = states.LLM_WRITES_CODE
            history.append(fix_code_error)
            return trim_list([get_epic_message(),get_update_directive_message(),get_update_plan_message(),fix_code_error])

    elif datastore.next_step == states.LLM_REVIEWS_CURRENT_PROJECT_STATE:
        print(f"reading project code from {datastore.project_folder}")
        logging.info("Read project code from {datastore.project_folder}")
        
        datastore.code = load_code(datastore.project_folder)
        
        with open(datastore.project_folder+"/project.md","r") as project_description_file:
            datastore.epic = project_description_file.read()

        system_resume_message ={"role": "system", "content": "Review source code provided by user and wait for further instructions. Confirm that you have reviewed the source code by responding: " + messages.review_complete}
        
        datastore.next_step = states.LLM_CONFIRMS_REVIEW_OF_CURRENT_PROJECT_STATE #not sure if this is an unnessescary step...
 

        return [get_epic_message(),system_resume_message]
   
    elif datastore.next_step == states.LLM_EXPLAIN_UPDATE_PLAN:
        
        update_code_message ={ "role": "system", "content": "Please review user update request. Explain the changes that must be made to fulfill the user update request" }
        history.append(update_code_message)

        return trim_list([get_epic_message(),get_update_directive_message(),update_code_message])
   
    elif datastore.next_step == states.LLM_PROVIDES_UPDATE_FILE_QUEUE:

        logging.info("asking llm to provide update queue")
        create_queue_directive={"role":"user","content": messages.define_update_queue }#+ " \n Do this for the user update request: " + update_request["content"] }
    
        return trim_list([get_epic_message(),get_update_directive_message(),get_update_plan_message(),create_queue_directive])

    elif datastore.next_step == states.USER_PROVIDES_UPDATE_DETAILS:
        return actions.NOOP

def send_instructions_to_llm(instructions):
    """
        Sends instructions to LLM and collects the response
    """
    print("INSTRUCTIONS")
    print(instructions)
    print("/INSTRUCTIONS/")
    data = {
        "mode": "instruct",
        "stream": True,
        "temperature": 0,
        "seed": 123,
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
            print(chunk, end='')

        #print(payload)
    print()
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
        code_file = extract_and_save_code_to_filepath_in_comments(response)
        report = scan_file(code_file)
        logging.info("scan step completed")
        logging.info(report)

        if report == constants.SCAN_SUCCESS:
            logging.info("scan succeeded")
            print(f'scan succeeded for {code_file}')
            if code_file in datastore.update_queue:
                datastore.update_queue.remove(code_file)
            datastore.done_queue.append(code_file)
            datastore.code += "\n " + response + " \n "
                
        else:
            print(f'scan failed for {code_file}')
            logging.info("----Scan Fail----")
            logging.info(f"datastore file {datastore.update_queue[0]}")
            logging.info(report)
            logging.info("----/Scan Fail/----")
            datastore.next_step = states.LLM_FIX_BUGGY_FILE
            datastore.last_linter_error = report

    elif datastore.next_step == states.LLM_CONFIRMS_REVIEW_OF_CURRENT_PROJECT_STATE:
        if messages.review_complete in response:
            print("LLM confirmed review of project, now please describe update requirements as follows %update my new requirement")
            datastore.next_step = states.USER_PROVIDES_UPDATE_DETAILS
        else:
            print("WARNING: LLM has not conformed to expected response pattern. Continuing, please provide update details as %update details of update")
            datastore.next_step = states.USER_PROVIDES_UPDATE_DETAILS

    elif datastore.next_step == states.LLM_EXPLAIN_UPDATE_PLAN:
        datastore.update_plan = response
        datastore.next_step = states.LLM_PROVIDES_UPDATE_FILE_QUEUE

    elif datastore.next_step == states.LLM_PROVIDES_UPDATE_FILE_QUEUE:
        datastore.update_queue = extract_update_files(response)
        datastore.next_step = states.LLM_WRITES_CODE


def get_main_directive_from_user():
    """
    gets commands and input from user
    """
    user_message = cli_input("> ")

    if "%create" in user_message:
        logging.info("Stream Manager: Create new project, this will read project description and ask LLM to create proposed app_files list")
        if len(user_message.split(" ")) < 3:
            print("Arguments Missing \n Usage: %create /path/to/project/description.md yourappname \n")
            return actions.NOOP
        project_description_file = user_message.split(" ")[1]
        datastore.app_name = user_message.split(" ")[2]
        messages.customize_app_name(datastore.app_name)
        print("creating")
        datastore.epic = load_description(project_description_file)
        datastore.next_step=states.LLM_CREATES_APPFILES

    # user can input resume /app/src/folder app_name
    # assumption: project.md contains the project description...must update to make this obvious to user
    elif "%resume" in user_message:
        logging.info("Stream Manager: Resuming an already created project with specific project folder provided")
        datastore.project_folder = user_message.split(" ")[1]
        datastore.app_name = user_message.split(" ")[2]
        datastore.next_step = states.LLM_REVIEWS_CURRENT_PROJECT_STATE
    elif "%update" in user_message:
        logging.info("Update command detected, asking for update queue list")
        datastore.update_directive = user_message.replace("%update","")
        datastore.next_step = states.LLM_EXPLAIN_UPDATE_PLAN

    elif "%appinfo" in user_message:
        print("appfiles: ", datastore.app_files)
        print("update_queue: ",datastore.update_queue)
        print("done: ",datastore.done_queue)


def main():
    
    # first get user intent
    print("""Please state your intent, you should use one of the following:
        
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
        logging.info(f"after instruction state: {datastore.next_step}")
        logging.info("instructions:")
        logging.info(instructions)

        if instructions != actions.NOOP:
            response = send_instructions_to_llm(instructions)
            process(response)
        else:
         get_main_directive_from_user()

main()
