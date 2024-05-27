## 27-05-2023

- moved states to states module and made them strings for easy debugging
- update logic still in the works...user vs system messages is a bit confusing and there is much loopiness in the code, need to modularize and use some sort of state machine to organize the logic. as always, the model itself is what governs the quality of the experience and the nuances of each model are very hard to map out fully...inderterministic behavior causes lots of grief

## 26-05-2023

Large rewrite...

- use more modules for storing constant names
- create a specific template format for code to be communicated back from LLM because of hokey behavior with triple tick format
- history is not sent entirely to LLM, just the last response and the overarching goal of the interaction, the file list and what to do next
- TODO: updating the resume/update commands to match the new setup. This will require understanding from the user what they want to change, and from the LLM how it proposes to do so. These then need to be somehow maintained across the interactions thereafter as is done with the creation process.
- some erblint checks disabled to reduce LLM confusion (like html tag termination style)

## 25-05-2023

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
