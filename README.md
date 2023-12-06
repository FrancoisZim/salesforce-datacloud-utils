# salesforce-datacloud-utils
Simple utility functions for calling the Salesforce Data Cloud APIs, specifically the Ingest API and Query APIv2.

## Overview

This package provides a basic REST API wrapper around the Salesforce Data Cloud API to enable data query, upsert and delete as well as basic bulk job management.

## Usage

### Create a new instance of the SalesforceDataCloud class

Initialise an instance of the API handler:

```python
from salesforce_datacloud_utils import SalesforceDataCloud
sfdc=SalesforceDataCloud()
```

The following are typically be specified as environment variables or in a .env file 
but they can be overridden in the constructor if required:
* sf_login_url - Salesforce login URL - defaults to: "login.salesforce.com" if not specified.
* client_id - [The Consumer Key](https://help.salesforce.com/s/articleView?id=sf.connected_app_rotate_consumer_details.htm&type=5) from the connected app that was configured in Salesforce above
* private_key_file - Path to the Private Key file generated above (server.key)
* sf_user_name - The pre-authorised salesforce user that will be used for API access
* temp_dir - Directory for creating temporary files during execution
* input_file_encoding - Specifies the encoding of the source files that will be uploaded via the IngestAPI (Default: utf-8)


### Upsert data via Streaming Ingest API
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

### Upsert data via Bulk Ingest API
Example: `sample_bulk_upsert.py`

```python
def bulk_upsert(self, source_api_name: str, source_object_name: str, data_file_paths: Iterable)
```
Upsert one or more files of data via Bulk Ingest API

* source_api_name (str): Name of the Ingest API data connector
* source_object_name (str): Name of the resource type to send to Data Cloud
* data_file_paths (iter): Iterable that emits a list of file paths for upload

Returns the response object from the API call

### Delete data via Bulk Ingest API
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
Example: `sample_sql_query.py`

```python
def query(self, query_str: str) -> pd.DataFrame:
```
Returns the result of the specified query

* query_str (str) - The query to execute

Returns a Dataframe containing query output

### List jobs
```python
def list_jobs(self, limit: int=50, offset=0, orderby: str="", state: str="") -> requests.Response:
```
Retrieves all jobs in Data Cloud

* limit (int) - The number of records to return. Defaults to 20. Maximum up to 100 records per request.
* offset (int) - Number of rows to skip before returning.
* orderBy (str) - The field used to order job definition results. The default order is by systemModstamp.
* states (str)	Get jobs in specific states. Valid states are Open, UploadComplete, Failed, Aborted, and JobComplete. The parameter’s value can be a comma-delimited list.

Returns the response object from the API call

### Get status information for a job
```python
def job_info(self, job_id: str) -> requests.Response:
```

Retrieves detailed information about the specified job.

* job_id (int) - The job id returned in the response body from the Create Job request.

Returns the response object from the API call

### Terminate a job
```python
def abort_job(self, job_id: str) -> requests.Response:
```

Attempts to abort the specified job

* job_id (int) - The job id returned in the response body from the Create Job request.

Returns the response object from the API call

### Terminate all jobs
```python
def abort_all_jobs(self) -> None:
```
Attempts to abort all Open and UploadComplete jobs in the Data Cloud instance

## Manage bulk jobs via the CLI
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

We recommend that you configure the following as environment variables or write to a .env file in the installation directory:

* SF_LOGIN_URL - Salesforce login URL - defaults to: "login.salesforce.com" if not specified.
* CLIENT_ID - [The Consumer Key](https://help.salesforce.com/s/articleView?id=sf.connected_app_rotate_consumer_details.htm&type=5) from the connected app that was configured in Salesforce above
* PRIVATE_KEY_FILE - Path to the Private Key file generated above (server.key)
* USER_NAME - The pre-authorised salesforce user that will be used for API access
* TEMP_DIR - Directory for creating temporary files during execution
* INPUT_FILE_ENCODING - Specifies the encoding of the source files that will be uploaded via the IngestAPI (Default: utf-8)

If required these can be passed as arguments to the SalesforceDataCloud object constructor to override the environment variables.
