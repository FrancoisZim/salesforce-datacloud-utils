"""Sample script to illustrate how to delete data from Salesforce Data Cloud using the bulk ingest API

Reads in a file containing a list of primary keys for rows to delete from the target.

"""
from salesforce_datacloud_utils import SalesforceDataCloud

sfdc=SalesforceDataCloud()
sfdc.bulk_delete("Event_API", "runner_profiles", ["sample_bulk_delete.csv"])

