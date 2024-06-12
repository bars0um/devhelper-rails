## 12-06-2024

- messages changed to accommodate js code instead of ruby - this is temporary and the plan is to make this more language agnostic
- allowed for more LLM behavioral issues treatment such as incorrect inferrred path for the file being written
- created two new flows:
  - %update %file to bring focus to a particular file but allow the LLM freedom in what updates to make to achieve the requested change (this is expected since files can have dependencies that need updating)
  - %modify to specifically address a particular file with no other changes expected
- curses panes used to separate the various aspects of the code:
  - An instructions pane showing the instructions sent.
  - A system pane to show messages concerning the flow
  - An LLM pane to show the response from the LLM
  - A user pane to show the user input

## 01-06-2024

- Update logic modified to use the task file list approach used in diagnosis workflow
- also added logic to detect non-conformance to code writing format and to highlight this as a "bug", bugs now being either actual syntax bugs or format of response.
- linter output seems a bit cryptic and does not always lead to the LLM correctly resolving the syntax issue

## 31-05-2024

- added diagnose capability. This is because you seldom get code that is fully functional out of the box. The point here is you run the resume command to load the current state of the project. You then pass the diagnose command along with the current error you see and the LLM is guided through resolving that error.

## 30-05-2024

- separated update message from epic and organized better the instruction queue with placeholders that are filtered out if they are set to None...this way we reuse the code writing process for creations and resume/update logic

## 29-05-2024

- completed re-write in main.py, code is cleaner and simpler to follow and extend. Diagrammed in README.md

## 28-05-2024

- rejigged code logic and placed it in main.py. Attempting to modularize and organize the code to fit within a simple but structured overall framework for determining user intent, conveying it to the LLM with the least divergence-causing setup.
- main.py is a reimplementation of what stream-chat.py has right now but in a more methodical manner...

## 27-05-2024

- moved states to states module and made them strings for easy debugging
- update logic still in the works...user vs system messages is a bit confusing and there is much loopiness in the code, need to modularize and use some sort of state machine to organize the logic. as always, the model itself is what governs the quality of the experience and the nuances of each model are very hard to map out fully...inderterministic behavior causes lots of grief

## 26-05-2024

Large rewrite...

- use more modules for storing constant names
- create a specific template format for code to be communicated back from LLM because of hokey behavior with triple tick format
- history is not sent entirely to LLM, just the last response and the overarching goal of the interaction, the file list and what to do next
- TODO: updating the resume/update commands to match the new setup. This will require understanding from the user what they want to change, and from the LLM how it proposes to do so. These then need to be somehow maintained across the interactions thereafter as is done with the creation process.
- some erblint checks disabled to reduce LLM confusion (like html tag termination style)

## 25-05-2024

Bug fixes:

- linter errors were not properly communicated to the LLM

Changes:

- update_queue now holds the files we expect the LLM to update for proper tracking
- LLM is asked to document every ruby file it writes

## 23-05-2024

- Resume command receives folder with code, code is stitched together into one large message and provided to LLM for review.
- Analyze command (only used after resume) asks the LLM to review project_description.md file and determine if there are gaps in implementation
- Update command (only used after analyze) asks LLM to implement its suggested changes from the Analyze command
- Create command reads project description from a file and configures app name. App name is used to replace placeholder `myapp` in instruction messages
- Write command instructs LLM to begin writing files assuming app_files has been populated
