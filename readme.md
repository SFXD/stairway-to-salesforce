## Description

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

## How to use it ?
# First installation
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

# Run a pipeline
uv run pipelines\<pipeline name>.py

# Run pipeline tests
uv run --with pytest pytest tests/pipelines/ -cov-report=term

## Working on the framework
# Run units tests
uv run --with pytest pytest tests/unit/ --cov=dlt_salesforce_advanced --cov-report=term

# View coverage
uv run --with pytest pytest start htmlcov/index.html
