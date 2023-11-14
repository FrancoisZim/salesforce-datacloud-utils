"""All exceptions for Salesforce Datacloud Utils"""

class SalesforceDataCloudError(Exception):
    def __init__(self, operation, url, status, content):
        self.operation = operation
        self.url = url
        self.status = status
        self.content = content
        super().__init__(f"Salesforce Data Cloud Error during operation '{operation}' on URL '{url}' with status code {status}: {content}")



