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

# What's next

- once the initial code is written there are likely tons of changes that you will want to make or possibly additions you want made.
  The next step to this project is to create a basic process for the developer to indicate what they would like to do with a specific file and have the LLM only address that change.
  Some of the logic needs to change to allow single file updates outside the context of the initial file list. This has yet to be worked in.
  Alternatively the developer may want to add a feature set that touches several files. This means a new iteration of the initial approach should be performed where the LLM is asked to enumerate
  the files that will be necessary to write or update in order for the new feature to be created. This would then be used to help track and guide it through the iteration.

# Docker

The Dockerfile should build an image capable of running this code and starting a rails server...
