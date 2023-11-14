"""Salesforce Data Cloud Utils

Utility functions for the Data Cloud API

Configure the following in the environment or a .env file before use
clientId=XXX
privateKeyFile=server.key
userName=XXX@tabemeadatacloud.demo
tempDir=tempfiles
inputFileEncoding=utf-8
"""

import requests
import json
import pandas as pd 
import csv
import time
import argparse
import logging
import jwt  # Make sure you have PyJWT installed
from typing import Dict, Optional, Any, Union, List, Iterable, Generator
from filesplit.split import Split

from exceptions import SalesforceDataCloudError

from dotenv import load_dotenv
import os
load_dotenv()

"""
Constants for Data Cloud Limits and Guidelines

See: https://help.salesforce.com/s/articleView?id=sf.c360_a_limits_and_guidelines.htm&type=5
"""
BULK_API_MAX_PAYLOAD_SIZE=150 * 1000 * 1000
STREAMING_API_MAX_PAYLOAD_SIZE=200 * 1000

# Initialize logging
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s %(funcName)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("debug.log"), consoleHandler],
)
logger = logging.getLogger("datacloud_utils")


class SalesforceDataCloud:
    """
    Salesforce Data Cloud Instance

    Handles authentication and basic operations to the Data Cloud REST API.

    """
    def __init__(self):
        self.context = {
            "loginUrl": "login.salesforce.com",
            "version": "52.0",
            "clientId": os.getenv('clientId'),
            "privateKeyFile": os.getenv('privateKeyFile'),
            "userName": os.getenv('userName'),
            "tempDir": os.getenv('tempDir'),
            "inputFileEncoding": os.getenv("inputFileEncoding"),
            "dne_cdpTokenRefreshTime": 0,
        }
        # Read the private key from a file
        with open(self.context["privateKeyFile"], 'r') as private_key_file:
            self.context["privateKey"] = private_key_file.read()

    def _authenticate(self, force_refresh: bool=False) -> None:
        """
        Login to data cloud instance and store access token etc. for api calls

        force_refresh (bool): If set then gets a new token even if the current one is still valid
        """
        logger.info("Token refresh time: " + str(self.context["dne_cdpTokenRefreshTime"]))
        cdpTokenAge = round((time.time() * 1000 - self.context["dne_cdpTokenRefreshTime"]) / 60000)
        logger.info("cdpTokenAge: " + str(cdpTokenAge))

        if cdpTokenAge < 115 and not force_refresh:
            logger.info("Existing cdp token valid")
        else:
            logger.info("Refreshing token...")
            self.context["dne_cdpTokenRefreshTime"] = int(time.time() * 1000)

            # Define JWT header
            header = {
                "alg": "RS256",
                "typ": "JWT"
            }
            # Define JWT payload
            payload = {
                "iss": self.context.get("clientId"),
                "sub": self.context.get("userName"),
                "aud": self.context.get("loginUrl"),
                "exp": int(time.time())
            }

            # Create and sign JWT
            jwt_token = jwt.encode(payload, self.context["privateKey"], algorithm='RS256')
            #jwt_token = jwt.encode(header, payload, self.context["privateKey"])
            logger.debug("JWT Assertion:"+jwt_token)
            self.context['dne_cdpAssertion'] = jwt_token

            logger.info("Get S2S Access Token...")
            # S2S Access Token Payload
            s2s_payload = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token
            }

            # S2S Access Token Request
            s2s_url = 'https://' + self.context["loginUrl"] + '/services/oauth2/token'
            s2s_headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            s2s_response = requests.post(s2s_url, data=s2s_payload, headers=s2s_headers)
            s2s_response_json = s2s_response.json()
            logger.debug(f"S2S Access Token Request Returned: {s2s_response.status_code}:{s2s_response.text}")
            logger.debug(json.dumps(s2s_response_json, indent = 2))
            if s2s_response.status_code != 200:
                raise SalesforceDataCloudError("Get S2S Access Token", s2s_url,
                    s2s_response.status_code,
                    s2s_response.text)

            self.context['dne_cdpAuthToken'] = s2s_response_json['access_token']
            self.context['dne_cdpInstanceUrl'] = s2s_response_json['instance_url']

            # Start the exchange flow
            logger.info("Data Cloud Token Exchange Request...")
            
            # CDP Token Exchange Payload
            cdp_payload = {
                "grant_type": "urn:salesforce:grant-type:external:cdp",
                "subject_token": self.context['dne_cdpAuthToken'],
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token"
            }
            
            # CDP Token Exchange Request
            cdp_url = self.context['dne_cdpInstanceUrl'] + '/services/a360/token'
            cdp_headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            cdp_response = requests.post(cdp_url, data=cdp_payload, headers=cdp_headers)
            cdp_response_json = cdp_response.json()
            logger.debug(f"Data Cloud Token Request Returned: {cdp_response.status_code}:{cdp_response.text}")
            logger.debug(json.dumps(cdp_response_json, indent = 2))
            if cdp_response.status_code != 200:
                raise SalesforceDataCloudError("Data Cloud Token Exchange", cdp_url,
                    cdp_response.status_code,
                    cdp_response.text)
            
            self.context['dne_cdpOffcoreToken'] = cdp_response_json['access_token']
            self.context['dne_cdpOffcoreUrl'] = cdp_response_json['instance_url']


    def _split_json_list(self, input_json_list, max_size):
        result_lists = []
        current_list = []
        current_size = 0

        for item in input_json_list:
            item_json_str = json.dumps(item)
            item_size = len(item_json_str.encode('utf-8'))

            # Check if adding the current item exceeds the maximum size
            if current_size + item_size > max_size:
                result_lists.append(current_list)
                current_list = []
                current_size = 0

            current_list.append(item)
            current_size += item_size

        if current_list:
            result_lists.append(current_list)

        return result_lists

    def streaming_upsert(self, source_api_name: str, source_object_name: str, data: object, test_mode: bool=False):
        """
        Upsert one or more rows of data via Streaming Ingest API

        source_api_name (str): Name of the Ingest API data connector
        source_object_name (str): Name of the resource type to send to Data Cloud
        data (str): Array of dicts with one dict per row
        test_mode (bool): Validate payload only (default: false)

        Returns the response object from the API call
        """
        self._authenticate()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+self.context['dne_cdpOffcoreToken']
        }
        response = None
        for chunk in self._split_json_list(data["data"], STREAMING_API_MAX_PAYLOAD_SIZE):
            payload = json.dumps({"data": chunk})
            logger.debug(payload)
            url='https://' + self.context['dne_cdpOffcoreUrl'] + f'/api/v1/ingest/sources/{source_api_name}/{source_object_name}'
            if test_mode: 
                logger.info("Test mode selected, records will not be committed")
                url+="/actions/test"

            response = requests.request("POST", url, headers=headers, data=payload)
            logger.info(f"Streaming UPSERT request returned: {response.status_code} : {response.text}")

            if response.status_code != 202:
                raise SalesforceDataCloudError("Streaming UPSERT", url,
                    response.status_code,
                    response.text)
            
        return response
    
    def _create_job(self, source_api_name: str, source_object_name: str, operation: str="upsert") -> str:
        """
        Open a new batch job

        source_api_name (str): Name of the Ingest API data connector
        source_object_name (str): Name of the resource type to send to Data Cloud

        return: job_id (str)
        """
        logger.info("Creating new job")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+self.context['dne_cdpOffcoreToken']
        }
        url='https://' + self.context['dne_cdpOffcoreUrl'] + '/api/v1/ingest/jobs'
        payload = json.dumps({
            "object": source_object_name,
            "sourceName": source_api_name,
            "operation": operation
        })
        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info(f"Create job returned: {response.status_code}: {response.text}")
        if response.status_code != 201:
            raise SalesforceDataCloudError("Create Job", url,
                response.status_code,
                response.text)
        response_dict = response.json()
        job_id=response_dict["id"]
        logger.info(f"Using job id:{job_id}")
        return job_id
    
    def _close_job(self, job_id: str, state: str="UploadComplete"):
        """
        Closes the specified job

        job_id (int) - The job id returned in the response body from the Create Job request.
        state (str) - Optional: Close with specified state (UploadComplete or Abort - Default=UploadComplete)

        Returns the response object from the API call
        """
        self._authenticate()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+self.context['dne_cdpOffcoreToken']
        }
        payload = json.dumps({
            "state": state
        })
        url='https://' + self.context['dne_cdpOffcoreUrl'] + f'/api/v1/ingest/jobs/{job_id}'
        response = requests.request("PATCH", url, headers=headers, data=payload)
        logger.info(response.text)
        return response
    
    def _bulk_operation(self, source_api_name: str, source_object_name: str, data_file_paths: Iterable, operation: str="upsert"):
        """
        Upsert one or more files of data via Bulk Ingest API

        source_api_name (str): Name of the Ingest API data connector
        source_object_name (str): Name of the resource type to send to Data Cloud
        data_file_paths (iter): Iterable that emits a list of file paths for upload

        Returns the response object from the API call
        """
        self._authenticate()
        job_id=None
        response=None
        job_id=self._create_job(source_api_name, source_object_name, operation)

        def split_callback(split_file_path: str, split_file_size: int):
                    logger.info(f"Uploading file part: {split_file_path} (size:{split_file_size})")
                    with open(split_file_path, 'r', encoding="utf8") as payload_file:
                        payload = payload_file.read()
                        response = requests.request("PUT", url, headers=headers, data=payload.encode('utf-8'))

                        if response.status_code != 202:
                            raise SalesforceDataCloudError("Upload File", url,
                                response.status_code,
                                response.text)
                        
                        logger.info(f"File upload complete: {split_file_path}, removing temp file")
                    os.remove(split_file_path)
        
        try: 
            #Upload files
            headers = {
                'Content-Type': 'text/csv',
                'Authorization': 'Bearer '+self.context['dne_cdpOffcoreToken']
            }
            url='https://' + self.context['dne_cdpOffcoreUrl'] + f'/api/v1/ingest/jobs/{job_id}/batches'

            for file_path in data_file_paths:
                logger.info(f"Processing file {file_path}")
                split = Split(file_path, self.context["tempDir"])
                if self.context["inputFileEncoding"]:
                    split.bysize(size=BULK_API_MAX_PAYLOAD_SIZE, newline=True, includeheader=True, callback=split_callback, encoding=self.context["inputFileEncoding"], split_file_encoding="utf-8")
                else:    
                    split.bysize(size=BULK_API_MAX_PAYLOAD_SIZE, newline=True, includeheader=True, callback=split_callback)

            response=self._close_job(job_id)
            job_id=None
        finally:
            if not job_id is None:
                self.abort_job(job_id)
        
        return response
    
    def bulk_upsert(self, source_api_name: str, source_object_name: str, data_file_paths: Iterable):
        """
        Upsert one or more files of data via Bulk Ingest API

        source_api_name (str): Name of the Ingest API data connector
        source_object_name (str): Name of the resource type to send to Data Cloud
        data_file_paths (iter): Iterable that emits a list of file paths for upload

        Returns the response object from the API call
        """

        self._bulk_operation(source_api_name=source_api_name, source_object_name=source_object_name, data_file_paths=data_file_paths, operation="upsert")

    def bulk_delete(self, source_api_name: str, source_object_name: str, data_file_paths: Iterable):
        """
        Delete rows via Bulk Ingest API

        source_api_name (str): Name of the Ingest API data connector
        source_object_name (str): Name of the resource type to send to Data Cloud
        data_file_paths (iter): Iterable that emits a list of file paths for upload

        Returns the response object from the API call
        """

        self._bulk_operation(source_api_name=source_api_name, source_object_name=source_object_name, data_file_paths=data_file_paths, operation="delete")

    def list_jobs(self, limit: int=50, offset=0, orderby: str="", state: str=""):
        """
        Retrieves all jobs in Data Cloud

        limit (int) - The number of records to return. Defaults to 20. Maximum up to 100 records per request.
        offset (int) - Number of rows to skip before returning.
        orderBy (str) - The field used to order job definition results. The default order is by systemModstamp.
        states (str)	Get jobs in specific states. Valid states are Open, UploadComplete, Failed, Aborted, and JobComplete. The parameter’s value can be a comma-delimited list.

        Returns the response object from the API call
        """
        self._authenticate()
        logger.info("Get list of jobs...")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+self.context['dne_cdpOffcoreToken']
        }
        payload = {}
        url='https://' + self.context['dne_cdpOffcoreUrl'] + f'/api/v1/ingest/jobs?limit={limit}&offset={offset}&orderby={orderby}&states={state}'
        response = requests.request("GET", url, headers=headers, data=payload)
        logger.info(json.dumps(response.json(), indent = 2))
        return response

    def job_info(self, job_id: str):
        """
        Retrieves detailed information about the specified job.

        job_id (int) - The job id returned in the response body from the Create Job request.

        Returns the response object from the API call
        """
        self._authenticate()
        logger.info(f"Get information for job:{job_id}")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+self.context['dne_cdpOffcoreToken']
        }
        payload = {}
        url='https://' + self.context['dne_cdpOffcoreUrl'] + f'/api/v1/ingest/jobs/{job_id}'
        response = requests.request("GET", url, headers=headers, data=payload)
        logger.info(json.dumps(response.json(), indent = 2))
        return response
    
    def abort_job(self, job_id: str):
        """
        Attempts to abort the specified job

        job_id (int) - The job id returned in the response body from the Create Job request.
        
        Returns the response object from the API call
        """
        return self._close_job(job_id, "Aborted")
    
    def abort_all_jobs(self):
        """
        Attempts to abort all Open and UploadComplete jobs in Data Cloud
        """
        self._authenticate()
        response=self.list_jobs(state="Open,UploadComplete")
        jobs=response.json()["data"]
        for job in jobs:
            logger.info(f'Abort job:{job["id"]}')
            self.abort_job(job["id"])
    
    def query(self, query_str: str) -> pd.DataFrame:
        """
        Returns the result of the specified query

        query_str (str) - The query to execute
        
        Returns dataframe, json or text

        Response	Dataframe containing uery output
        """
        self._authenticate()
        logger.info(f'Execute Query: "{query_str}""...')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+self.context['dne_cdpOffcoreToken']
        }
        url='https://' + self.context['dne_cdpOffcoreUrl'] + '/api/v2/query'
        payload = json.dumps({
            "sql": query_str
        })
        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info(f"Query returned: {response.status_code}")
        if response.status_code != 200:
            raise SalesforceDataCloudError("Query", url,
                response.status_code,
                response.text)
        response_dict = response.json()
        output_metadata=response_dict["metadata"]
        df = pd.DataFrame(response_dict["data"], columns =output_metadata.keys())
        while not response_dict["done"]:
            nextBatchId=response_dict["nextBatchId"]
            logger.info(f'Fetch next batch of results: nextBatchId:"{nextBatchId}""...')
            url='https://' + self.context['dne_cdpOffcoreUrl'] + f'/api/v2/query/{nextBatchId}'
            response = requests.request("GET", url, headers=headers)
            logger.info(f"Fetch next batch returned: {response.status_code}")
            if response.status_code != 200:
                raise SalesforceDataCloudError("Query", url,
                    response.status_code,
                    response.text)
            response_dict = response.json()
            df2 = pd.DataFrame(response_dict["data"], columns =output_metadata.keys())
            df.append(df2, ignore_index=True)
        
        logger.info(f'Query returned {len(df)} rows"...')
        return df


def main():
    # Define Command Line Args
    parser = argparse.ArgumentParser(
        prog="python3 salesforce_datacloud_utils.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
Utility functions for the Data Cloud API

Command Line Functions:
- list_active_jobs: (default action) Show jobs with status "Open,UploadComplete,InProgress"
- list_all_jobs: Show all jobs
- job_info: Show detailed information for the specified job
- abort_job: Terminate the specified job with state "Aborted"
        """,
    )
    parser.add_argument(
        "--command",
        default="list_active_jobs",
        choices=["list_active_jobs","list_all_jobs","job_info","abort_job"],
        help="Select the operation to execute",
    )
    parser.add_argument(
        "--job_id",
        help="The job id returned in the response body from the Create Job request.",
    )
    sfdc=SalesforceDataCloud()

    args = parser.parse_args()
    selected_command = args.command
    job_id=vars(args).get("job_id")
    if selected_command=="list_active_jobs":
        logger.info("Get list of active jobs...")
        sfdc.list_jobs(state="Open,UploadComplete,InProgress")
    elif selected_command=="list_all_jobs":
        logger.info("Get list of all jobs...")
        sfdc.list_jobs()
    elif selected_command=="job_info":
        if bool(job_id):
            sfdc.job_info(job_id)
        else:
            logger.error('Must specify job_id when command is "job_info"')
    elif selected_command=="abort_job":
        if bool(job_id):
            sfdc.abort_job(job_id)
        else:
            logger.error('Must specify job_id when command is "abort_job"')
    else:
        logger.error(f"Invalid command:{command}")
    
                
if __name__ == "__main__":
    main()
