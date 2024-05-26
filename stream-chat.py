import requests
import sseclient  # pip install sseclient-py
import json
from utils.cli_input import cli_input
from utils.processors import process_response, load_code, load_description
import utils.datastore as datastore
import utils.constants as constants
import logging
import utils.messages as messages
import sys
import utils.states as states

last_assistant_message_block = False
log_format = "%(asctime)s - %(levelname)-5s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s"
logging.basicConfig(filename='dev-ai-assist.log', filemode='w',level=logging.INFO,format=log_format)

url = "http://oobabooga-server:5000/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

history = []


system_message_block = {'role': 'system', 'content':  messages.general_system_message}

while True:

    send_buffer=[]
       
    if datastore.state == constants.STATE_UNINITIALIZED and datastore.project_description == "":
        print("Please describe your project.")
    
    if len(datastore.queue) > 0:
        logging.info("action detected...handling adding to send_buffer")
        user_message_block = datastore.queue.pop(0)
        send_buffer.append(user_message_block)
        logging.info(user_message_block)
    else:
        user_message = cli_input("> ")
        user_message_block = {"role": "user", "content": user_message}
        send_buffer.append(user_message_block)

        if "%appinfo" in user_message:
            print(datastore.app_files)
            print(datastore.update_queue)
            print(datastore.done_queue)

            continue 

        if "%appname" in user_message:
            datastore.app_name = user_message.split(" ")[1]
            print("app name is now: datastore.app_name this will be used to direct assistant to write files under a folder with this name under /app")
            messages.customize_app_name(datastore.app_name)
            continue

        elif "%create" in user_message:
            logging.info("Stream Manager: Create new project, this will read project description and ask LLM to create proposed app_files list")
            if len(user_message.split(" ")) < 3:
                print("Arguments Missing \n Usage: %create /path/to/project/description.md yourappname \n")
                continue
            project_description_file = user_message.split(" ")[1]
            datastore.app_name = user_message.split(" ")[2]
            messages.customize_app_name(datastore.app_name)
            print("creating")
            datastore.project_description = load_description(project_description_file)
            create_message ={"role": "system", "content": "The following is the current project description. Please review the description and create a listing of the files necessary to create the application described. \n" \
                    + datastore.project_description + "\n" + messages.define_app_files  }  
            history.append(create_message)
            logging.info(create_message)
            datastore.state = constants.STATE_UNINITIALIZED
            send_buffer.append(create_message)

        # user can input resume /app/src/folder app_name
        # assumption: project.md contains the project description...must update to make this obvious to user
        elif "%resume" in user_message:
            logging.info("Stream Manager: Resuming an already created project with specific project folder provided")
            project_folder = user_message.split(" ")[1]
            datastore.app_name = user_message.split(" ")[2]
            print("resuming ")
            code = load_code(project_folder)
            with open(project_folder+"/project.md","r") as project_description_file:
                datastore.project_description = project_description_file.read()

            datastore.state = constants.STATE_COMPLETED_FIRST_ROUND
            resume_message ={"role": "user", "content": "The following is the current project code. Please review the project_description.md file for the project goal."
                                                        + code + "\n"}  
            system_resume_message ={"role": "system", "content": "Review source code provided by user and wait for further instructions. Confirm that you have reviewed the source code by responding: REVIEW COMPLETE, READY FOR FURTHER INSTRUCTIONS" }

            history.append(resume_message)
            history.append(system_resume_message)
            logging.info(resume_message)
            logging.info(system_resume_message)
        
            send_buffer.append(resume_message)
            send_buffer.append(system_resume_message)

        elif "%write" in user_message:
            logging.info("Stream Manager: Write command, we will proceed assuming app_files is defined and project description has been provided")
            write_code_message ={"role": "system", "content": "Please write the code for " + datastore.update_files[0] + "\n"
                                                        + messages.how_to_write_code + "\n"  }
            history.append(write_code_message)
            logging.info(write_code_message)

            send_buffer.append(write_code_message)

        elif "%analyze" in user_message:
            logging.info("Stream Manager: Code Analyze command detected, checking how to improve source code")
            if datastore.state != constants.STATE_COMPLETED_FIRST_ROUND:
                print("No files loaded for review, please use %resume /app/folder/ directive first")
            else:
                analyze_code_message ={"role": "system", "content": "Review source code provided and specifically project_description.md. Identify gaps in implementation and provide a new app_files json definition of files that need to be updated or created."
                                                        + messages.define_app_files + "\n" + "Do not write any code just yet please. Update the app_file list according to the user's feedback. If they ask you to start writing the code you can do so." }
            history.append(analyze_code_message)
            logging.info(analyze_code_message)
            datastore.state = constants.STATE_COMPLETED_ANALYSIS
        
            send_buffer.append(analyze_code_message)

        elif "%update" in user_message:
        # need to allow user to request modification of specific file
        # also ability to add file to app_files
            logging.info("Stream Manager: Code update command detected, asking for update queue list")
            if datastore.state != constants.STATE_COMPLETED_FIRST_ROUND:
                print("No files loaded for review, please use %resume /app/folder/ directive first")
                continue
            else:   
                update_code_message ={"role": "system", "content": messages.define_update_queue }
            
                history.append(update_code_message)
                logging.info(update_code_message)
                datastore.state = states.PENDING_UPDATE_QUEUE
                send_buffer.append(update_code_message)         
                print("modifying files")

        

        elif "%implement" in user_message: 
            logging.info("Stream Manager: Code review and update process, updating code")
            if datastore.state != constants.STATE_COMPLETED_ANALYSIS:
                print("You must ask assistant to analyze your current project after running the resume directive")
            else:
                analyze_code_message ={"role": "system", "content": "Please write the code for " + datastore.update_files[0] + "\n"
                                                        + messages.how_to_write_code + "\n"  }
            history.append(analyze_code_message)
            logging.info(analyze_code_message)
            send_buffer.append(analyze_code_message)
            
    #      if datastore.state == constants.STATE_UNINITIALIZED and datastore.project_description == "":
            #  datastore.project_description = user_message
            #  project_desctription_app_files_json_step = {"role": "system", "content": "The following is the user description of the application they want:"
            #                                              + datastore.project_description + " " 
            #                                              + messages.define_app_files }
            #  history.append(project_desctription_app_files_json_step)
            #  logging.info(project_desctription_app_files_json_step)
        
        else:
            logging.info("Stream Manager: no specific commands passing block on")
            logging.info(user_message_block)
            history.append(user_message_block)
            send_buffer.append(user_message_block)

    instructions = []

    instructions.append(system_message_block)

    # add other info
    if len(datastore.app_files) > 0:
        project_state_message_block ={"role": "system", "content": "The following is the current project description." \
                + " Please review the description and create a listing of the files necessary to create the application described. \n" \
                + datastore.project_description + "\n the following is a listing of the files for this application: \n" + ','.join(datastore.app_files)
                }
        instructions.append(project_state_message_block)


    if last_assistant_message_block !=False:
        instructions.append( last_assistant_message_block )

    instructions += send_buffer

    print("INSTRUCTIONS")
    print(instructions)
    print("end INSTRUCTIONS")
    data = {
        "mode": "instruct",
        "stream": True,
        "temperature": 0,
        "seed": 123,
        "do_sample":True,
        "messages": instructions
    }

    logging.info("<======INSTRUCTIONS=====>")
    logging.info(instructions)
    logging.info("<======/INSTRUCTIONS=====>")

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
    last_assistant_message_block = {"role": "assistant", "content": assistant_message}
    history.append(last_assistant_message_block)
   
    if datastore.state in [
                            states.UNINITIALIZED,
                            states.PENDING_CODE_WRITE,
                            states.PENDING_SUMMARY_WRITE,
                            states.PENDING_UPDATE_QUEUE]:
        action = process_response(assistant_message)

        if action["command"] == constants.ACTION_FOLLOWUP:
            logging.info("Stream Manager: follow-up added to queue\n" )
            logging.info(action["message"])

            datastore.queue.append(action["message"])
            #clear the user_message
            user_message=""

