import re
from pathlib import Path
import os
import utils.datastore as datastore
import json
import subprocess
import utils.constants as constants
import utils.messages as messages
import logging

def extract_app_files(data):

    # Parse JSON data
    data = json.loads(data)
    logging.info(f"data: {data} ")
    # Extract file paths from the list and store them in a new list
    if  data["app_files"]:
        datastore.app_files = data["app_files"]
        logging.info(f"app_files extracted: {datastore.app_files}")
    #  if not file_paths:
        #  raise ValueError("data not properly formulated, please review and try to fix.")

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
    pattern = re.compile(r"^\s*(?:[<!%\-]*)\s*#\s*(/[\w/.\-]+)", re.MULTILINE)
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

        except Exception as e:
            # Print the error if rubocop exits with a non-zero status
            logging.info("Scan Failed:")
            #  logging.info(e)
            logging.info("==============")
            logging.info(e.output)
            logging.info("==============")
            return e.output
    elif language == constants.LANGUAGE_HTML or language == constants.LANGUAGE_ERB:
        # Prepare the command to run rubocop
        command = ['erblint', file_path]
        
        # Execute the command
        try:
            # Run the command and capture the output
            result = subprocess.run(command, check=True, text=True, capture_output=True )
            # Print the stdout and stderr from rubocop
            logging.info("-------------------------------")
            logging.info(f"Erblint Output:\n {result.stdout}")
            logging.info("-------------------------------")

            if "No errors were found" in result.stdout:
                return constants.SCAN_SUCCESS

        except Exception as e:
            # Print the error if rubocop exits with a non-zero status
            logging.info("Scan Failed:")
            #  logging.info(e)
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
            extract_app_files(input_string)
            datastore.state = constants.STATE_APPFILES_DEFINED
            logging.info("Found app_files JSON")
            action = {
                "command": constants.ACTION_FOLLOWUP,
                "message": {
                    "role":"user",
                    "content": "please only write " + datastore.app_files[0] + " Note: " +  messages.how_to_write_code 
                    }
            }
        except:
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
                file_path = datastore.app_files[0]
            create_file(file_path,content)
            
            report = scan_file(file_path,language)

   
            if report == constants.SCAN_SUCCESS:
                print(f'scan succeeded for {file_path}')
                datastore.app_files.remove(file_path)
                datastore.done_files.append(file_path)
                
                logging.info("----Scan Sucess----")
                logging.info(report)
                logging.info("----/Scan Sucess/----")
                
                if len(datastore.app_files) > 0:
                    datastore.state=constants.STATE_COMPLETED_FIRST_ROUND
                    action = {
                        "command": constants.ACTION_FOLLOWUP,
                        "message": {
                            "role":"user",
                            "content": "please only write " + datastore.app_files[0] #+ " Note: " +  messages.how_to_write_code 
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
                logging.info(f"datastore file {datastore.app_files[0]}")
                logging.info(report)
                logging.info("----/Scan Fail/----")
                action = {
                    "command": constants.ACTION_FOLLOWUP,
                    "message": {
                        "role":"user",
                        "content": "Linter has detected an issue in the code for " + datastore.app_files[0] + " please correct the problem and rewrite the file. Bug report: " + report 
                        }
                }

        else:
            extract_app_files(content)
            datastore.state = constants.STATE_APPFILES_DEFINED

    return action
