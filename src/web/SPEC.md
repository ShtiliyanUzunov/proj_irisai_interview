# Project Context

This is a web service, that should rely only on the django-rest framework for endpoint implementation.
The service handles requests related to the classification of research articles based on their subject + abstract.
The service has two major dependencies - BERT based models for classification. 

## PROJECT CONFIGURATION
    All variables, and configurations should be implemented using a .env file that should sit on a root level of the project.
    


## REST ENDPOINTS
    To handle such requirements we have to implement a task-based API. 
    The API design should be able to handle multiple requests as once, should be responsive and scalable.
    - Task allocation endpoint Specs:
    This endpoint should allocate a task, the task allocation API should take as params list of objects, 
    each object should contain subject + abstract fields. And should return a task ID. Once task is created it should be added to a queue of tasks.
    We have to keep the order of the requests - meaning if client 1 creates a task at time T, and client 2 creates a task at time T+1, the task of
    client 1 should be submitted for execution before the task of client 2.

    - Task result endpoint specs:
    This endpoint should take as input the task ID, and should return the status of the task. 
    We have 3 types of tasks - [NOT STARTED, IN PROGRESS, FINISHED]. For the FINISHED tasks - also return the result as part of the body.
    The return respone should indicate if the result is fetched from the cache or not. The field should be called fromCache: boolean.

    - Queue status endpoint:
    This should return the status of the queue with the IDs, and their execution order.

## LOGGING
    The service uses logs to track activity. The logs should be placed in a file that's configured through the .env file.
    Use "LOG_DIR" as key in the .env to determine where the logs should be placed.

## Caching 
    To prevent double calculation of the same object we have a semantic cache. The semantic cache acts as follows:
    - When a new request comes for computation in the prediction pipeline, it calculates embeddings for the input
    - After an embedding is created it compares the embedding with the existing embeddings in its internal storage. 
    - To do embedding comparison use cosine similarity as method of choice. The threshold should be configured in the .env file through the CACHE_THRESHOLD variable. Variable should be between 0 and 1. 0.95 default value.
    - If a given target embedding is matched, the cache should returns result, without using the prediciton pipeline.