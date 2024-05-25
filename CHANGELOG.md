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
