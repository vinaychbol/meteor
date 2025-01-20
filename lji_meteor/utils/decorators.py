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
            
        #fetching data from S3
        with console.status("Please wait - Loading Congurations...", spinner="pong"):
            try:
                credentials = kwargs['profile'].strip()
                session = boto3.Session(profile_name=credentials)
                client = session.client('s3', region_name='us-west-2')
                response = client.get_object(Bucket='gravty-comet', Key='comet-details.json')
                data = json.loads(response['Body'].read())
                # print(json.dumps(data, indent=2))
                
            except Exception as e:
                console.print(f"\n[bold red]Error at :[/bold red] {str(e)}")
                return
        
        #take input of env if it's not mentioned
        if kwargs['env'] is None:
            envs = list(data.keys())
            kwargs['env'] = envs[survey.routines.select('Select Environment : ', options = tuple(envs))]
            
        kwargs['data'] = json.dumps(data[kwargs['env'].strip().lower()])
        
            
        func(*args, **kwargs)
    
    return wrapper