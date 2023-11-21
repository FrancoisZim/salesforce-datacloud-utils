"""Sample script to illustrate how to upsert data to Salesforce Data Cloud using the bulk ingest API

Reads in a file containing a list of rows to upsert to the target.

"""
from salesforce_datacloud_utils import SalesforceDataCloud

sfdc=SalesforceDataCloud()
sfdc.bulk_upsert("Event_API", "runner_profiles", ["sample_bulk_upsert.csv"])

