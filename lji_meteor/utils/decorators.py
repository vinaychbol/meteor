import os
import functools
import survey
import configparser

import json
import boto3
import typer
import survey
from rich import print
from rich.console import Console

console = Console()

def fetch_data_from_s3(profile):
    with console.status("Please wait - Loading Configurations...", spinner="pong"):
        try:
            credentials = profile
            session = boto3.Session(profile_name=credentials)
            client = session.client('s3', region_name='us-west-2')
            response = client.get_object(Bucket='gravty-comet', Key='comet-detailsnew.json')
            data = json.loads(response['Body'].read())
            return data
        except Exception as e:
            console.print(f"\n[bold red]Error at :[/bold red] {str(e)}")
            return None
    
def fetch_envs(profile):
    try:
        session = boto3.Session(profile_name=profile)
        client = session.client('s3')
        buckets = client.list_buckets(Prefix='gravty-ui-')
        buckets = buckets['Buckets']
        bucket_list = []
        for bucket in buckets:
            bucket_name = bucket['Name']
            if 'gravty-ui-' in bucket_name:
                bucket_list.append(bucket_name.split('-')[-1])
    except Exception as e:
        return None
    return bucket_list

def env_and_creds_layer(func):
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        
        if kwargs['profile'] is None:
            aws_config_file_path = os.path.expanduser("~/.aws/credentials")
            aws_config_file = configparser.ConfigParser()
            aws_config_file.read(aws_config_file_path)
            profiles_list = aws_config_file.sections()
            kwargs['profile'] = profiles_list[survey.routines.select('Select Profile : ', options = tuple(profiles_list))]
        
        data = fetch_data_from_s3(kwargs['profile'])
        if data is None:
            return

        if kwargs['env'] is None:
            envs = fetch_envs(kwargs['profile'])
            if envs is None:
                console.print("\n[bold red]Error:[/bold red] Unable to fetch environments. Please check your AWS credentials and permissions. Falling back to manual selection.")
                envs = list(data.keys())
            kwargs['env'] = envs[survey.routines.select('Select Environment : ', options = tuple(envs))]
            print(f"\n[bold yellow]Selected Environment :[/bold yellow] {kwargs['env']}")
            
        kwargs['data'] = json.dumps(data[kwargs['env'].strip().lower()])
        func(*args, **kwargs)
    
    return wrapper
