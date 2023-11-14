'''Uses boto3 to find matching filenames in s3 and bulk upsert to datacloud

Requires the following additional python libraries:
  pip install boto3
'''

from salesforce_datacloud_utils import SalesforceDataCloud
import sys, os, fnmatch, boto3, botocore

#S3 Configuration
aws_profile_name="saml"
bucket_name="dc4t-1"
name_format="BulkAPITests/*.csv"

#Data Cloud Configuration
source_api_name="Event_API"
source_object_name="runner_profiles"

def get_csvs_from_s3(bucket_name, name_format, aws_profile_name):
    #Generator function - yields a list of csv files

    print(f"Downloading files from bucket{bucket_name} matching {name_format}")

    # Starts boto3 session based on profile name.
    # Will typically look for credential files /Users/[you]/.aws/credentials for linux
    session = boto3.Session(profile_name=aws_profile_name)
    s3 = session.client('s3')

    # Creates list of all objects in a given bucket.
    try:
        filenames = s3.list_objects(Bucket=bucket_name)['Contents']
    except botocore.exceptions.ClientError as e:
        sys.exit(e)

    # Downloads matching pattern and header file.
    for file_object in s3.list_objects(Bucket=bucket_name)['Contents']:
        if fnmatch.fnmatch(file_object['Key'], name_format):
            file_name=file_object['Key']
            print(f"Downloading {file_name} from S3...")
            s3.download_file(bucket_name, file_name, file_name)
            yield file_name
            print(f"Delete {file_name}...")
            os.remove(file_name)

def main():
    sfdc=SalesforceDataCloud()
    sfdc.bulk_upsert(source_api_name=source_api_name, source_object_name=source_object_name, 
        data_file_paths=get_csvs_from_s3(bucket_name, name_format, aws_profile_name))

if __name__ == '__main__':
    main()
