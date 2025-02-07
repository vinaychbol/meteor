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
cache_file_path = os.path.expanduser("~/.meteor/comet-details.json")

def update_cache(profile):
    with console.status("Please wait - Loading Configurations...", spinner="pong"):
        try:
            credentials = profile
            session = boto3.Session(profile_name=credentials)
            client = session.client('s3', region_name='us-west-2')
            response = client.get_object(Bucket='gravty-comet', Key='comet-details.json')
            data = json.loads(response['Body'].read())
            
            # Ensure the directory exists before writing the cache file
            os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
            
            # Save the fetched data to the cache file
            with open(cache_file_path, 'w') as cache_file:
                return json.dump(data, cache_file)
            
        except Exception as e:
            console.print(f"\n[bold red]Error at :[/bold red] {str(e)}")
            return
    

def env_and_creds_layer(func):
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        
        if kwargs['profile'] is None:
            aws_config_file_path = os.path.expanduser("~/.aws/credentials")
            # Initialize ConfigParser and read the config file
            aws_config_file = configparser.ConfigParser()
            aws_config_file.read(aws_config_file_path)
            # Get a list of all profile names
            profiles_list = aws_config_file.sections()
            kwargs['profile'] = profiles_list[survey.routines.select('Select Profile : ', options = tuple(profiles_list))]
        
        # Check if the cache file exists
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r') as cache_file:
                data = json.load(cache_file)
        else:
            data = update_cache(kwargs['profile'])            
            
        #take input of env if it's not mentioned
        if kwargs['env'] is None:
            envs = list(data.keys())
            kwargs['env'] = envs[survey.routines.select('Select Environment : ', options = tuple(envs))]
            
        kwargs['data'] = json.dumps(data[kwargs['env'].strip().lower()])
        func(*args, **kwargs)
    
    return wrapper