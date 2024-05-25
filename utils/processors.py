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


def get_file_path(code):
    """
    Extracts a file path from various comment formats at the beginning of the provided code block.
 
    Parameters:
        code (str): A string containing the content of a file or code block.
 
    Returns:
        str: The extracted file path if found, otherwise raises an exception.
    """
    # Regular expression pattern to match a file path in various comment formats
    pattern = re.compile(r"^\s*(?:[<!%\-]*)\s*#\s*(.*/[\w/.\-]+)", re.MULTILINE)
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

def scan_file(file_path,language):

    if language == constants.LANGUAGE_RUBY:
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
            logging.info(e.output)
            logging.info("==============")
            return e.output
    elif language == constants.LANGUAGE_HTML or language == constants.LANGUAGE_ERB:
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

    # Extract the content within triple-ticked code block
    # Find the start of the triple-ticked block
    start_marker = "```"
    end_marker = "```"
    action = {
            "command": constants.ACTION_NOOP
            }
    if not start_marker in input_string:
        if datastore.state == constants.STATE_UNINITIALIZED:
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

        logging.info(f"no code found in response, informing LLM: {action['command']}")

        logging.info("We will try to parse the input fully and see if that works")
        try:
            logging.info("code block marker missing...checking entire input for app_files")
            datastore.update_queue = extract_app_files(input_string)
            datastore.state = constants.STATE_APPFILES_DEFINED
            logging.info("Found app_files JSON")
            action = {
                "command": constants.ACTION_FOLLOWUP,
                "message": {
                    "role":"user",
                    "content": "please only write " + datastore.update_queue[0] + " Note: " +  messages.how_to_write_code 
                    }
            }
        except Exception as e:
            logging.info(e)
            logging.info("unable to find app_files json")

    else:
        content_start = input_string.find(start_marker) + len(start_marker)

        # Find the end of the line to remove the language name
        first_new_line = input_string.find("\n", content_start)
        language = input_string[content_start:first_new_line].strip()

        # Find the end of the code block
        content_end = input_string.find(end_marker, content_start)
        content = input_string[first_new_line + 1:content_end].strip()  # +1 to skip the newline
        
        if language.lower() != "json":
            try:
                file_path = get_file_path(content)
            except:
                logging.info('no file path was found, using the top file on app_info if it exists')
                # file_path = datastore.update_queue[0]
                action = {
                        "command": constants.ACTION_FOLLOWUP,
                        "message": {
                            "role":"user",
                            "content": "No file path was found at the top of the the code block, please only write " + datastore.update_queue[0] \
                                    + ". Please add descriptive comments in all the code you write."  +  messages.how_to_write_code 
                            }
                    }
                return action
            
            create_file(file_path,content)
            
            # no need to scan if this is a summary file
            if "md" in file_path:
                report = constants.SCAN_SUCCESS
            else:
                report = scan_file(file_path,language)

   
            if report == constants.SCAN_SUCCESS:
                print(f'scan succeeded for {file_path}')
                if file_path in datastore.update_queue:
                    datastore.update_queue.remove(file_path)
                datastore.done_queue.append(file_path)
                
        #       # have LLM summarize file for resume capability later on
                if ".rb" in file_path: 
                    action = {
                        "command": constants.ACTION_FOLLOWUP,
                        "message": {
                            "role":"user",
                            "content": "please summarize what this file does in a file called " + file_path.split(".")[0] + ".llm.md"
                            }
                    }

                elif len(datastore.update_queue) > 0:
                    datastore.state=constants.STATE_COMPLETED_FIRST_ROUND
                    action = {
                        "command": constants.ACTION_FOLLOWUP,
                        "message": {
                            "role":"user",
                            "content": "please only write " + datastore.update_queue[0] + ". Please add descriptive comments in all the code you write." #+ " Note: " +  messages.how_to_write_code 
                            }
                    }
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
                        "content": "Linter has detected an issue in the code for " + datastore.update_queue[0] + " please correct the problem and rewrite the file. Bug report: " + report 
                        }
                }

        else:
            extract_app_files(content)
            logging.info("attempting to find app_files info inside codeblock")
            datastore.state = constants.STATE_APPFILES_DEFINED

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
            datastore.app_files = json.loads(app_files)
            for app_file_path in datastore.app_files["app_files"]:
                with open(app_file_path,"r") as app_file:
                    content = app_file.read()
                    yield app_file_path, content 



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
