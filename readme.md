# Stairway to Salesforce

[![CI](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml/badge.svg)](https://github.com/SFXD/stairway-to-salesforce/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/SFXD/stairway-to-salesforce/branch/main/graph/badge.svg)](https://codecov.io/gh/SFXD/stairway-to-salesforce)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/SFXD/stairway-to-salesforce)](LICENSE)

# Description
Stairway to Salesforce is simple ETL Python Framework dedicated to Salesforce, built on top of the DLT library. DLT handles data (extract/normalize/transform/load) with predefined system connectors (source/destination) and tools (credential/performance tweaks/...).  Applied to Salesforce, a few components were missing, such as proper Bulk2 connectors or a Salesforce Key Resolver (converting an external id values into a Salesforce ID to be send through the Bulk2 API).

Notes: Salesforce interactions is built with the python library simple-salesforce.

## What is dlt?  (from the official documentation)
dlt is an open-source Python library that loads data from various, often messy data sources into well-structured datasets. It provides lightweight Python interfaces to extract, load, inspect and transform the data. dlt and the dlt docs are built ground up to be used with LLMs: LLM-native workflow will take you pipeline code to data in a notebook for over 5,000 sources.

dlt is designed to be easy to use, flexible, and scalable:
- dlt extracts data from REST APIs, SQL databases, cloud storage, Python data structures, and many more
- dlt infers schemas and data types, normalizes the data, and handles nested data structures.
- dlt supports a variety of popular destinations and has an interface to add custom destinations to create reverse ETL pipelines.
- dlt automates pipeline maintenance with incremental loading, schema evolution, and schema and data contracts.
- dlt supports Python and SQL data access, transformations and supports pipeline inspection and visualizing data in Marimo Notebooks.
- dlt can be deployed anywhere Python runs, be it on Airflow, serverless functions, or any other cloud deployment of your choice.

Official DLT documentation can be found https://dlthub.com/docs/intro 

## Content overview
- Pipeline Samples in "pipelines" folder
- unit tests in "tests" folder
- framework components in "dlt_salesforce_advanced" folder
    - Sources with Salesforce Bulk2    
    - Destinations with Salesforce Bulk2
    - Drivers with Salesforce Driver used by the components
    - components with a base pipeline and Salesforce Key Resolver

## Content details
- Salesforce Bulk2 as source
- Salesforce Bulk2 as destination with the following capacities
    - insert :  write_disposition = "append"  / x-salesforce-operation = "insert"
    - upsert :  write_disposition = "append"  / x-salesforce-operation = "upsert" / primary_key = "<required>"
    - delete :  write_disposition = "append"  / x-salesforce-operation = "delete" / primary_key = "<required>"
        for an optimized pipeline, the primary_key should Id, as Salesforce Bulk2 does not support deletion on external Id
        if the primary key is not "Id", a query will be performed to convert the external id into a Salesforce Id. 
    - replace : write_disposition = "replace"
        the entiere sobject records will deleted ( Query + delete) and the given data will be inserted.
        To avoid if the source system can transmit incremental update, as it's consuming additional resources (especially with a large data volume) and preventing any historic in Salesforce
- SalesforceKeyResolver as component
    - resolve an External Key as a Salesforce Id -  useful for lookup
- Base pipeline as component

# Installation
## Python setup
- Make sure you have Python and pip 
python --version
pip --version

- Install UV ( modern environment manager )
C:\> pip3 install -U pip
C:\> pip3 install uv

- TO BE CONFIRMED - Installation of tzdata
run scripts/download_tzdata.py   to download tzdata in the folder "Downloads" of your user.  (Requirement for pyArrow conversion)

- Get the sources
- Setup python env with uv sync
- Check the pipeline folder for the samples
- Add new source/destination connectors from DLT
uv add dlt[<Connector name>]  
Example : uv add dlt[postgres]

## Environments
You will probably not test your scripts against your production environments. Environments are defined through suffix in credentials, for instance salesforce.dev, salesforce.production, postgres.dev, postgres.production,.... 
dev environment is the default one if none is precised when running the pipeline. You can define any environment as long as the credentials matchs the pipeline parameter.

## Credentials
DLT will check for the credential in environment variables, then in secret.toml (within a subfolder .dlt).
In the repo, the .dlt folder contains a secrets_sample file, with sample credentials used by the sample pipeline.  To activate it, you should rename it as secrets.toml. 

Regarding Salesforce credentials, you can choose the connection flow and setup the required attributes as defined in dlt_salesforce_advanced\drivers\salesforce_driver\sfdriver_specs.py
In the sample, we are using a connected app with a client credentials.


# Sample pipelines
To illustrate the possibilities, a few samples have been defined. 
All the samples are using the BasePipeline components and have the following logic : 
- Step 1: Init Pipeline
- Step 2: Source
- Step 3: Transform
- Step 4: Destination
- Step 5: Execution
It can be adjust to your needs or preferences

## sample_sync_account_sf_to_postgres
Sample showing the synchronisation of the update accounts (based on LastModifiedDate) from Salesforce to postgres. 
Principles:
- Incremental synchronisation 
- Salesforce Bulk2 as source
- Transform between Source and destination with a simple field mapping
- Postgres as destination

Notes on the postgres destination:
- For sample purpose, the postgres connector is included. It was addded through the command uv add dlt[postgres] and can be removed through uv remove dlt[postgres]
- Official postgres destination documentation : https://dlthub.com/docs/dlt-ecosystem/destinations/postgres
- The synchonisation state is directly handled by the destination postgres ( and stored within the postgres database).

## sample_upsert_contact_csv_sf
Sample showing the loading of data from a csv file into upserting salesforce contacts
Principles:
- Base pipeline with csv path
- filesystem as source
- Transform with field mapping
- Salesforce Key Resolver to resolve External_Id__c into a proper Salesforce ID ( for the parent account )
- Salesforce Bulk2 as destination for an upsert operation

## sample_delete_contact_csv_sf.py
Sample showing the deletion of contacts from a csv file containing Contact emails
Principles: 
- Base pipeline with csv path
- filesystem as source
- Salesforce Bulk2 as destination for a delete operation with automatic key resolution ( with the Salesforce Key Resolver under the hood)

## sample_replace_fixedrecord_csv_sf
Sample showing the replace operation, meaning deleting all records and creating them
Principles:
- Base pipeline with csv path
- fileystem as source
- Salesforce Bulk2 as destination for a replace operation

# Work with pipelines
## Run pipeline
Base commande to run the pipeline : uv run pipelines\<pipeline name>.py 
Environment can be specified: uv run pipelines\<pipeline name>.py --env dev
Filepath can be specified if your pipeline read or write data from a csv file : uv run pipelines\<pipeline name>.py "file_path"

## Drop pipeline ( to reset the state for instance )
dlt pipeline sample_sync_account_sf_to_postgres drop

## State of the pipeline
States are stored as file by default in your <user>\.dlt\pipelines\
A hard reset can done by deleting the pipeline specific subfolder. 

# Unit tests
## Run pipeline tests
uv run --with pytest pytest tests/pipelines/ -cov-report=term

## Run framework tests
uv run --with pytest pytest tests/unit/ --cov=dlt_salesforce_advanced --cov-report=term

## View coverage
uv run --with pytest pytest start htmlcov/index.html
