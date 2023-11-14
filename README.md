# salesforce-datacloud-utils
Simple utility functions for calling the Salesforce Data Cloud APIs, specifically the Ingest API and Query APIv2.

## Overview

This package provides a basic REST API wrapper around the Salesforce Data Cloud API.  To use:

### Create a new instance of the SalesforceDataCloud class

```python
from salesforce_datacloud_utils import SalesforceDataCloud
sfdc=SalesforceDataCloud()
```

### Upstert Date via Streaming Ingest API
Example: `sample_streaming_upsert.py`

```python
def streaming_upsert(self, source_api_name: str, source_object_name: str, data: object, test_mode: bool=False)
```
Upsert one or more rows of data via Streaming Ingest API

* source_api_name (str): Name of the Ingest API data connector
* source_object_name (str): Name of the resource type to send to Data Cloud
* data (str): Array of dicts with one dict per row
* test_mode (bool): Validate payload only (default: false)

Returns the response object from the API call

### Upstert Date via Bulk Ingest API
Example: `sample_bulk_upsert.py`

```python
def bulk_upsert(self, source_api_name: str, source_object_name: str, data_file_paths: Iterable)
```
Upsert one or more files of data via Bulk Ingest API

* source_api_name (str): Name of the Ingest API data connector
* source_object_name (str): Name of the resource type to send to Data Cloud
* data_file_paths (iter): Iterable that emits a list of file paths for upload

Returns the response object from the API call

### Delete Date via Bulk Ingest API
Example: `sample_bulk_delete.py`

```python
def bulk_delete(self, source_api_name: str, source_object_name: str, data_file_paths: Iterable)
```
Delete rows via the Bulk API that match the identifiers contained in one or more files

* source_api_name (str): Name of the Ingest API data connector
* source_object_name (str): Name of the resource type to send to Data Cloud
* data_file_paths (iter): Iterable that emits a list of file paths for upload

Returns the response object from the API call

### Query data


### View or terminate bulk jobs


### CLI Usage Notes
A subset of functions are exposed via CLI to enable you to monitor and terminate active jobs if required.

```console
usage: python3 salesforce_datacloud_utils.py [-h] [--command {list_active_jobs,list_all_jobs,job_info,abort_job}] [--job_id JOB_ID]

Utility functions for the Data Cloud API

Command Line Functions:
- list_active_jobs: (default action) Show jobs with status "Open,UploadComplete,InProgress"
- list_all_jobs: Show all jobs
- job_info: Show detailed information for the specified job
- abort_job: Terminate the specified job with state "Aborted"
        

optional arguments:
  -h, --help            show this help message and exit
  --command {list_active_jobs,list_all_jobs,job_info,abort_job}
                        Select the operation to execute
  --job_id JOB_ID       The job id returned in the response body from the Create Job request.
```


## Pre-requisites

### Configure Data Cloud Connected App and OAuth Certificates
Authorization is via JWT and requires the following to be carried out:
* [Create a Private Key and Self-Signed Digital Certificate](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_key_and_cert.htm) - the Privte Key (server.key) file here will be used by the scrips and the Certificate (server.crt) will be passed to the Connected App configuration..
* [Create a Connected App for Data Cloud Ingestion API](https://help.salesforce.com/s/articleView?id=sf.connected_app_create_api_integration.htm&type=5) - configure this for JWT OAuth flow by uploading the Digital Signature file (server.crt) generated above.  Ensure that you enable the following access scopes: 

  * Access interaction API resources (interaction_api)
  * Access all Data Cloud API resources (cdp_api)
  * Manage Data Cloud Ingestion API data (cdp_ingest_api)
  * Manage Data Cloud Profile data (cdp_profile_api)
  * Manage user data via APIs (api)
  * Perform ANSI SQL Queries on Data Cloud data (cdp_query_api)
  * Perform requests on your behalf at any time (refresh_token, offline_access)

* [Pre-Authorize User App Access Through Connected App Policies](https://help.salesforce.com/s/articleView?id=sf.branded_apps_allow_deny_con_app.htm&type=5) - Ensure that "Admin approved users are pre-authorised" is selected under OAuth policies.  After selecting this option, manage profiles for the app by editing each profile’s Connected App Access list. Or manage permission sets for the app by editing each permission set’s Assigned Connected App list.

### Configure Ingest API
If you are inserting or deleting data via the Ingest API then execute the followng steps:
* [Set Up Ingestion API Connector](https://help.salesforce.com/s/articleView?id=sf.c360_a_connect_an_ingestion_source.htm&type=5) - As an admin in Data Cloud, set up an Ingestion API connector source and define the schema for input objects.
* [Create an Ingestion API Data Stream](https://help.salesforce.com/s/articleView?id=sf.c360_a_create_ingestion_data_stream.htm&type=5) - This step defines the Data Lake Objects that the data streams will write to inside Data Cloud.  After the data streams are deployed, you can make calls to the object endpoints to send data into Data Cloud.

### Install Required Python Libraries

* Recommended: Create a virtual python environment:
```console
mkdir .venv
python3 -m venv .venv
source .venv/bin/activate
```

* Install the required Python libraries:
```console
python3 -m pip install --upgrade pip
pip install filesplit PyJWT python-dotenv requests urllib3 pandas
```

### Configure Environment Variables

Configure the following as environment variables or write to a .env file in the installation directory:

* clientId - [The Consumer Key](https://help.salesforce.com/s/articleView?id=sf.connected_app_rotate_consumer_details.htm&type=5) from the connected app that was configured in Salesforce above
* privateKeyFile - Path to the Private Key file generated above (server.key)
* userName - The pre-authorised salesforce user that will be used for API access
* tempDir - Directory for creating temporary files during execution
* inputFileEncoding - Optional: Specifies the encoding of the source files that will be uploaded via the IngestAPI (e.g. utf-8)


