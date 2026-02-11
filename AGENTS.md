## Project Context

The project works with the arXiv dataset from kaggle, and the goal is to build a classification 
system for the categories, by just using the paper abstracts. The classification will be approached on two stages

stage 1 - parent category classification.
stage 2 - subcategory classification.

The Dataset contains about 3 million samples. 
The classification pipeline should be trained locally, and should run locally.
Don't use external LLMs through APIs.



## Project Instructions

- Resource files that are going to be used in the pipeline should be placed in the /resources folder. (e.g. model weights, json files, etc.)
- The task definition is found in the Task.pdf file.
- Never update files on your own - send everything for Review. 
- Every change should be reviewed and accepted by the developer.
- The codebase runs on a Windows machine with Anaconda environment.

## Style Instructions

- Always use type hinting in .py files.