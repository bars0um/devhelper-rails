import utils.markers as markers
import json
import logging
import utils.datastore as datastore
import re
import os

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
        pattern = re.compile(r"^\s*(?:[<!%\-]*)\s*//*\s*(.*\/[\w\/.\-]+)", re.MULTILINE)
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


def extract(start_marker,end_marker,input_string):
   
    content_start = input_string.find(start_marker) + len(start_marker)

    # Find the end of the line to remove the language name
    first_new_line = input_string.find("\n", content_start)

    # Find the end of the code block
    content_end = input_string.find(end_marker, content_start)
    content = input_string[first_new_line + 1:content_end].strip()  # +1 to skip the newline

    return content

def extract_epic_files(data):
    
    plain_data = extract(markers.START_APPFILES,markers.END_APPFILES,data)
    # Parse JSON data
    json_data = json.loads(plain_data)
    logging.info(f"data: {data} ")
    
    # Extract file paths from the list and store them in a new list
    if "app_files" not in json_data:
        raise Exception("No app files could be extracted")
    
    # TODO: check changes to app_files.sjon
    with open(f"/app/{datastore.app_name}/app_files.json","w") as file:
        file.write(plain_data)

    logging.info(f"app_files extracted and written to app_files.json")
    
    return json_data["app_files"]

def remove_triple_ticks(code):

    cleaned_text = re.sub(r'```[a-z]*\n([\s\S]*?)```', r'\1', code)
    
    return cleaned_text

def extract_and_save_code_to_filepath_in_comments(input_string):
    
    print("extract_and_save_code_to_filepath called")
    if not markers.START_CODE_RESPONSE in input_string or not markers.END_CODE_RESPONSE in input_string:
        raise Exception("Missing START_CODE_RESPONSE and END_CODE_RESPONSE markers")
    code = extract(markers.START_CODE_RESPONSE,markers.END_CODE_RESPONSE,input_string)
    code = remove_triple_ticks(code)
    file_path = get_file_path(input_string)
    create_file(file_path,code)
    
    return file_path

def strip_comments(text):
   lines = text.split('\n')
   stripped_lines = []
   for line in lines:
       if '//' in line:
           line = line[:line.index('//')]
       stripped_lines.append(line)
   return '\n'.join(stripped_lines)

def extract_update_files(data):
    
    data = strip_comments(data)
    plain_data = extract(markers.START_UPDATE_QUEUE,markers.END_UPDATE_QUEUE,data)
    # Parse JSON data
    logging.info("extracting update files: plain_data")
    logging.info(plain_data)
    json_data = json.loads(plain_data)
    logging.info(f"update files data: {data} ")
    update_list = []
    
    # Extract file paths from the list and store them in a new list
    if "update_files" in json_data:
        for file in json_data["update_files"]:
            if any(re.findall(r'mp3|png|jpg|jpeg|node_modules',file,re.IGNORECASE)):
                continue
            else:
                update_list.append(file)
    elif "create_and_update_files" in json_data:
        for file in json_data["create_and_update_files"]:
            if any(re.findall(r'mp3|png|jpg|jpeg|node_modules',file,re.IGNORECASE)):
                continue
            else:
                update_list.append(file)
    else: 

        raise Exception("No update files could be extracted")

    return update_list

def extract_task_relevant_files(data):
    plain_data = extract(markers.READ_FILES,markers.END_READ_FILES,data)
    # Parse JSON data
    json_data = json.loads(plain_data)
    logging.info(f"read files data: {data} ")
    
    # Extract file paths from the list and store them in a new list
    if "task_files" not in json_data:
        raise Exception("No update files could be extracted")
        
    return json_data["task_files"]
