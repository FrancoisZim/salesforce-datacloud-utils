from salesforce_datacloud_utils import SalesforceDataCloud

sfdc=SalesforceDataCloud()
sfdc.bulk_delete("Event_API", "runner_profiles", ["bulk_delete.csv"])

