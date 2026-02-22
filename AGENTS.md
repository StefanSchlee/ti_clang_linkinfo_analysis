# Project Description
I want to create a python analysis tool for the linkinfo.xml files, which are emitted by the texas instruments clang arm compiler.

# Folder structure
- Ignore the "dev_archive/", this are some old files from me.
- "example_files/": Here are some example linkinfo files, can be used to understand the file structure and for unit tests
  - Use the *debug* files
  - the dpl_demo* files are smaller projects, the enet_cli* files are larger projects

# How we develop together
- In the "requirements.md" file i describe all requirements for the project, like coding guidelines, feature requests etc.
  - I will add new requirements from time to time
  - You can suggest adding or modifying requirements for clarification
- I want you to keep track of the work in a "ticket-like" system using the "agents_tasklist.md":
  - Add necessary work packages in the file with checkmarks to keep track of work done
  - split large tasks into small manageable tasks, which will be done commit for commit
  - add references to my requirements
  - order the tasks to be done in a reasonable order
  - Delete fully-done tasks from the file
  - Update the file whenever necessary, like if new tasks arose or if a task is done
- I want you to create pytest tests, and run these after major modifications to see if all still works
- You are allowed to refactor and restructure the whole project whenever necessary

# Tools
- Use the local .venv for calling any python commands