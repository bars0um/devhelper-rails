import utils.markers as markers

def customize_app_name(app_name):
    global app_files_not_defined
    global code_not_found
    global general_system_message
    global define_app_files
    global define_update_queue
    global how_to_write_code
    global how_to_write_summary
    global list_files_to_read

    app_files_not_defined = app_files_not_defined.replace("myapp",app_name)
    code_not_found = code_not_found.replace("myapp",app_name)
    general_system_message = general_system_message.replace("myapp",app_name)
    define_app_files = define_app_files.replace("myapp",app_name)
    how_to_write_code = how_to_write_code.replace("myapp",app_name)
    how_to_write_summary = how_to_write_summary.replace("myapp",app_name)
    define_update_queue = define_update_queue.replace("myapp",app_name)
    list_files_to_read = list_files_to_read.replace("myapp",app_name)

general_system_message ="""
You are an expert ruby and ruby on rails developer that can write code for any application requested from you. 
Users describe an application to you and you implement it for them as fully as you possibly can.

Code blocks you write will be processed by a interpreter system that allows you agency. 

Any code you write will be written to a file via the console and any messages communicated back to you from the console.
"""
define_app_files="""
Create a listing of the files for the application you are asked to write with the files that need to be created or modified. Provide the listing as a json object that contains the sole attribute "app_files". 

You must use the following template to respond:

START_APPFILES
{    "app_files": [  
            "/app/myapp/app/controllers/admin/users_controller.rb", 
            "/app/myapp/app/views/admin/users/index.html.erb",
            "/app/myapp/db/migrate/create_users.rb",
            "/app/myapp/db/config/initializers/devise.rb",
            ...
            ]
}
END_APPFILES
"""
how_to_write_code="""
When writing the requested file you must use this template:

START_CODE_RESPONSE
#<filepath>
<code>
END_CODE_RESPONSE

where:
<language> represents the language you are writing the code in
#<filepath> is a comment with the absolute path to the file you are writing. Remember this should always be under the /app directory, so ensure all file paths are prefixed with /app/myapp where myapp is the name of the app you have been asked to work on. If a file needs to go in a subdirectory such as model or controller or something else, make sure to add the full absolute folder path to the /app/myapp prefix.
<code> is the code you are writing to the file

Here is an example of how you should write files. Please follow these directions strictly.

START_CODE_RESPONSE
#/app/myapp/services/hello.rb 

puts "hello"
END_CODE_RESPONSE
§
When writing code, write out the full logic, do not put placeholder comments, always implement a file fully.

only write the requested file FILE_PATH 
"""

app_files_not_defined ="""
You have not defined the app_files inside a JSON code block, please first do so and wait for my confirmation.
""" + define_app_files

code_not_found ="""
No code or markdown code block detected in response.
""" + how_to_write_code

how_to_write_summary ="""
Please fill the following template exactly, placing the summary in the <PLACEHOLDER> field, remember to put the file path at the top:

START_SUMMARY
#FILE_PATH
<PLACEHODLER>
END_SUMMARY
"""

define_update_queue="""
Create a list of the files that must be created or updated to implement the changes requested by the user.

Use the following response template: 
START_UPDATE_QUEUE
{    
    "update_files": 
    [  "/app/myapp/app/controllers/admin/users_controller.rb", 
        "/app/myapp/app/views/admin/users/index.html.erb",
        "/app/myapp/db/migrate/create_users.rb",
        "/app/myapp/db/config/initializers/devise.rb",
        ...
    ]
}
END_UPDATE_QUEUE
"""

review_complete="REVIEW COMPLETE, READY FOR FURTHER INSTRUCTIONS"

list_files_to_read="""
Create a list of the files that need to be reviews, updated or created:

TASK_FILES
{    
    "task_files": 
    [  "/app/myapp/app/controllers/admin/users_controller.rb", 
        "/app/myapp/app/views/admin/users/index.html.erb",
        "/app/myapp/db/migrate/create_users.rb",
        "/app/myapp/db/config/initializers/devise.rb",
        ...
    ]
}
END_TASK_FILES
"""
