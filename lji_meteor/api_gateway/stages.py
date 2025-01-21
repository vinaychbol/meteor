import boto3
import botocore
from rich import print

class Stage:
    
    def __init__(self, profile, env, region):
        self.profile = profile
        self.region = region
        session = boto3.Session(profile_name=profile)
        self.client = session.client('apigateway', region_name=self.region)
    
    def turn_off_logging(self):
        """
        Turn off logging for the API Gateway for specific environment.
        """
        paginator = self.client.get_paginator('get_rest_apis')
        for response in paginator.paginate():
            # print(response)
            for api in response['items']:
                api_name = api['name']
                api_id = str(api['id'])
                print(f"[blue]Disabling logging for API: {api_name} [/blue]")
                stages = self.client.get_stages(restApiId=api_id)
                for item in stages['item']:
                    stageName = item['stageName']
                    try:
                        response = self.client.update_stage(
                            restApiId=api_id,
                            stageName=stageName,
                            patchOperations=[
                                {
                                    'op': 'replace',
                                    'path': '/*/*/logging/dataTrace',
                                    'value': 'false'
                                },
                                {
                                    'op': 'replace',
                                    'path': '/*/*/logging/loglevel',
                                    'value': 'OFF'
                                }
                            ]
                        )
                        print(f"[green]Logging disabled successfully for {api_name} on stage {stageName}[/green]")
                    except botocore.exceptions.ClientError as error:
                        print(f"[red]An error occurred while disabling logging for {api_name} on stage {stageName} - {error}[/red]")
        