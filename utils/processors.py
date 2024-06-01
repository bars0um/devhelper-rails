import re
from pathlib import Path
import os
import utils.datastore as datastore
import json
import subprocess
import utils.constants as constants
import utils.messages as messages
import logging
import sys
import glob
import utils.markers as markers
import utils.states as states

def extract_app_files(data):

    # Parse JSON data
    plain_data = data
    data = json.loads(data)
    logging.info(f"data: {data} ")
    # Extract file paths from the list and store them in a new list
    if  data["app_files"]:
        datastore.app_files = data["app_files"]
        logging.info(f"app_files extracted: {datastore.app_files}")
        # TODO: check changes to app_files.sjon
        with open(f"/app/{datastore.app_name}/app_files.json","w") as file:
            file.write(plain_data)

    return datastore.app_files


def extract_update_files(data):

    # Parse JSON data
    plain_data = data
    data = json.loads(data)
    logging.info(f"data: {data} ")
    # Extract file paths from the list and store them in a new list
    if  data["update_files"]:
        datastore.update_queue = data["update_files"]
        logging.info(f"update_files extracted: {datastore.app_files}")

    return datastore.update_queue

def get_file_path(code):
    """
    Extracts a file path from various comment formats at the beginning of the provided code block.
 
    Parameters:
        code (str): A string containing the content of a file or code block.
 
    Returns:
        str: The extracted file path if found, otherwise raises an exception.
    """
    if len(code)>0:
        # Regular expression pattern to match a file path in various comment formats
        pattern = re.compile(r"^\s*(?:[<!%\-]*)\s*#*\s*(.*\/[\w\/.\-]+)", re.MULTILINE)
        # Search through the entire content to find the first valid file path in a comment
        for line in code.splitlines():
            match = pattern.match(line)
            if match:
                # Return the first file path found within the comments
                return match.group(1)
 
    # If no valid path is found, raise an exception
    raise Exception("Could not find comment with file path at top of code block. ensure you put the full absolute path to the file " + datastore.app_files[0])


def create_file(full_path,code):

    dir_path = os.path.dirname(full_path)

    # Extract the file name
    file_name = os.path.basename(full_path)

    # Create the directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Create the full file path including the directory
    file_path = os.path.join(dir_path, file_name)

    # Open the file for writing
    with open(file_path, 'w') as file:
        # Write to the file
        file.write(code)
    
    print(f'{full_path} created successfully')

def scan_file(file_path):

    if ".rb" in file_path:
        # Prepare the command to run rubocop
        command = ['rubocop', '-a','-l', file_path]
        
        # Execute the command
        try:
            # Run the command and capture the output
            result = subprocess.run(command, check=True, text=True, capture_output=True )
            # Print the stdout and stderr from rubocop
            logging.info("-------------------------------")
            logging.info(f"Rubocop Output:\n  {result.stdout}")
            logging.info("-------------------------------")

            if "no offenses detected" in result.stdout:
                return constants.SCAN_SUCCESS
            else:
                raise Exception(result.stdout)

        except  Exception as e:
            # Print the error if rubocop exits with a non-zero status
            logging.info("Scan Failed:")
            logging.info("==============")
            try:
                logging.info(e.output)
                error=e.output
            except AttributeError as ex:
                logging.info(e)
                error=repr(e)
            logging.info("==============")
            return error
    elif "html" in file_path or "ebr" in file_path:
        # Prepare the command to run rubocop
        command = ['erblint', file_path]
        
        # Execute the command
        try:
            logging.info(f"------> calling {command} ")
            # Run the command and capture the output
            result = subprocess.run(command, check=True, text=True, capture_output=True )

            logging.info("-------< call completed")
            # Print the stdout and stderr from rubocop
            logging.info(f"Erblint Output:\n {result.stdout}")
            logging.info("-------------------------------")

            if "No errors were found" in result.stdout:
                return constants.SCAN_SUCCESS
            else:
                raise Exception(result.stdout)

        except  Exception as e:
            # Print the error if rubocop exits with a non-zero status
            logging.info("Scan Failed:")
            logging.info("==============")
            logging.info(e.output)
            logging.info("==============")
            return e.output





def process_response(input_string):

    action = {
            "command": constants.ACTION_NOOP
            }
    start_marker="UNDEFINED"
    # Extract the content within triple-ticked code block
    # Find the start of the triple-ticked block
    if markers.START_APPFILES in input_string:
        start_marker = markers.START_APPFILES
        end_marker = markers.END_APPFILES
    elif markers.START_CODE_RESPONSE in input_string:
        start_marker = markers.START_CODE_RESPONSE
        end_marker = markers.END_CODE_RESPONSE
    elif markers.START_SUMMARY in input_string:
        start_marker = markers.START_SUMMARY
        end_marker = markers.END_SUMMARY
    elif markers.START_UPDATE_QUEUE in input_string:
        start_marker = markers.START_UPDATE_QUEUE
        end_marker = markers.END_UPDATE_QUEUE

    else: 
        if datastore.next_step == states.UNINITIALIZED:
            action = {
                "command": constants.ACTION_FOLLOWUP,
                "message": {
                    "role":"user",
                    "content": messages.app_files_not_defined
                    }
                }
        else:
            action = {
                "command": constants.ACTION_FOLLOWUP,
                "message": {
                    "role":"user",
                    "content": messages.code_not_found
                    }
                }

        logging.info(f"State:{datastore.next_step} \nno code found in response, informing LLM: {action['command']}")

 #         logging.info("We will try to parse the input fully and see if that works")
        #  if 
        #  try:
        #      logging.info("code block marker missing...checking entire input for app_files")
        #      datastore.update_queue = extract_app_files(input_string)
        #      datastore.next_step = states.APPFILES_DEFINED
        #      logging.info("Found app_files JSON")
        #      action = {
        #          "command": constants.ACTION_FOLLOWUP,
        #          "message": {
        #              "role":"user",
        #              "content": "please only write " + datastore.update_queue[0] + ". Please add descriptive comments in all the code you write." + " Note: " +  messages.how_to_write_code 
        #              }
        #      }
        #  except Exception as e:
        #      logging.info(e)
        #      logging.info("unable to find app_files json")
    if start_marker != "UNDEFINED":
        content_start = input_string.find(start_marker) + len(start_marker)

        # Find the end of the line to remove the language name
        first_new_line = input_string.find("\n", content_start)

        # Find the end of the code block
        content_end = input_string.find(end_marker, content_start)
        content = input_string[first_new_line + 1:content_end].strip()  # +1 to skip the newline
       
        if datastore.next_step == states.PENDING_UPDATE_QUEUE:
            datastore.update_queue = extract_update_files(content)
            logging.info("found update_files moving on")
            action = {
                    "command": constants.ACTION_FOLLOWUP,
                    "message": {
                        "role":"user",
                        "content": "update_files successfully defined. Please only write " + datastore.update_queue[0] \
                                + " \n " + messages.how_to_write_code.replace("FILE_PATH", datastore.update_queue[0] )
                        }
            }
            datastore.next_step = states.PENDING_CODE_WRITE

        #  if datastore.next_step == states.PENDING_UPDATE_QUEUE:
        #      datastore.update_queue = extract_update_files(content)
        #      logging.info("found app_files moving on")
        #      action = {
        #              "command": constants.ACTION_FOLLOWUP,
        #              "message": {
        #                  "role":"user",
        #                  "content": "update_files successfully defined. Please explain what changes you will make to these files"
        #                  }
        #      }
        #      datastore.next_step = states.PENDING_UPDATE_DESCRIPTION

        elif datastore.next_step != states.UNINITIALIZED:
            try:
                file_path = get_file_path(content)
                if start_marker == markers.START_SUMMARY:
                    file_path = file_path.split(".")[0] + ".llm.md"
            except Exception as e:
                logging.info(e)
                logging.info('no file path was found, using the top file on app_info if it exists')
                # file_path = datastore.update_queue[0]
                action = {
                        "command": constants.ACTION_FOLLOWUP,
                        "message": {
                            "role":"user",
                            "content": "No file path was found at the top of the the code block, please only re-write " + datastore.update_queue[0] \
                                    + ". Remember to use the correct format for the code block. The following is the incorrect code you provided: " \
                                    + content + ". Ensure the absolut path of the file is placed in the top on of the code block." \
                            }
                    }
                return action
            
            create_file(file_path,content)
            
            # no need to scan if this is a summary file
            if "md" in file_path:
                report = constants.SCAN_SUCCESS
            else:
                report = scan_file(file_path)
            
            logging.info("scan step completed")
            logging.info(report)
   
            if report == constants.SCAN_SUCCESS:
                print(f'scan succeeded for {file_path}')
                if file_path in datastore.update_queue:
                    datastore.update_queue.remove(file_path)
                datastore.done_queue.append(file_path)
                
#          #       # have LLM summarize file for resume capability later on
                #  if ".rb" in file_path: 
                #      action = {
                #          "command": constants.ACTION_FOLLOWUP,
                #          "message": {
                #              "role":"user",
                #              "content": "please write a summary of the code you just wrote." + "\n"+ messages.how_to_write_summary.replace("FILE_PATH", file_path.split(".")[0] + ".llm.md")
                #              }
                #      }
                    #  datastore.next_step = states.PENDING_SUMMARY_WRITE

                #el
                if len(datastore.update_queue) > 0:
                    action = {
                        "command": constants.ACTION_FOLLOWUP,
                        "message": {
                            "role":"user",
                            "content": "please only write " + datastore.update_queue[0] + ". Please add descriptive comments in all the code you write." \
                                    + " Note: " +  messages.how_to_write_code.replace("FILE_PATH", datastore.update_queue[0])

                            }
                    }
                    datastore.next_step = states.PENDING_CODE_WRITE
                else: 
                    action = {
                        "command": constants.ACTION_NOOP,
                        "message": {
                            "role":"user",
                            "content": "Well done, you have completed the requested task. Please await further instructions." #+ " Note: " +  messages.how_to_write_code 
                            }
                    }

            else:
                print(f'scan failed for {file_path}')
                logging.info("----Scan Fail----")
                logging.info(f"datastore file {datastore.update_queue[0]}")
                logging.info(report)
                logging.info("----/Scan Fail/----")
                action = {
                    "command": constants.ACTION_FOLLOWUP,
                    "message": {
                        "role":"user",
                        "content": "Linter has detected an issue in the code for " + datastore.update_queue[0] + " please correct the problem and rewrite the file. Bug report: " + report \
                                + " \n " + messages.how_to_write_code.replace("FILE_PATH", datastore.update_queue[0] )
                        }
                }

        else:
            logging.info("detected json, extracting app_files")
            datastore.update_queue = extract_app_files(content)
            logging.info("found app_files moving on")
            datastore.next_step = states.APPFILES_DEFINED
            action = {
                    "command": constants.ACTION_FOLLOWUP,
                    "message": {
                        "role":"user",
                        "content": "app_files successfully defined. Please only write " + datastore.update_queue[0] \
                                + " \n " + messages.how_to_write_code.replace("FILE_PATH", datastore.update_queue[0] )
                        }
            }
            datastore.next_step = states.PENDING_CODE_WRITE

    return action



def read_files(dir_path: str):
    for path in glob.iglob(f'{dir_path}/**', recursive=True):
        if path.endswith(('.rb', '.erb', '.html', '.md')):
            with open(path, 'r') as file:
                content = file.read()
                yield path, content 

def fetch_code_blocks(files):
    code_base = ""
    for path, content in files:
        filename = Path(path)
        code_base+=(f"```\n# {filename}\n{content}```\n")
    return code_base

def load_description(file_path):
    if not os.path.isfile(file_path):
        print(f"{file_path} is not a valid file.")
        sys.exit(1)

    print("Loading project description...")
    with open(file_path) as file:
        content = file.read()
        return content


# read the files from the stored app_files structure
def read_app_files():
      with open(f"/app/{datastore.app_name}/app_files.json","r") as file:
            app_files = file.read()
            
            app_files = json.loads(app_files)["app_files"]
            if len(app_files) > 0:
                datastore.app_files = app_files
                for app_file_path in datastore.app_files:
                    with open(app_file_path,"r") as app_file:
                        content = app_file.read()
                        yield app_file_path, content 
            else:
                raise Exception("could not load app_files")


def load_code(dir_path):

    # if app_fies exists then read only the files from this structure
    if os.path.isfile(f"/app/{datastore.app_name}/app_files.json"):
        files = read_app_files()
    else:
        if not os.path.isdir(dir_path):
            print(f"{dir_path} is not a valid directory.")
            sys.exit(1)

        print("Loading source code files...")
        files = read_files(dir_path)
    
    return fetch_code_blocks(files)


def load_code_from_list(file_list):

    code_block = ""
    for file in file_list:
        if not os.path.isfile(file):
            code = "FILE_DOES_NOT_EXIST"

        else:
            with open(file) as file_content:
                code = file_content.read()

        code_block += markers.START_CODE_RESPONSE + " \n # " + file + " \n " + code + " \n " + markers.END_CODE_RESPONSE + " \n "
    
    return code_block

