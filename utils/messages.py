app_files_not_defined ="""
You have not defined the app_files inside a JSON code block, please first do so and wait for my confirmation.
Create a listing of the files for the application.
Provide the listing as a json object that contains the sole attribute "app_files" inside a JSON code block. 
For example:
```json
{    "app_files": [  
            "/app/myapp/somefolder/file1.rb", 
            "/app/myapp/somefolder/file2.rb",
            ...
            ]
}
```
"""
code_not_found ="""
No code detected in response.

When writing code you must use this template:
```<language>
#<filepath>
<code>
```
where:
<language> represents the language you are writing the code in
#<filepath> is a comment with the absolute path to the file you are writing. 
Remember this should always be under the /app directory, so ensure all file paths are prefixed with /app/<app-name> where <app-name> is the name of the app you have been asked to work on. 

If a file needs to go in a subdirectory such as model or controller or something else, make sure to add the full absolute folder path to the /app/<app-name> prefix.
<code> is the code you are writing to the file
Here is an example of how you should write files. Please follow these directions strictly. 
```ruby
#/app/myapp/services/hello.rb
puts "hello"
``` 
"""
general_system_message ="""
You are an expert ruby and ruby on rails developer that can write code for any application requested from you. 
Users describe an application to you and you implement it for them as fully as you possibly can.

Code blocks you write will be processed by a interpreter system that allows you agency. 

Any code you write will be written to a file via the console and any messages communicated back to you from the console.
```
"""
define_app_files="""
Create a listing of the files for the application you are asked to write. Provide the listing as a json object that contains the sole attribute "app_files". 

You must use the following app_files format:

```json
{    "app_files": [  
        "/app/myapp/somefolder/file1.rb", 
        "/app/myapp/somefolder/file2.rb", 
        ...
        ]
}

"""
how_to_write_code="""
When writing code you must use this template:

```<language>
#<filepath>
<code>
```

where:
<language> represents the language you are writing the code in
#<filepath> is a comment with the absolute path to the file you are writing. Remember this should always be under the /app directory, so ensure all file paths are prefixed with /app/<app-name> where <app-name> is the name of the app you have been asked to work on. If a file needs to go in a subdirectory such as model or controller or something else, make sure to add the full absolute folder path to the /app/<app-name> prefix.
<code> is the code you are writing to the file

Here is an example of how you should write files. Please follow these directions strictly.

```ruby
#/app/myapp/services/hello.rb 

puts "hello"
```

please only write code, do not write text outside code block and do not add any notes to your responses.
"""
