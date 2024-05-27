# DevHelper for Ruby on Rails

DevHelper for Ruby on Rails is an open source AI-based development assistant for Rails developers

This project is inspired by various projects including open-interpreter which astounded me with the numerous possible application of LLMs to various tasks.

This simple chat script assumes that you have oobabooga or an OpenAI compatible API at the end point defined in the url in stream-chat.py.

The model I found most simple to work with was the Nous Hermes II, other models might perform as well.

Important notes:

- to limit the chaos involved I forced temperature to 0
- to have some reference for determinisim I set some seed

# How this works

- This script simply takes your general description of an application that you would like written in Rails.
- It asks the LLM to list the files that it thinks it would need to write to achieve your request
- The file list it generates is stored and then fed to the LLM to be written one at a time
- each file that is written is passed through a linter for a basic sanity check, if it fails, the LLM is asked to review the linter output and re-write the code
- once all files have been created, the script pauses and a new phase of the development effort is at hand
  ...(to be continued)

Usage:

```
python3 -u stream-chat.py
```

## Starting a new project:

Simply start DevHelper and describe the project or application you want. It will then proceed to list the files that it will write and then write them.

If you have a project description, put it in a file and use the create instruction to make the LLM read it and plan the files to write:

```
%create /app/myapp/project.md mycoolapp
```

This should get the LLM to create an app_files json which will then be processed by the script and the LLM will be directed to create each file in sequence.

mycoolapp will be used to replace example texts in the llm instructions to ensure the LLM does not diverge unnecessarily.

## Resuming or modifying an existing project:

start the script and the enter the following:

```
%resume /app/folder/ mycoolapp
```

This will simply load all the code files in that folder (erb,rb,html) (from app_files.json) and provide it to the LLM for review.

```
%update _describe your update request here_
```

Will instruct the LLM to explain how it intends to do the change you request. And then guides it through doing that.

# Docker

The Dockerfile should build an image capable of running this code and starting a rails server...
