import requests
import sseclient  # pip install sseclient-py
import json
from utils.cli_input import cli_input
from utils.processors import process_response
import utils.datastore as datastore
import utils.constants as constants
import logging
import utils.messages as messages

log_format = "%(asctime)s - %(levelname)-5s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s"
logging.basicConfig(filename='dev-ai-assist.log', filemode='w',level=logging.INFO,format=log_format)

url = "http://oobabooga-server:5000/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

history = []

system_message_block = {'role': 'system', 'content':  messages.general_system_message}
history.append(system_message_block)
logging.info("SYSTEM MESSAGE")
logging.info(system_message_block)

while True:
       
    if datastore.state == constants.STATE_UNINITIALIZED and datastore.project_description == "":
        print("Please describe your project.")
    
    if len(datastore.queue) > 0:
        user_message_block = datastore.queue.pop(0)
    else:
        user_message = cli_input("> ")
        user_message_block = {"role": "user", "content": user_message}

    if datastore.state == constants.STATE_UNINITIALIZED and datastore.project_description == "":
        datastore.project_description = user_message
        project_desctription_app_files_json_step = {"role": "system", "content": "The following is the user description of the application they want:"
                                                    + datastore.project_description + " ``" 
                                                    + messages.define_app_files }
        history.append(project_desctription_app_files_json_step)
        logging.info(project_desctription_app_files_json_step)
    
    else:
        logging.info(user_message_block)
        history.append(user_message_block)


    data = {
        "mode": "instruct",
        "stream": True,
        "temperature": 0,
        "seed": 123,
        "do_sample":True,
        "messages": history
    }

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
    logging.info(assistant_message)
    history.append({"role": "assistant", "content": assistant_message})
    action = process_response(assistant_message)

    if action["command"] == constants.ACTION_FOLLOWUP:
        datastore.queue.append(action["message"])
