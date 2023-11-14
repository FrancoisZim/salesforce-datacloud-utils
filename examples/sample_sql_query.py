import pandas as pd
from salesforce_datacloud_utils import SalesforceDataCloud

sql_query_str="""
    SELECT	
                SUM(ssot__SalesOrder__dlm.ssot__TotalAmount__c) as TotalSpend
                , ssot__Individual__dlm.ssot__Id__c as CustomerId
    FROM		ssot__SalesOrder__dlm
    INNER JOIN	ssot__Individual__dlm ON 1=1
        AND		ssot__SalesOrder__dlm.ssot__SoldToCustomerId__c = ssot__Individual__dlm.ssot__Id__c
    GROUP BY 	ssot__Individual__dlm.ssot__Id__c
    ORDER BY    1
"""


sfdc=SalesforceDataCloud()
df=sfdc.query(query_str=sql_query_str)
print(df)

