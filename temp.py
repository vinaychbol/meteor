import boto3

client = boto3.client('s3', region_name='us-east-1')

buckets = client.list_buckets(Prefix='gravty-ui-')

buckets = buckets['Buckets']

bucket_list = []
for bucket in buckets:
    bucket_name = bucket['Name']
    if 'gravty-ui-' in bucket_name:
        bucket_list.append(bucket_name.split('-')[-1])
    
    
print(bucket_list)



