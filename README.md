# salesforce-datacloud-utils
Simple utility functions for calling the Salesforce Data Cloud APIs, specifically the Ingest API and Query APIv2.

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
* [Set Up Ingestion API Connector](https://help.salesforce.com/s/articleView?id=sf.c360_a_connect_an_ingestion_source.htm&type=5)
* [Create an Ingestion API Data Stream](https://help.salesforce.com/s/articleView?id=sf.c360_a_create_ingestion_data_stream.htm&type=5)

### Install Required Python Libraries

TODO

### Configure Environment Variables

Configure the following as environment variables or write to a .env file in the installation directory:

* client - [The Consumer Key](https://help.salesforce.com/s/articleView?id=sf.connected_app_rotate_consumer_details.htm&type=5) from the connected app that was configured in Salesforce above
* privateKeyFile - Path to the Private Key file generated above (server.key)
* userName - The pre-authorised salesforce user that will be used for API access
* tempDir - Directory for creating temporary files during execution
* inputFileEncoding - Optional: Specifies the encoding of the source files that will be uploaded via the IngestAPI (e.g. utf-8)


