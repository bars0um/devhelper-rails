# Attempt to re-write and organize this code
# Here we need to think about what the user desire is
# initially we get a broad 

import requests
import sseclient  # pip install sseclient-py
import json
from utils.cli_input import cli_input
from utils.processors import process_response, load_code, load_description,scan_file
from utils.extractors import extract_epic_files, extract_and_save_code_to_filepath_in_comments
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

def create_instructions():
    
    epic_message_block = {}
    if len(datastore.app_files) > 0:
        epic_message_block ={"role": "system", "content": "The following is the current project description." \
                + datastore.epic + "\n the following is a listing of the files for this application: \n" + ','.join(datastore.app_files)
                }

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
                            "content": "please only write " + datastore.update_queue[0] + ". Please add descriptive comments in all the code you write." \
                                    + " Note: " +  messages.how_to_write_code.replace("FILE_PATH", datastore.update_queue[0])}

        return [epic_message_block,write_code_message]
    elif datastore.next_step == states.LLM_FIX_BUGGY_FILE:
        with open(datastore.update_queue[0],"r") as buggy_file:
            buggy_code = buggy_file.read()
            fix_code_error= {
                            "role":"user",
                            "content": "linter has detected an issue in the code for " + datastore.update_queue[0] + " please correct the problem and rewrite the file. bug report: " + datastore.last_linter_error \
                                    + " \n " + messages.how_to_write_code.replace("file_path", datastore.update_queue[0] ) + " here is the code that requires correction: " \
                                    + markers.START_CODE_RESPONSE + " \n " + buggy_code + " \n " + markers.END_CODE_RESPONSE

                            }
            datastore.next_step = states.LLM_WRITES_CODE
            return [epic_message_block,fix_code_error]
#  def get_next_message_for_llm():
    #  resume_message = False
    #  update_code_message = False
    #  update_description = False
    #  update_instructions = False
    #  update_request = False
    #  send_buffer=[]
    #  if datastore.next_step == states.UNINITIALIZED and datastore.epic == "":
    #      print("Input:")
    
    #  if len(datastore.queue) > 0:
    #      logging.info("action detected...handling adding to send_buffer")
    #      user_message_block = datastore.queue.pop(0)
    #      send_buffer.append(user_message_block)
    #      logging.info(user_message_block)
    #  else:
    #      user_message = cli_input("> ")
    #      user_message_block = {"role": "user", "content": user_message }
    #      if not "%update" in user_message:
    #          send_buffer.append(user_message_block)
        
    #      if "%appinfo" in user_message:
    #          print(f"app_files: {datastore.app_files}")
    #          print(f"update_queue {datastore.update_queue}")
    #          print(f"done_queue: {datastore.done_queue}")
            
    #          return actions.NOOP

    #      if "%appname" in user_message:
    #          datastore.app_name = user_message.split(" ")[1]
    #          print("app name is now: datastore.app_name this will be used to direct assistant to write files under a folder with this name under /app")
    #          messages.customize_app_name(datastore.app_name)
    #          return actions.NOOP
        
    #      if "%update" in user_message:
    #      # need to allow user to request modification of specific file
    #      # also ability to add file to app_files
    #          logging.info("Stream Manager: Code update command detected, asking for update queue list")
    #          user_message = user_message.replace("%update","")
    #          if datastore.next_step != states.PENDING_UPDATE_INSTRUCTIONS:
    #              print("must resume a project first, review logic")
    #              return actions.NOOP
    #          else:   
    #              user_update_message={ "role":"user","content": user_message }
    #              update_request = user_update_message
    #              update_code_message ={"role": "system", "content": "Please review user update request. Explain what needs to be done to achieve this." }
            
    #              history.append(user_update_message)
    #              logging.info(user_update_message)
    #              send_buffer.append(user_update_message)         
    #              history.append(update_code_message)
    #              logging.info(update_code_message)
    #              send_buffer.append(update_code_message)         
    #              datastore.next_step = states.PENDING_UPDATE_INSTRUCTIONS
    #              print("modifying files")
        
        
    #      else:
    #          logging.info("Stream Manager: no specific commands passing block on")
    #          logging.info(user_message_block)
    #          history.append(user_message_block)
    #          send_buffer.append(user_message_block)
           
        
    #  instructions = []

    #  instructions.append(system_message_block)

    #  # add other info
    #  if len(datastore.app_files) > 0:
    #      project_state_message_block ={"role": "system", "content": "The following is the current project description." \
    #              + " Please review the description and create a listing of the files necessary to create the application described. \n" \
    #              + datastore.epic + "\n the following is a listing of the files for this application: \n" + ','.join(datastore.app_files)
    #              }
    #      instructions.append(project_state_message_block)

    #  if resume_message != False and not datastore.next_step == states.RESUME_STARTED:
    #      instructions.append(resume_message)

    #  if update_request!=False and not update_request in instructions and not update_request in send_buffer:
    #      instructions.append(update_request)

    #  if update_code_message != False and not datastore.next_step == states.PENDING_UPDATE_QUEUE:
    #      if not update_code_message in instructions and not update_code_message in send_buffer:
    #          instructions.append(update_code_message)

    #  if update_instructions != False:
    #      instructions.append(update_instructions)

    #  if datastore.last_assistant_message !=False:
    #      if not datastore.last_assistant_message in instructions and not datastore.last_assistant_message in send_buffer:
    #          instructions.append( datastore.last_assistant_message )


    #  instructions += send_buffer

  
    #  return instructions


def send_instructions_to_llm(instructions):
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
                
        else:
            print(f'scan failed for {code_file}')
            logging.info("----Scan Fail----")
            logging.info(f"datastore file {datastore.update_queue[0]}")
            logging.info(report)
            logging.info("----/Scan Fail/----")
            datastore.next_step = states.LLM_FIX_BUGGY_FILE
            datastore.last_linter_error = report


    #  if datastore.next_step in [
    #                          states.UNINITIALIZED,
    #                          states.PENDING_CODE_WRITE,
    #                          states.PENDING_SUMMARY_WRITE,
    #                          states.PENDING_USER_AGREE,
    #                          states.PENDING_UPDATE_QUEUE
    #                          ]:
    #      logging.info(f"datastore.next_step is {datastore.next_step}")
    #      action = process_response(response)

    #      if action["command"] == constants.ACTION_FOLLOWUP:
    #          logging.info("Stream Manager: follow-up added to queue\n" )
    #          logging.info(action["message"])

    #          datastore.queue.append(action["message"])
    #          #clear the user_message
    #          user_message=""

    #  if datastore.next_step == states.PENDING_UPDATE_INSTRUCTIONS:
    #      logging.info("LLM provided update plan")
    #      update_instructions = datastore.last_assistant_message
    #      create_queue_directive={"role":"user","content": messages.define_update_queue }#+ " \n Do this for the user update request: " + update_request["content"] }
    #      datastore.queue.append(create_queue_directive)
    #      datastore.next_step = states.PENDING_UPDATE_QUEUE

    #  if messages.review_complete in response:
    #      logging.info("LLM reported review complete")
        #  datastore.next_step = states.PENDING_UPDATE_INSTRUCTIONS


def get_epic_from_user():
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
        project_folder = user_message.split(" ")[1]
        datastore.app_name = user_message.split(" ")[2]
        print("resuming ")
        code = load_code(project_folder)
        with open(project_folder+"/project.md","r") as project_description_file:
            datastore.epic = project_description_file.read()

        datastore.next_step = states.RESUME_STARTED
        resume_message ={"role": "user", "content": "The following is the current project code. Please review the project_description.md file for the project goal."
                                                    + code + "\n"}  
        system_resume_message ={"role": "system", "content": "Review source code provided by user and wait for further instructions. Confirm that you have reviewed the source code by responding: " + messages.review_complete}

        history.append(resume_message)
        history.append(system_resume_message)
        logging.info(resume_message)
        logging.info(system_resume_message)
    
        send_buffer.append(resume_message)
        send_buffer.append(system_resume_message)
        logging.info(f"datastore.next_step is {datastore.next_step}")

def main():
    
    # first get user intent
    print("""Please state your intent, you should use one of the following:
        
        * %create /app/myapp/project.md mycoolapp
          make sure you place a clear description of what you want to build in 
          the project.md as this will become the epic that the LLM will work with.
          
        * %resume /app/myapp mycoolapp
          note this will look for app_files.json file which was created by the create
          stage. It will load that code and present it to the LLM

        * %update add some cool feature blah blah blah
          this needs to be run after a resume to describe what you want to done to the
          existing application you created previously. description ghere becomes the epic
          """
    )

    # determine what epic we will work on today
    get_epic_from_user()
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
         get_epic_from_user()

main()
