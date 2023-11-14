from salesforce_datacloud_utils import SalesforceDataCloud

sfdc=SalesforceDataCloud()
data_json={
    "data": [
        {
        "maid": 123,
        "first_name": "Sandeep",
        "last_name": "Aulakh",
        "email": "saulakh@salesforce-nto.com",
        "gender": "Male",
        "city": "Wilton",
        "state": "CT",
        "created": "2021-10-22T09:11:11.816319Z"
        },
        {
        "maid": 124,
        "first_name": "Aaron",
        "last_name": "Cates",
        "email": "acates@salesforce-nto.com",
        "gender": "Male",
        "city": "San Francisco",
        "state": "CA",
        "created": "2021-10-22T09:11:11.816319Z"
        }
    ]
}

sfdc.streaming_upsert("External_Data", "runner_profiles", data_json)