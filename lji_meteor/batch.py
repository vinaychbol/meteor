import os
import boto3
import json
from rich import print_json

def list_aws_batch_jobs():
    client = boto3.client('batch', region_name='ap-south-1')
    response = client.describe_jobs(
    jobs=[
        '3a4e2c23-dcd7-4412-baf6-9148f3f38d1a',
        '4a550bae-60b9-4bef-82f6-c4af99969807'
      ]
    )
    return response
# Example usage
if __name__ == "__main__":
    aws_jobs = list_aws_batch_jobs()
    print_json(data=aws_jobs)